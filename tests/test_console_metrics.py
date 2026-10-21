"""Session metrics and outcome labels for the defense console."""

import pytest

from ui.metrics import (
    classify_run,
    compute_kpis,
    guardrail_label,
    truncate_sql,
)
from ui.rbac_display import ROLES, ROLE_POLICY
from ui.scenarios import SCENARIOS, scenario_label_for_prompt


def test_kpis_block_rate_and_retry_count():
    runs = [
        {"outcome": "blocked", "latency_ms": 12},
        {"outcome": "blocked", "latency_ms": 18},
        {"outcome": "retried_ok", "latency_ms": 40},
    ]
    kpis = compute_kpis(runs)
    assert kpis["total"] == 3
    assert kpis["blocked"] == 2
    assert kpis["retried_ok"] == 1
    assert kpis["block_rate"] == pytest.approx(2 / 3)
    assert kpis["last_latency_ms"] == 40


def test_empty_session_kpis():
    kpis = compute_kpis([])
    assert kpis == {
        "total": 0,
        "blocked": 0,
        "retried_ok": 0,
        "last_latency_ms": None,
        "block_rate": 0.0,
    }


def test_ok_run_without_retry():
    assert (
        classify_run(
            planner_ok=True,
            trace_outcome="ok",
            result='[{"category": "A"}]',
            attempt_outcomes=["ok"],
        )
        == "ok"
    )


def test_retry_then_ok_is_retried_ok():
    assert (
        classify_run(
            planner_ok=True,
            trace_outcome="ok",
            result='[{"category": "A"}]',
            attempt_outcomes=["retry", "ok"],
        )
        == "retried_ok"
    )


def test_security_abort_is_blocked():
    result = "Error: role is not allowed to read 'pg.public.hr_payroll'."
    assert (
        classify_run(
            planner_ok=True,
            trace_outcome="abort",
            result=result,
            attempt_outcomes=["abort"],
        )
        == "blocked"
    )
    assert guardrail_label("blocked", result) == "RBAC"


def test_read_only_block_label():
    result = (
        "Error: This query does not appear to be read-only. "
        "The execute_query_read_only tool only accepts SELECT queries."
    )
    assert guardrail_label("blocked", result) == "Read-only"


def test_timeout_block_label():
    result = "LỖI GUARDRAIL TỪ UI (Circuit Breaker): Phát hiện tấn công DoS!"
    assert guardrail_label("blocked", result) == "Giới hạn tài nguyên"


def test_exhausted_retry_is_failed():
    result = "Error executing query: COLUMN_NOT_FOUND"
    assert (
        classify_run(
            planner_ok=True,
            trace_outcome="exhausted",
            result=result,
            attempt_outcomes=["retry", "exhausted"],
        )
        == "failed"
    )
    assert guardrail_label("failed", result) == "—"


def test_planner_failure_is_failed():
    assert (
        classify_run(
            planner_ok=False,
            trace_outcome=None,
            result="",
            attempt_outcomes=[],
        )
        == "failed"
    )


def test_truncate_sql():
    assert truncate_sql("select 1", limit=20) == "select 1"
    assert truncate_sql("x" * 30, limit=10).endswith("…")
    assert len(truncate_sql("x" * 30, limit=10)) == 10


def test_role_policy_matches_seed_roles():
    assert ROLES == ["analyst", "sales", "support", "hr", "admin"]
    assert "pg.public.hr_payroll" in ROLE_POLICY["analyst"]["denied_tables"]
    assert ROLE_POLICY["analyst"]["max_rows"] == 5000
    assert ROLE_POLICY["analyst"]["can_export"] is False
    assert ROLE_POLICY["sales"]["can_export"] is True
    assert ROLE_POLICY["sales"]["max_rows"] == 2000
    assert ROLE_POLICY["hr"]["allowed_tables"] == [
        "pg.public.employees",
        "mysql.agentic_bi.agent_query_history",
    ]
    assert ROLE_POLICY["admin"]["allowed_tables"] == ["*"]
    assert ROLE_POLICY["admin"]["denied_tables"] == []
    assert ROLE_POLICY["admin"]["max_rows"] == 10000


def test_catalog_has_26_scenarios():
    assert len(SCENARIOS) == 26
    assert [item.number for item in SCENARIOS] == list(range(1, 27))
    assert scenario_label_for_prompt(SCENARIOS[0].prompt) == SCENARIOS[0].title
    assert scenario_label_for_prompt("câu hỏi tự viết") == "Tùy chỉnh"
    assert SCENARIOS[0].science.startswith("Kịch bản nghiệp vụ baseline")
    assert "Pedro" in SCENARIOS[3].science
    assert SCENARIOS[25].filter_group == "Export"
