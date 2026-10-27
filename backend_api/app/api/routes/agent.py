import asyncio
import json
import logging
import traceback

from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.responses import StreamingResponse
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.core.config import settings
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
from app.services.llm_service import (
    LLMNonRetryableError,
    LLMTimeoutError,
    is_non_retryable_llm_error,
)
from app.services.mcp_client import MCPQueryTimeoutError

router = APIRouter(prefix="/agent", tags=["agent"])
logger = logging.getLogger(__name__)


def _llm_timeout_budget() -> float:
    """Outer asyncio budget: per-model timeout times unique model count."""
    per_call = max(1.0, float(settings.llm_timeout_seconds))
    unique_models = len({m for m in settings.available_models if m}) or 1
    return per_call * unique_models


async def _generate_sql_plan_async(
    user_query: str,
    filtered_schema: str,
    error_feedback: str | None = None,
) -> dict:
    """Call Gemini planning with an asyncio-level timeout guard."""
    return await asyncio.wait_for(
        asyncio.to_thread(
            llm_service.generate_sql_plan,
            user_query,
            filtered_schema,
            error_feedback,
        ),
        timeout=_llm_timeout_budget(),
    )


async def _synthesize_final_answer_async(user_query: str, serialized_data: str) -> str:
    return await asyncio.wait_for(
        asyncio.to_thread(
            llm_service.synthesize_final_answer,
            user_query,
            serialized_data,
        ),
        timeout=_llm_timeout_budget(),
    )


def _is_fatal_llm_failure(exc: BaseException) -> bool:
    return isinstance(
        exc,
        (LLMNonRetryableError, LLMTimeoutError, asyncio.TimeoutError),
    ) or is_non_retryable_llm_error(exc)


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


def _preview_rows(data: object, limit: int = 10) -> object:
    if isinstance(data, list):
        return data[:limit]
    if isinstance(data, tuple):
        return list(data[:limit])
    return data


def _filtered_table_names(filtered_schema: str) -> list[str]:
    return [
        line.split(" (", 1)[0].split(". ", 1)[-1]
        for line in filtered_schema.splitlines()
        if ". " in line and " (" in line
    ]


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
        agent_plan = await _generate_sql_plan_async(request.query, filtered_schema)
    except (LLMNonRetryableError, LLMTimeoutError, asyncio.TimeoutError) as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Neural SQL planning service unavailable: {exc}",
        ) from exc
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
            agent_plan = await _generate_sql_plan_async(
                request.query,
                filtered_schema,
                error_feedback,
            )
            generated_sql = agent_plan["tool_call"]["arguments"]["query"]
            if not isinstance(generated_sql, str):
                raise ValueError("LLM returned a non-string SQL query")
        except (KeyError, TypeError, RuntimeError, ValueError, asyncio.TimeoutError) as exc:
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
            if _is_fatal_llm_failure(exc):
                raise HTTPException(
                    status_code=status.HTTP_502_BAD_GATEWAY,
                    detail=f"Neural SQL planning service unavailable: {exc}",
                ) from exc
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
            agent_plan = await _generate_sql_plan_async(
                request.query,
                filtered_schema,
                error_feedback,
            )
            generated_sql = agent_plan["tool_call"]["arguments"]["query"]
            if not isinstance(generated_sql, str):
                raise ValueError("LLM returned a non-string SQL query")
        except (KeyError, TypeError, RuntimeError, ValueError, asyncio.TimeoutError) as exc:
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
            if _is_fatal_llm_failure(exc):
                raise HTTPException(
                    status_code=status.HTTP_502_BAD_GATEWAY,
                    detail=f"Neural SQL planning service unavailable: {exc}",
                ) from exc
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
        final_answer = await _synthesize_final_answer_async(
            request.query,
            serialized_data,
        )
    except (LLMNonRetryableError, LLMTimeoutError, asyncio.TimeoutError) as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Result synthesis service unavailable: {exc}",
        ) from exc
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
    http_request: Request,
    db_session: Session = Depends(get_db),
) -> StreamingResponse:
    """Stream observable secure-pipeline progress as newline-delimited JSON."""

    async def event_stream():
        async def emit(
            message: str,
            xray_data: dict | None = None,
            **extra: object,
        ):
            event = {"type": "step", "message": message, **extra}
            if xray_data is not None:
                event["xray_data"] = xray_data
            yield json.dumps(event, ensure_ascii=False, default=str) + "\n"
            await asyncio.sleep(0.1)

        async def ensure_client_connected() -> bool:
            if await http_request.is_disconnected():
                logger.info("[StreamPipeline] Client disconnected; aborting pipeline")
                return False
            return True

        async def emit_error(message: str):
            yield json.dumps(
                {"type": "error", "message": message},
                ensure_ascii=False,
            ) + "\n"

        try:
            if not await ensure_client_connected():
                return

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
            async for item in emit(
                "✅ Đã tải chính sách RBAC.",
                xray_data={
                    "step": "RBAC Authorization",
                    "target": "MySQL Database",
                    "execution_detail": (
                        "SELECT allowed_catalogs, allowed_tables, denied_tables, "
                        "can_export_file, max_row_limit FROM agent_role_permissions "
                        f"WHERE role_name = '{request.role}'"
                    ),
                    "input": {"role": request.role},
                    "output": {"permissions": permissions},
                },
            ):
                yield item

            if not await ensure_client_connected():
                return

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
            async for item in emit(
                "✅ Đã lọc schema theo RBAC.",
                xray_data={
                    "step": "Metadata Discovery",
                    "target": "Trino Catalog & RBAC Filter",
                    "execution_detail": (
                        "Lấy schema từ Trino cho các catalogs: "
                        f"{permissions['allowed_catalogs']} và lọc giữ lại các bảng được phép."
                    ),
                    "input": {"allowed_catalogs": permissions["allowed_catalogs"]},
                    "output": {"filtered_schema": _filtered_table_names(filtered_schema)},
                },
            ):
                yield item

            iteration_history: list[ReflexionIteration] = []
            error_feedback: str | None = None
            raw_data = None
            execution_time_seconds = 0.0

            for attempt_number in range(1, request.max_iterations + 1):
                if not await ensure_client_connected():
                    return

                if attempt_number == 1:
                    llm_status = "🧠 Đang gọi LLM để sinh kế hoạch SQL..."
                else:
                    llm_status = (
                        "🧠 Đang gọi LLM để Reflexion kế hoạch SQL "
                        f"(lần {attempt_number}/{request.max_iterations})..."
                    )
                async for item in emit(
                    llm_status,
                    attempt_number=attempt_number,
                ):
                    yield item
                generated_sql = ""
                planning_feedback = error_feedback
                try:
                    agent_plan = await _generate_sql_plan_async(
                        request.query,
                        filtered_schema,
                        error_feedback,
                    )
                    generated_sql = agent_plan["tool_call"]["arguments"]["query"]
                    if not isinstance(generated_sql, str):
                        raise ValueError("LLM returned a non-string SQL query")
                except (
                    KeyError,
                    TypeError,
                    RuntimeError,
                    ValueError,
                    asyncio.TimeoutError,
                ) as exc:
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
                        f"❌ LLM planning thất bại ở attempt {attempt_number}.",
                        xray_data={
                            "step": "LLM Planning / Reflexion",
                            "attempt_number": attempt_number,
                            "target": f"Gemini LLM (Model: {settings.available_models[0]})",
                            "execution_detail": llm_service.build_sql_plan_prompt(
                                request.query, filtered_schema, planning_feedback
                            ),
                            "input": {
                                "query": request.query,
                                "error_feedback": planning_feedback,
                            },
                            "error": error_feedback,
                        },
                    ):
                        yield item
                    if _is_fatal_llm_failure(exc):
                        async for item in emit(
                            f"⛔ {message}. Dừng pipeline (lỗi LLM không thể retry).",
                            attempt_number=attempt_number,
                        ):
                            yield item
                        async for item in emit_error(
                            f"Không kết nối được LLM: {exc}"
                        ):
                            yield item
                        return
                    async for item in emit(
                        f"⚠️ {message}. Đang thử lại...",
                        attempt_number=attempt_number,
                    ):
                        yield item
                    continue

                async for item in emit(
                    f"✅ LLM hoàn tất attempt {attempt_number}.",
                    xray_data={
                        "step": "LLM Planning / Reflexion",
                        "attempt_number": attempt_number,
                        "target": f"Gemini LLM (Model: {settings.available_models[0]})",
                        "execution_detail": llm_service.build_sql_plan_prompt(
                            request.query, filtered_schema, planning_feedback
                        ),
                        "input": {
                            "query": request.query,
                            "error_feedback": planning_feedback,
                        },
                        "output": agent_plan,
                    },
                ):
                    yield item

                if not await ensure_client_connected():
                    return

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
                        "Đang Reflexion để thử lại...",
                        attempt_number=attempt_number,
                    ):
                        yield item
                    async for item in emit(
                        f"❌ AST blocked attempt {attempt_number}.",
                        xray_data={
                            "step": "AST Validation",
                            "attempt_number": attempt_number,
                            "target": "sqlglot AST Validator",
                            "execution_detail": (
                                "Sử dụng thư viện sqlglot (dialect: trino) để phân tích "
                                "Abstract Syntax Tree (AST) của câu lệnh SQL sinh ra. "
                                "Đối chiếu các Node (Table, Column, Command Type) với "
                                "ma trận quyền (allowed_tables) để chặn DDL/DML và "
                                "kiểm soát truy cập."
                            ),
                            "input": generated_sql,
                            "error": f"Blocked: {ast_reason}",
                        },
                    ):
                        yield item
                    continue

                async for item in emit(
                    f"✅ AST passed attempt {attempt_number}.",
                    xray_data={
                        "step": "AST Validation",
                        "attempt_number": attempt_number,
                        "target": "sqlglot AST Validator",
                        "execution_detail": (
                            "Sử dụng thư viện sqlglot (dialect: trino) để phân tích "
                            "Abstract Syntax Tree (AST) và đối chiếu với allowed_tables."
                        ),
                        "input": generated_sql,
                        "output": "Passed",
                    },
                ):
                    yield item

                if not await ensure_client_connected():
                    return

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
                    async for item in emit(
                        f"❌ Trino timeout ở attempt {attempt_number}.",
                        xray_data={
                            "step": "Trino Execution",
                            "attempt_number": attempt_number,
                            "target": "Trino Federated Engine (via MCP Proxy)",
                            "execution_detail": (
                                "Gọi tool 'execute_query_read_only' với tham số query: "
                                f"{generated_sql}"
                            ),
                            "input": generated_sql,
                            "error": message,
                        },
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
                        f"🔄 Trino báo lỗi, đang Reflexion để thử lại: "
                        f"{error_msg}",
                        attempt_number=attempt_number,
                    ):
                        yield item
                    async for item in emit(
                        f"❌ Trino execution failed ở attempt {attempt_number}.",
                        xray_data={
                            "step": "Trino Execution",
                            "attempt_number": attempt_number,
                            "target": "Trino Federated Engine (via MCP Proxy)",
                            "execution_detail": (
                                "Gọi tool 'execute_query_read_only' với tham số query: "
                                f"{generated_sql}"
                            ),
                            "input": generated_sql,
                            "error": error_msg,
                        },
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
                async for item in emit(
                    "✅ Trino thực thi thành công.",
                    attempt_number=attempt_number,
                    xray_data={
                        "step": "Trino Execution",
                        "attempt_number": attempt_number,
                        "target": "Trino Federated Engine (via MCP Proxy)",
                        "execution_detail": (
                            "Gọi tool 'execute_query_read_only' với tham số query: "
                            f"{generated_sql}"
                        ),
                        "input": generated_sql,
                        "output": _preview_rows(raw_data),
                    },
                ):
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

            if not await ensure_client_connected():
                return

            async for item in emit(
                "🧼 Đang áp dụng Taint Filter và tổng hợp câu trả lời..."
            ):
                yield item
            serialized_data = json.dumps(raw_data, ensure_ascii=False, default=str)
            try:
                final_answer = await _synthesize_final_answer_async(
                    request.query,
                    serialized_data,
                )
            except (
                LLMNonRetryableError,
                LLMTimeoutError,
                asyncio.TimeoutError,
                RuntimeError,
                ValueError,
            ) as exc:
                async for item in emit(
                    "❌ Synthesis thất bại.",
                    xray_data={
                        "step": "Taint Filter & Synthesis",
                        "target": "Gemini LLM (Synthesis)",
                        "execution_detail": llm_service.build_synthesis_prompt(
                            request.query, serialized_data
                        ),
                        "input": {
                            "query": request.query,
                            "raw_data": _preview_rows(raw_data),
                        },
                        "error": str(exc),
                    },
                ):
                    yield item
                async for item in emit_error(
                    f"Không tổng hợp được câu trả lời từ LLM: {exc}"
                ):
                    yield item
                return
            async for item in emit(
                "✅ Đã tổng hợp câu trả lời an toàn.",
                xray_data={
                    "step": "Taint Filter & Synthesis",
                    "target": "Gemini LLM (Synthesis)",
                    "execution_detail": llm_service.build_synthesis_prompt(
                        request.query, serialized_data
                    ),
                    "input": {
                        "query": request.query,
                        "raw_data": _preview_rows(raw_data),
                    },
                    "output": final_answer,
                },
            ):
                yield item
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
