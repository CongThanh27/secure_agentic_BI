"""Retry one SQL statement when the gateway reports a technical error.

Security denials stop immediately. The reflector may replace the SQL text only.
"""

import json
from dataclasses import dataclass, field
from typing import Callable, Literal, Optional

MAX_REFLECTION_RETRIES = 2

_ABORT_MARKERS = (
    "does not appear to be read-only",
    "Write queries are disabled",
    "role is not allowed",
    "is not permitted",
    "role is required",
    "LỖI GUARDRAIL",
    "concurrent query slot",
    "timed out",
    "QueryTimeout",
)

_RETRY_MARKERS = (
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

_REFLECTION_TEMPLATE = """
You fix one failed Trino SQL statement. The gateway rejected it for a technical reason.
Keep the user's question. Do not change tables in order to reach data the gateway refused.
Return only this JSON object:
{{
  "query": "one SQL statement without a trailing semicolon"
}}

User question:
{question}

Failed SQL:
{sql}

Gateway error:
{error}
"""


def _is_error_result(result: str) -> bool:
    text = (result or "").lstrip()
    return (
        text.startswith("Error:")
        or text.startswith("Error executing query:")
        or text.startswith("LỖI GUARDRAIL")
    )


def classify_execution(result: str) -> Literal["ok", "abort", "retry"]:
    """Classify a tool result. Row text is ignored unless the result is an error."""
    if not _is_error_result(result):
        return "ok"
    if any(marker in result for marker in _ABORT_MARKERS):
        return "abort"
    if any(marker in result for marker in _RETRY_MARKERS):
        return "retry"
    return "abort"


def reflection_prompt(user_prompt: str, failed_sql: str, error: str) -> str:
    return _REFLECTION_TEMPLATE.format(
        question=user_prompt,
        sql=failed_sql,
        error=error,
    )


def parse_reflected_sql(raw: str) -> Optional[str]:
    """Read the query field. Extra keys are ignored."""
    text = (raw or "").replace("```json", "").replace("```", "").strip()
    try:
        payload = json.loads(text)
    except json.JSONDecodeError:
        return None
    if not isinstance(payload, dict):
        return None
    query = payload.get("query")
    if not isinstance(query, str) or not query.strip():
        return None
    return query.strip().rstrip(";").strip() or None


@dataclass
class Attempt:
    query: str
    result: str
    outcome: str


@dataclass
class ReflexionTrace:
    query: str
    result: str
    outcome: str
    attempts: list[Attempt] = field(default_factory=list)


def execute_with_reflexion(
    query: str,
    execute: Callable[[str], str],
    reflect: Callable[[str, str], Optional[str]],
    max_retries: int = MAX_REFLECTION_RETRIES,
) -> ReflexionTrace:
    """Run SQL, then rewrite it at most max_retries times after a technical error."""
    current = query.strip()
    attempts: list[Attempt] = []
    for index in range(max_retries + 1):
        result = execute(current)
        decision = classify_execution(result)
        if decision == "retry" and index < max_retries:
            revised = reflect(current, result)
            if revised is None or not revised.strip():
                attempts.append(Attempt(current, result, "abort"))
                return ReflexionTrace(current, result, "abort", attempts)
            attempts.append(Attempt(current, result, "retry"))
            current = revised.strip().rstrip(";").strip()
            continue
        final = "exhausted" if decision == "retry" else decision
        attempts.append(Attempt(current, result, final))
        return ReflexionTrace(current, result, final, attempts)
    raise RuntimeError("reflexion loop exited without a result")


def reflect_query(
    user_prompt: str, failed_sql: str, error: str, active_model: str
) -> Optional[str]:
    """Ask the model for a replacement SQL statement. Returns None when parsing fails."""
    from .llm import call_llm_with_fallback

    try:
        raw_text, _used_model = call_llm_with_fallback(
            reflection_prompt(user_prompt, failed_sql, error),
            active_model,
        )
    except Exception:
        return None
    return parse_reflected_sql(raw_text)
