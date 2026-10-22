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
from app.services.reflexion import ReflexionTimeout, ReflexionTrace, execute_with_reflexion

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


def _iteration_history(trace: ReflexionTrace):
    return [
        ReflexionIteration(
            attempt_number=attempt.attempt_number,
            generated_sql=attempt.generated_sql,
            error_message=attempt.error_message,
            status=attempt.status,
        )
        for attempt in trace.attempts
    ]


async def _run_guarded_reflexion(
    request: ReflexionChatRequest,
    filtered_schema: str,
    permissions,
    *,
    timeout_seconds: float,
    on_step=None,
) -> ReflexionTrace:
    """Run the shared Reflexion loop for every SQL endpoint."""

    async def plan(feedback: str | None) -> str:
        agent_plan = await asyncio.to_thread(
            llm_service.generate_sql_plan,
            request.query,
            filtered_schema,
            feedback,
        )
        try:
            generated_sql = agent_plan["tool_call"]["arguments"]["query"]
        except (KeyError, TypeError) as exc:
            raise ValueError("LLM returned no executable SQL") from exc
        if not isinstance(generated_sql, str):
            raise ValueError("LLM returned a non-string SQL query")
        return generated_sql

    async def validate(sql: str) -> tuple[bool, str]:
        return await asyncio.to_thread(
            sql_validator.validate_sql_ast,
            sql,
            permissions,
        )

    async def execute(sql: str):
        try:
            return await mcp_client.execute_sql_with_timeout(sql, timeout_seconds)
        except (MCPQueryTimeoutError, asyncio.TimeoutError) as exc:
            elapsed = exc.elapsed_seconds if isinstance(exc, MCPQueryTimeoutError) else 0.0
            raise ReflexionTimeout(str(exc), elapsed) from exc
        except Exception as exc:
            raise RuntimeError(_database_error_message(exc)) from exc

    async def reflect(sql: str, error: str) -> str | None:
        return await asyncio.to_thread(
            llm_service.reflect_failed_sql,
            request.query,
            sql,
            error,
        )

    return await execute_with_reflexion(
        request.query,
        plan=plan,
        validate=validate,
        execute=execute,
        reflect=reflect,
        max_iterations=request.max_iterations,
        on_step=on_step,
    )


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

    trace = await _run_guarded_reflexion(
        request,
        filtered_schema,
        permissions,
        timeout_seconds=10.0,
    )
    return ReflexionChatResponse(
        query=request.query,
        role=request.role,
        status=trace.status,
        total_iterations_used=len(trace.attempts),
        iteration_history=_iteration_history(trace),
        final_data=trace.data if trace.status == "success" else None,
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

    trace = await _run_guarded_reflexion(
        request,
        filtered_schema,
        permissions,
        timeout_seconds=request.timeout_seconds,
    )
    history = _iteration_history(trace)
    if trace.status != "success":
        return SecurePipelineResponse(
            status=trace.status,
            total_iterations_used=len(history),
            execution_time_seconds=trace.execution_time_seconds,
            iteration_history=history,
            raw_data=None,
            final_answer="",
        )

    try:
        serialized_data = json.dumps(trace.data, ensure_ascii=False, default=str)
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
        total_iterations_used=len(history),
        execution_time_seconds=trace.execution_time_seconds,
        iteration_history=history,
        raw_data=trace.data,
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

            queue: asyncio.Queue = asyncio.Queue()

            async def on_step(message: str, attempt_number: int) -> None:
                await queue.put(
                    {
                        "type": "step",
                        "message": message,
                        "attempt_number": attempt_number,
                    }
                )
                await asyncio.sleep(0)

            async def runner() -> None:
                try:
                    trace = await _run_guarded_reflexion(
                        request,
                        filtered_schema,
                        permissions,
                        timeout_seconds=request.timeout_seconds,
                        on_step=on_step,
                    )
                    history = _iteration_history(trace)
                    if trace.status != "success":
                        payload = SecurePipelineResponse(
                            status=trace.status,
                            total_iterations_used=len(history),
                            execution_time_seconds=trace.execution_time_seconds,
                            iteration_history=history,
                            raw_data=None,
                            final_answer="",
                        ).model_dump()
                        await queue.put({"type": "final_result", "data": payload})
                        return

                    await queue.put(
                        {
                            "type": "step",
                            "message": "🧼 Đang áp dụng Taint Filter và tổng hợp câu trả lời...",
                        }
                    )
                    serialized_data = json.dumps(
                        trace.data, ensure_ascii=False, default=str
                    )
                    try:
                        final_answer = await asyncio.to_thread(
                            llm_service.synthesize_final_answer,
                            request.query,
                            serialized_data,
                        )
                    except (RuntimeError, ValueError):
                        logger.exception("Result synthesis failed")
                        await queue.put(
                            {
                                "type": "error",
                                "message": "Result synthesis service is unavailable",
                            }
                        )
                        return
                    payload = SecurePipelineResponse(
                        status="success",
                        total_iterations_used=len(history),
                        execution_time_seconds=trace.execution_time_seconds,
                        iteration_history=history,
                        raw_data=trace.data,
                        final_answer=final_answer,
                    ).model_dump()
                    await queue.put({"type": "final_result", "data": payload})
                except Exception as exc:
                    logger.exception("Streaming secure pipeline failed")
                    await queue.put({"type": "error", "message": str(exc)})
                finally:
                    await queue.put(None)

            task = asyncio.create_task(runner())
            try:
                while True:
                    event = await queue.get()
                    if event is None:
                        break
                    yield json.dumps(event, ensure_ascii=False, default=str) + "\n"
                    await asyncio.sleep(0.1)
            finally:
                await task
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
