import asyncio
import json
import logging
import traceback

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import StreamingResponse
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.schemas.chat import (
    ChatRequest,
    ChatResponse,
    ReflexionChatRequest,
    ReflexionChatResponse,
    ReflexionIteration,
    SecurePipelineRequest,
    SecurePipelineResponse,
)
from app.services import (
    llm_service,
    mcp_client,
    rbac_service,
    schema_filter,
    sql_validator,
)
from app.services.mcp_client import MCPQueryTimeoutError

router = APIRouter(prefix="/agent", tags=["agent"])
logger = logging.getLogger(__name__)


async def _stream_event(event: dict[str, object]):
    """Yield one JSON Lines event and give the server a chance to flush it."""
    yield json.dumps(event, ensure_ascii=False, default=str) + "\n"
    await asyncio.sleep(0.1)


def _database_error_message(error: BaseException) -> str:
    """Extract the most useful Trino error from nested ExceptionGroups."""
    nested_errors = getattr(error, "exceptions", None)
    if nested_errors:
        messages = [
            _database_error_message(nested_error)
            for nested_error in nested_errors
        ]
        messages = [message for message in messages if message]
        prioritized = [
            message
            for message in messages
            if "TrinoUserError" in message or "COLUMN_NOT_FOUND" in message
        ]
        return " | ".join(prioritized or messages)

    formatted = "".join(traceback.format_exception(error)).strip()
    if "TrinoUserError" in formatted or "COLUMN_NOT_FOUND" in formatted:
        return formatted
    return str(error) or formatted


@router.post(
    "/query",
    response_model=ChatResponse,
    status_code=status.HTTP_200_OK,
)
async def process_agent_query(
    request: ChatRequest, db_session: Session = Depends(get_db)
) -> ChatResponse:
    """Receive an NLQ request and inject RBAC-filtered metadata context."""
    try:
        permissions = await asyncio.to_thread(
            rbac_service.get_role_permissions, db_session, request.role
        )
    except HTTPException:
        raise
    except SQLAlchemyError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="RBAC policy service is unavailable",
        ) from exc

    try:
        raw_schema = await mcp_client.fetch_trino_schema(
            permissions["allowed_catalogs"]
        )
        filtered_schema = schema_filter.filter_schema_by_rbac(
            raw_schema, permissions
        )
    except (OSError, RuntimeError, ValueError) as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Metadata discovery service is unavailable",
        ) from exc

    try:
        agent_plan = await asyncio.to_thread(
            llm_service.generate_sql_plan,
            request.query,
            filtered_schema,
        )
    except (RuntimeError, ValueError) as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Neural SQL planning service returned an invalid response",
        ) from exc

    try:
        sql = agent_plan["tool_call"]["arguments"]["query"]
    except (KeyError, TypeError):
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Neural SQL planning service returned no executable SQL",
        ) from None
    if not isinstance(sql, str):
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Neural SQL planning service returned invalid SQL",
        )

    is_valid, reason = await asyncio.to_thread(
        sql_validator.validate_sql_ast,
        sql,
        permissions,
    )
    return ChatResponse(
        query=request.query,
        role_name=permissions["role_name"],
        filtered_schema=filtered_schema,
        agent_plan=agent_plan,
        status="passed" if is_valid else "blocked",
        reason=reason,
        sql=sql,
    )


@router.post(
    "/query_reflexion",
    response_model=ReflexionChatResponse,
    status_code=status.HTTP_200_OK,
)
async def process_agent_query_reflexion(
    request: ReflexionChatRequest,
    db_session: Session = Depends(get_db),
) -> ReflexionChatResponse:
    """Iteratively repair an LLM SQL plan using AST and Trino feedback."""
    try:
        permissions = await asyncio.to_thread(
            rbac_service.get_role_permissions, db_session, request.role
        )
    except HTTPException:
        raise
    except SQLAlchemyError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="RBAC policy service is unavailable",
        ) from exc

    try:
        raw_schema = await mcp_client.fetch_trino_schema(
            permissions["allowed_catalogs"]
        )
        filtered_schema = schema_filter.filter_schema_by_rbac(
            raw_schema, permissions
        )
    except (OSError, RuntimeError, ValueError) as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Metadata discovery service is unavailable",
        ) from exc

    iteration_history: list[ReflexionIteration] = []
    error_feedback: str | None = None
    final_data = None
    final_status = "failed_after_max_iterations"

    for attempt_number in range(1, request.max_iterations + 1):
        logger.info(
            "[Reflexion] Attempt %s/%s started",
            attempt_number,
            request.max_iterations,
        )
        generated_sql = ""

        try:
            agent_plan = await asyncio.to_thread(
                llm_service.generate_sql_plan,
                request.query,
                filtered_schema,
                error_feedback,
            )
            generated_sql = agent_plan["tool_call"]["arguments"]["query"]
            if not isinstance(generated_sql, str):
                raise ValueError("LLM returned a non-string SQL query")
        except (KeyError, TypeError, RuntimeError, ValueError) as exc:
            error_feedback = f"LLM planning error: {exc}"
            iteration_history.append(
                ReflexionIteration(
                    attempt_number=attempt_number,
                    generated_sql=generated_sql,
                    error_message=error_feedback,
                    status="error_llm",
                )
            )
            logger.warning(
                "[Reflexion] Attempt %s/%s failed at LLM: %s",
                attempt_number,
                request.max_iterations,
                exc,
            )
            continue

        is_valid, ast_reason = await asyncio.to_thread(
            sql_validator.validate_sql_ast,
            generated_sql,
            permissions,
        )
        if not is_valid:
            error_feedback = ast_reason
            iteration_history.append(
                ReflexionIteration(
                    attempt_number=attempt_number,
                    generated_sql=generated_sql,
                    error_message=ast_reason,
                    status="error_ast",
                )
            )
            logger.warning(
                "[Reflexion] Attempt %s/%s failed at AST: %s",
                attempt_number,
                request.max_iterations,
                ast_reason,
            )
            continue

        try:
            final_data = await mcp_client.execute_trino_query(
                generated_sql, timeout_seconds=10.0
            )
        except (OSError, RuntimeError, ValueError) as exc:
            error_feedback = f"Trino engine error: {exc}"
            iteration_history.append(
                ReflexionIteration(
                    attempt_number=attempt_number,
                    generated_sql=generated_sql,
                    error_message=error_feedback,
                    status="error_engine",
                )
            )
            logger.warning(
                "[Reflexion] Attempt %s/%s failed at Trino: %s",
                attempt_number,
                request.max_iterations,
                exc,
            )
            continue

        iteration_history.append(
            ReflexionIteration(
                attempt_number=attempt_number,
                generated_sql=generated_sql,
                error_message="",
                status="success",
            )
        )
        final_status = "success"
        logger.info(
            "[Reflexion] Attempt %s/%s succeeded",
            attempt_number,
            request.max_iterations,
        )
        break

    return ReflexionChatResponse(
        query=request.query,
        role=request.role,
        status=final_status,
        total_iterations_used=len(iteration_history),
        iteration_history=iteration_history,
        final_data=final_data,
    )


@router.post(
    "/query_secure_pipeline",
    response_model=SecurePipelineResponse,
    status_code=status.HTTP_200_OK,
)
async def process_secure_pipeline(
    request: SecurePipelineRequest,
    db_session: Session = Depends(get_db),
) -> SecurePipelineResponse:
    """Run RBAC, metadata, Reflexion, execution, and taint-safe synthesis."""
    try:
        permissions = await asyncio.to_thread(
            rbac_service.get_role_permissions, db_session, request.role
        )
    except HTTPException:
        raise
    except SQLAlchemyError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="RBAC policy service is unavailable",
        ) from exc

    try:
        raw_schema = await mcp_client.fetch_trino_schema(
            permissions["allowed_catalogs"]
        )
        filtered_schema = schema_filter.filter_schema_by_rbac(
            raw_schema, permissions
        )
    except (OSError, RuntimeError, ValueError) as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Metadata discovery service is unavailable",
        ) from exc

    iteration_history: list[ReflexionIteration] = []
    error_feedback: str | None = None
    raw_data = None
    execution_time_seconds = 0.0

    for attempt_number in range(1, request.max_iterations + 1):
        logger.info(
            "[SecurePipeline] Attempt %s/%s started",
            attempt_number,
            request.max_iterations,
        )
        generated_sql = ""
        try:
            agent_plan = await asyncio.to_thread(
                llm_service.generate_sql_plan,
                request.query,
                filtered_schema,
                error_feedback,
            )
            generated_sql = agent_plan["tool_call"]["arguments"]["query"]
            if not isinstance(generated_sql, str):
                raise ValueError("LLM returned a non-string SQL query")
        except (KeyError, TypeError, RuntimeError, ValueError) as exc:
            error_feedback = f"LLM planning error: {exc}"
            iteration_history.append(
                ReflexionIteration(
                    attempt_number=attempt_number,
                    generated_sql=generated_sql,
                    error_message=error_feedback,
                    status="error_llm",
                )
            )
            logger.warning(
                "[SecurePipeline] Attempt %s/%s failed at LLM: %s",
                attempt_number,
                request.max_iterations,
                exc,
            )
            continue

        is_valid, ast_reason = await asyncio.to_thread(
            sql_validator.validate_sql_ast,
            generated_sql,
            permissions,
        )
        if not is_valid:
            error_feedback = ast_reason
            iteration_history.append(
                ReflexionIteration(
                    attempt_number=attempt_number,
                    generated_sql=generated_sql,
                    error_message=ast_reason,
                    status="error_ast",
                )
            )
            logger.warning(
                "[SecurePipeline] Attempt %s/%s failed at AST: %s",
                attempt_number,
                request.max_iterations,
                ast_reason,
            )
            continue

        try:
            raw_data, execution_time_seconds = (
                await mcp_client.execute_sql_with_timeout(
                    generated_sql, request.timeout_seconds
                )
            )
        except (MCPQueryTimeoutError, asyncio.TimeoutError) as exc:
            message = str(exc)
            if isinstance(exc, MCPQueryTimeoutError):
                execution_time_seconds = exc.elapsed_seconds
            iteration_history.append(
                ReflexionIteration(
                    attempt_number=attempt_number,
                    generated_sql=generated_sql,
                    error_message=message,
                    status="circuit_breaker_timeout",
                )
            )
            logger.warning(
                "[SecurePipeline] Attempt %s/%s stopped by circuit breaker: %s",
                attempt_number,
                request.max_iterations,
                exc,
            )
            return SecurePipelineResponse(
                status="circuit_breaker_timeout",
                total_iterations_used=len(iteration_history),
                execution_time_seconds=execution_time_seconds,
                iteration_history=iteration_history,
                raw_data=None,
                final_answer="",
            )
        except Exception as exc:
            error_msg = _database_error_message(exc)
            error_feedback = (
                "Lỗi thực thi từ Database: "
                f"{error_msg}. Hãy kiểm tra lại TÊN CỘT và CÚ PHÁP."
            )
            iteration_history.append(
                ReflexionIteration(
                    attempt_number=attempt_number,
                    generated_sql=generated_sql,
                    error_message=error_feedback,
                    status="error_engine",
                )
            )
            logger.warning(
                "[SecurePipeline] Attempt %s/%s failed at Trino: %s",
                attempt_number,
                request.max_iterations,
                exc,
            )
            continue

        iteration_history.append(
            ReflexionIteration(
                attempt_number=attempt_number,
                generated_sql=generated_sql,
                error_message="",
                status="success",
            )
        )
        logger.info(
            "[SecurePipeline] Attempt %s/%s succeeded",
            attempt_number,
            request.max_iterations,
        )
        break
    else:
        return SecurePipelineResponse(
            status="failed_after_max_iterations",
            total_iterations_used=len(iteration_history),
            execution_time_seconds=execution_time_seconds,
            iteration_history=iteration_history,
            raw_data=None,
            final_answer="",
        )

    try:
        serialized_data = json.dumps(raw_data, ensure_ascii=False, default=str)
        final_answer = await asyncio.to_thread(
            llm_service.synthesize_final_answer,
            request.query,
            serialized_data,
        )
    except (RuntimeError, ValueError) as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Result synthesis service is unavailable",
        ) from exc

    return SecurePipelineResponse(
        status="success",
        total_iterations_used=len(iteration_history),
        execution_time_seconds=execution_time_seconds,
        iteration_history=iteration_history,
        raw_data=raw_data,
        final_answer=final_answer,
    )


@router.post(
    "/query_stream",
    status_code=status.HTTP_200_OK,
)
async def process_agent_query_stream(
    request: SecurePipelineRequest,
    db_session: Session = Depends(get_db),
) -> StreamingResponse:
    """Stream observable secure-pipeline progress as newline-delimited JSON."""

    async def event_stream():
        async def emit(message: str, **extra: object):
            event = {"type": "step", "message": message, **extra}
            yield json.dumps(event, ensure_ascii=False, default=str) + "\n"
            await asyncio.sleep(0.1)

        try:
            async for item in emit("🔐 Đang xác thực role và tải chính sách RBAC..."):
                yield item
            try:
                permissions = await asyncio.to_thread(
                    rbac_service.get_role_permissions, db_session, request.role
                )
            except HTTPException:
                raise
            except SQLAlchemyError as exc:
                raise RuntimeError("RBAC policy service is unavailable") from exc

            async for item in emit("🧭 Đang khám phá metadata và lọc schema theo RBAC..."):
                yield item
            try:
                raw_schema = await mcp_client.fetch_trino_schema(
                    permissions["allowed_catalogs"]
                )
                filtered_schema = schema_filter.filter_schema_by_rbac(
                    raw_schema, permissions
                )
            except (OSError, RuntimeError, ValueError) as exc:
                raise RuntimeError("Metadata discovery service is unavailable") from exc

            iteration_history: list[ReflexionIteration] = []
            error_feedback: str | None = None
            raw_data = None
            execution_time_seconds = 0.0

            for attempt_number in range(1, request.max_iterations + 1):
                async for item in emit(
                    "🧠 Đang gọi LLM để sinh kế hoạch SQL "
                    f"(Reflexion lần {attempt_number}/{request.max_iterations})...",
                    attempt_number=attempt_number,
                ):
                    yield item
                generated_sql = ""
                try:
                    agent_plan = await asyncio.to_thread(
                        llm_service.generate_sql_plan,
                        request.query,
                        filtered_schema,
                        error_feedback,
                    )
                    generated_sql = agent_plan["tool_call"]["arguments"]["query"]
                    if not isinstance(generated_sql, str):
                        raise ValueError("LLM returned a non-string SQL query")
                except (KeyError, TypeError, RuntimeError, ValueError) as exc:
                    error_feedback = f"LLM planning error: {exc}"
                    message = f"LLM không tạo được SQL: {error_feedback}"
                    iteration_history.append(
                        ReflexionIteration(
                            attempt_number=attempt_number,
                            generated_sql=generated_sql,
                            error_message=error_feedback,
                            status="error_llm",
                        )
                    )
                    logger.warning("[StreamPipeline] %s", message)
                    async for item in emit(
                        f"⚠️ {message}. Đang thử lại...",
                        attempt_number=attempt_number,
                    ):
                        yield item
                    continue

                async for item in emit(
                    "🛡️ Đang kiểm tra an toàn AST Parser...",
                    attempt_number=attempt_number,
                ):
                    yield item
                is_valid, ast_reason = await asyncio.to_thread(
                    sql_validator.validate_sql_ast,
                    generated_sql,
                    permissions,
                )
                if not is_valid:
                    error_feedback = ast_reason
                    iteration_history.append(
                        ReflexionIteration(
                            attempt_number=attempt_number,
                            generated_sql=generated_sql,
                            error_message=ast_reason,
                            status="error_ast",
                        )
                    )
                    logger.warning(
                        "[StreamPipeline] Attempt %s blocked by AST: %s",
                        attempt_number,
                        ast_reason,
                    )
                    async for item in emit(
                        f"🚫 AST đã chặn truy vấn: {ast_reason}. "
                        f"Đang tự phản ngẫm (lần {attempt_number})...",
                        attempt_number=attempt_number,
                    ):
                        yield item
                    continue

                async for item in emit(
                    "🔌 Đang gọi Trino MCP "
                    "(execute_query_read_only)...",
                    attempt_number=attempt_number,
                ):
                    yield item
                try:
                    raw_data, execution_time_seconds = (
                        await mcp_client.execute_sql_with_timeout(
                            generated_sql, request.timeout_seconds
                        )
                    )
                except (MCPQueryTimeoutError, asyncio.TimeoutError) as exc:
                    message = str(exc)
                    if isinstance(exc, MCPQueryTimeoutError):
                        execution_time_seconds = exc.elapsed_seconds
                    iteration_history.append(
                        ReflexionIteration(
                            attempt_number=attempt_number,
                            generated_sql=generated_sql,
                            error_message=message,
                            status="circuit_breaker_timeout",
                        )
                    )
                    async for item in emit(
                        f"⏱️ Circuit Breaker dừng truy vấn: {message}",
                        attempt_number=attempt_number,
                    ):
                        yield item
                    payload = SecurePipelineResponse(
                        status="circuit_breaker_timeout",
                        total_iterations_used=len(iteration_history),
                        execution_time_seconds=execution_time_seconds,
                        iteration_history=iteration_history,
                        raw_data=None,
                        final_answer="",
                    ).model_dump()
                    yield json.dumps(
                        {"type": "final_result", "data": payload},
                        ensure_ascii=False,
                        default=str,
                    ) + "\n"
                    return
                except Exception as exc:
                    error_msg = _database_error_message(exc)
                    error_feedback = (
                        "Lỗi thực thi từ Database: "
                        f"{error_msg}. Hãy kiểm tra lại TÊN CỘT và CÚ PHÁP."
                    )
                    iteration_history.append(
                        ReflexionIteration(
                            attempt_number=attempt_number,
                            generated_sql=generated_sql,
                            error_message=error_feedback,
                            status="error_engine",
                        )
                    )
                    logger.warning(
                        "[StreamPipeline] Attempt %s failed at Trino: %s",
                        attempt_number,
                        error_msg,
                    )
                    async for item in emit(
                        f"🔄 Trino báo lỗi, đang tự phản ngẫm "
                        f"(Reflexion lần {attempt_number}): {error_msg}",
                        attempt_number=attempt_number,
                    ):
                        yield item
                    continue

                iteration_history.append(
                    ReflexionIteration(
                        attempt_number=attempt_number,
                        generated_sql=generated_sql,
                        error_message="",
                        status="success",
                    )
                )
                async for item in emit("✅ Trino thực thi thành công.", attempt_number=attempt_number):
                    yield item
                break
            else:
                payload = SecurePipelineResponse(
                    status="failed_after_max_iterations",
                    total_iterations_used=len(iteration_history),
                    execution_time_seconds=execution_time_seconds,
                    iteration_history=iteration_history,
                    raw_data=None,
                    final_answer="",
                ).model_dump()
                yield json.dumps(
                    {"type": "final_result", "data": payload},
                    ensure_ascii=False,
                    default=str,
                ) + "\n"
                return

            async for item in emit("🧼 Đang áp dụng Taint Filter và tổng hợp câu trả lời..."):
                yield item
            serialized_data = json.dumps(raw_data, ensure_ascii=False, default=str)
            final_answer = await asyncio.to_thread(
                llm_service.synthesize_final_answer,
                request.query,
                serialized_data,
            )
            payload = SecurePipelineResponse(
                status="success",
                total_iterations_used=len(iteration_history),
                execution_time_seconds=execution_time_seconds,
                iteration_history=iteration_history,
                raw_data=raw_data,
                final_answer=final_answer,
            ).model_dump()
            yield json.dumps(
                {"type": "final_result", "data": payload},
                ensure_ascii=False,
                default=str,
            ) + "\n"
        except HTTPException as exc:
            yield json.dumps(
                {"type": "error", "message": str(exc.detail)},
                ensure_ascii=False,
            ) + "\n"
        except (RuntimeError, ValueError, OSError) as exc:
            logger.exception("Streaming secure pipeline failed")
            yield json.dumps(
                {"type": "error", "message": str(exc)},
                ensure_ascii=False,
            ) + "\n"

    return StreamingResponse(
        event_stream(),
        media_type="application/x-ndjson",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
        },
    )
