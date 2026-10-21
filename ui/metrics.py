"""Session KPIs and audit rows. No Streamlit imports."""

from typing import Optional

from agent.reflexion import classify_execution

AUDIT_COLUMNS = [
    "Thời điểm",
    "Role",
    "Model",
    "Kịch bản",
    "Outcome",
    "Guardrail",
    "SQL",
]

SQL_PREVIEW_LIMIT = 180


def truncate_sql(sql: str, limit: int = SQL_PREVIEW_LIMIT) -> str:
    text = (sql or "").strip()
    if len(text) <= limit:
        return text
    return text[: limit - 1].rstrip() + "…"


def classify_run(
    *,
    planner_ok: bool,
    trace_outcome: Optional[str],
    result: str,
    attempt_outcomes: list[str],
) -> str:
    """Map one pipeline result to ok, blocked, retried_ok, or failed."""
    if not planner_ok:
        return "failed"
    if trace_outcome == "ok":
        if "retry" in attempt_outcomes:
            return "retried_ok"
        return "ok"
    if classify_execution(result or "") == "abort" or trace_outcome == "abort":
        return "blocked"
    return "failed"


def guardrail_label(outcome: str, result: str) -> str:
    """Short guardrail name for a blocked run. Passing runs stay blank."""
    if outcome not in {"blocked"}:
        return "—"
    text = result or ""
    if (
        "does not appear to be read-only" in text
        or "Write queries are disabled" in text
    ):
        return "Read-only"
    if (
        "role is not allowed" in text
        or "is not permitted" in text
        or "role is required" in text
    ):
        return "RBAC"
    if (
        "Circuit Breaker" in text
        or "concurrent query slot" in text
        or "timed out" in text
        or "QueryTimeout" in text
    ):
        return "Giới hạn tài nguyên"
    if "LỖI GUARDRAIL" in text or outcome == "blocked":
        return "Guardrail"
    return "—"


def build_run_record(
    *,
    timestamp: str,
    role: str,
    model: str,
    scenario: str,
    latency_ms: int,
    planner_ok: bool,
    trace_outcome: Optional[str],
    result: str,
    attempt_outcomes: list[str],
    sql: str,
    thought: str = "",
    answer: str = "",
    synth_model: str = "",
    route_model: str = "",
    attempts: Optional[list[dict]] = None,
    tool_arguments: Optional[dict] = None,
) -> dict:
    outcome = classify_run(
        planner_ok=planner_ok,
        trace_outcome=trace_outcome,
        result=result,
        attempt_outcomes=attempt_outcomes,
    )
    return {
        "timestamp": timestamp,
        "role": role,
        "model": model,
        "scenario": scenario,
        "outcome": outcome,
        "guardrail": guardrail_label(outcome, result),
        "sql": truncate_sql(sql),
        "sql_full": (sql or "").strip(),
        "latency_ms": latency_ms,
        "thought": thought,
        "answer": answer,
        "synth_model": synth_model,
        "route_model": route_model,
        "result": result or "",
        "attempts": list(attempts or []),
        "tool_arguments": tool_arguments,
    }


def compute_kpis(runs: list[dict]) -> dict:
    total = len(runs)
    blocked = sum(1 for run in runs if run.get("outcome") == "blocked")
    retried_ok = sum(1 for run in runs if run.get("outcome") == "retried_ok")
    last_latency_ms = runs[-1].get("latency_ms") if runs else None
    block_rate = (blocked / total) if total else 0.0
    return {
        "total": total,
        "blocked": blocked,
        "retried_ok": retried_ok,
        "last_latency_ms": last_latency_ms,
        "block_rate": block_rate,
    }


def audit_rows(runs: list[dict]) -> list[dict]:
    return [
        {
            "Thời điểm": run.get("timestamp", ""),
            "Role": run.get("role", ""),
            "Model": run.get("model", ""),
            "Kịch bản": run.get("scenario", ""),
            "Outcome": run.get("outcome", ""),
            "Guardrail": run.get("guardrail", ""),
            "SQL": run.get("sql", ""),
        }
        for run in runs
    ]


def runs_to_csv(runs: list[dict]) -> str:
    import csv
    import io

    buffer = io.StringIO()
    writer = csv.DictWriter(buffer, fieldnames=AUDIT_COLUMNS, lineterminator="\n")
    writer.writeheader()
    writer.writerows(audit_rows(runs))
    return buffer.getvalue()
