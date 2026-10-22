"""Retry technical SQL failures and stop on security denials or timeouts."""

import json
import logging
import re
from collections.abc import Awaitable, Callable
from dataclasses import dataclass
from typing import Any, Literal

logger = logging.getLogger(__name__)

FailureDecision = Literal["retry", "abort", "timeout"]

_TIMEOUT_MARKERS = (
    "timed out",
    "QueryTimeout",
    "exceeded timeout",
)

_AST_RETRY_MARKERS = (
    "SQL parse error",
    "JOIN requires an ON or USING condition",
)

_ENGINE_ABORT_MARKERS = (
    "does not appear to be read-only",
    "Write queries are disabled",
    "role is not allowed",
    "is not permitted",
    "role is required",
    "LỖI GUARDRAIL",
    "concurrent query slot",
)

_ENGINE_RETRY_MARKERS = (
    "COLUMN_NOT_FOUND",
    "TABLE_NOT_FOUND",
    "SCHEMA_NOT_FOUND",
    "CATALOG_NOT_FOUND",
    "SYNTAX_ERROR",
    "mismatched input",
    "cannot be resolved",
    "could not be parsed",
    "must be fully qualified",
)

_REFLECTION_PROMPT = """\
You fix one failed Trino SQL statement. The gateway or parser rejected it for a technical reason.
Keep the user's question. Do not change tables in order to reach data the gateway refused.
Return only this JSON object:
{
  "query": "one SELECT statement without a trailing semicolon"
}

User question:
{question}

Failed SQL:
{sql}

Error:
{error}
"""


class ReflexionTimeout(Exception):
    """Raised when execution hits the circuit breaker."""

    def __init__(self, message: str, elapsed_seconds: float = 0.0) -> None:
        super().__init__(message)
        self.elapsed_seconds = elapsed_seconds


@dataclass
class ReflexionAttempt:
    attempt_number: int
    generated_sql: str
    error_message: str
    status: str


@dataclass
class ReflexionTrace:
    status: str
    attempts: list[ReflexionAttempt]
    data: Any = None
    execution_time_seconds: float = 0.0


def classify_failure(stage: str, message: str) -> FailureDecision:
    """Decide whether a failure may be repaired. Unknown failures abort."""
    text = message or ""
    if stage == "timeout" or any(marker in text for marker in _TIMEOUT_MARKERS):
        return "timeout"
    if stage == "ast":
        if any(marker in text for marker in _AST_RETRY_MARKERS):
            return "retry"
        return "abort"
    if any(marker in text for marker in _ENGINE_ABORT_MARKERS):
        return "abort"
    if any(marker in text for marker in _ENGINE_RETRY_MARKERS):
        return "retry"
    return "abort"


def reflection_prompt(user_query: str, failed_sql: str, error: str) -> str:
    """Ask the model to replace one SQL statement and nothing else."""
    return (
        _REFLECTION_PROMPT.replace("{question}", user_query)
        .replace("{sql}", failed_sql)
        .replace("{error}", error)
    )


def parse_reflected_sql(raw: str) -> str | None:
    """Read the query field. Extra keys are ignored."""
    text = (raw or "").strip()
    if text.startswith("```"):
        text = re.sub(r"^```(?:json)?\s*", "", text, flags=re.IGNORECASE)
        text = re.sub(r"\s*```$", "", text)
    try:
        payload = json.loads(text)
    except json.JSONDecodeError:
        return None
    if not isinstance(payload, dict):
        return None
    query = payload.get("query")
    if not isinstance(query, str):
        return None
    cleaned = query.strip().rstrip(";").strip()
    return cleaned or None


async def _notify(
    on_step: Callable[[str, int], Awaitable[None]] | None,
    message: str,
    attempt_number: int,
) -> None:
    if on_step is not None:
        await on_step(message, attempt_number)


async def _revised_sql(
    reflect: Callable[[str, str], Awaitable[str | None]],
    sql: str,
    error: str,
) -> str | None:
    try:
        revised = await reflect(sql, error)
    except Exception:
        logger.exception("SQL reflector failed")
        return None
    if not isinstance(revised, str) or not revised.strip():
        return None
    return revised.strip()


async def execute_with_reflexion(
    user_query: str,
    *,
    plan: Callable[[str | None], Awaitable[str]],
    validate: Callable[[str], Awaitable[tuple[bool, str]]],
    execute: Callable[[str], Awaitable[tuple[Any, float]]],
    reflect: Callable[[str, str], Awaitable[str | None]],
    max_iterations: int,
    on_step: Callable[[str, int], Awaitable[None]] | None = None,
) -> ReflexionTrace:
    """Plan once, then rewrite SQL only after a technical failure."""
    attempts: list[ReflexionAttempt] = []
    sql: str | None = None
    plan_feedback: str | None = None
    elapsed_seconds = 0.0

    for attempt_number in range(1, max_iterations + 1):
        logger.info(
            "[Reflexion] Attempt %s/%s started query=%r",
            attempt_number,
            max_iterations,
            user_query,
        )
        if sql is None:
            await _notify(
                on_step,
                "🧠 Đang gọi LLM để sinh kế hoạch SQL "
                f"(Reflexion lần {attempt_number}/{max_iterations})...",
                attempt_number,
            )
            try:
                planned = await plan(plan_feedback)
                sql = planned.strip() if isinstance(planned, str) else ""
            except Exception as exc:
                message = f"LLM planning error: {exc}"
                attempts.append(
                    ReflexionAttempt(attempt_number, "", message, "error_llm")
                )
                logger.warning("[Reflexion] Attempt %s failed at LLM: %s", attempt_number, exc)
                if attempt_number == max_iterations:
                    return ReflexionTrace("failed_after_max_iterations", attempts)
                plan_feedback = message
                await _notify(
                    on_step,
                    f"⚠️ LLM không tạo được SQL: {message}. Đang thử lại...",
                    attempt_number,
                )
                continue

        await _notify(on_step, "🛡️ Đang kiểm tra an toàn AST Parser...", attempt_number)
        is_valid, reason = await validate(sql)
        if not is_valid:
            decision = classify_failure("ast", reason)
            attempts.append(ReflexionAttempt(attempt_number, sql, reason, "error_ast"))
            logger.warning("[Reflexion] Attempt %s failed at AST: %s", attempt_number, reason)
            if decision != "retry" or attempt_number == max_iterations:
                stop_message = (
                    f"🚫 Hết số lần tự sửa sau lỗi AST: {reason}"
                    if decision == "retry"
                    else f"🚫 AST đã chặn truy vấn và dừng Reflexion: {reason}"
                )
                await _notify(on_step, stop_message, attempt_number)
                status = "failed_after_max_iterations" if decision == "retry" else "aborted"
                return ReflexionTrace(status, attempts, None, elapsed_seconds)
            revised = await _revised_sql(reflect, sql, reason)
            if revised is None:
                await _notify(
                    on_step,
                    "🛑 LLM không trả về SQL sửa hợp lệ. Dừng Reflexion.",
                    attempt_number,
                )
                return ReflexionTrace("aborted", attempts, None, elapsed_seconds)
            await _notify(
                on_step,
                f"🚫 AST đã chặn truy vấn: {reason}. Đang tự phản ngẫm (lần {attempt_number})...",
                attempt_number,
            )
            sql = revised
            continue

        await _notify(
            on_step,
            "🔌 Đang gọi Trino MCP (execute_query_read_only)...",
            attempt_number,
        )
        try:
            data, elapsed_seconds = await execute(sql)
        except ReflexionTimeout as exc:
            attempts.append(
                ReflexionAttempt(
                    attempt_number,
                    sql,
                    str(exc),
                    "circuit_breaker_timeout",
                )
            )
            logger.warning("[Reflexion] Attempt %s stopped by circuit breaker: %s", attempt_number, exc)
            await _notify(
                on_step,
                f"⏱️ Circuit Breaker dừng truy vấn: {exc}",
                attempt_number,
            )
            return ReflexionTrace(
                "circuit_breaker_timeout",
                attempts,
                None,
                exc.elapsed_seconds,
            )
        except Exception as exc:
            message = str(exc) or exc.__class__.__name__
            decision = classify_failure("engine", message)
            if decision == "timeout":
                attempts.append(
                    ReflexionAttempt(attempt_number, sql, message, "circuit_breaker_timeout")
                )
                await _notify(
                    on_step,
                    f"⏱️ Circuit Breaker dừng truy vấn: {message}",
                    attempt_number,
                )
                return ReflexionTrace("circuit_breaker_timeout", attempts, None, elapsed_seconds)
            attempts.append(ReflexionAttempt(attempt_number, sql, message, "error_engine"))
            logger.warning("[Reflexion] Attempt %s failed at Trino: %s", attempt_number, message)
            if decision != "retry" or attempt_number == max_iterations:
                stop_message = (
                    f"🛑 Hết số lần tự sửa: {message}"
                    if decision == "retry"
                    else f"🛑 Lỗi này không được tự sửa. Dừng Reflexion: {message}"
                )
                await _notify(on_step, stop_message, attempt_number)
                status = "failed_after_max_iterations" if decision == "retry" else "aborted"
                return ReflexionTrace(status, attempts, None, elapsed_seconds)
            revised = await _revised_sql(reflect, sql, message)
            if revised is None:
                await _notify(
                    on_step,
                    "🛑 LLM không trả về SQL sửa hợp lệ. Dừng Reflexion.",
                    attempt_number,
                )
                return ReflexionTrace("aborted", attempts, None, elapsed_seconds)
            await _notify(
                on_step,
                "🔄 Trino báo lỗi, đang tự phản ngẫm "
                f"(Reflexion lần {attempt_number}): {message}",
                attempt_number,
            )
            sql = revised
            continue

        attempts.append(ReflexionAttempt(attempt_number, sql, "", "success"))
        logger.info("[Reflexion] Attempt %s succeeded", attempt_number)
        await _notify(on_step, "✅ Trino thực thi thành công.", attempt_number)
        return ReflexionTrace("success", attempts, data, elapsed_seconds)

    return ReflexionTrace("failed_after_max_iterations", attempts, None, elapsed_seconds)
