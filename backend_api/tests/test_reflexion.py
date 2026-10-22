"""Guarded Reflexion: retry technical SQL errors and abort security denials."""

import asyncio

from app.services.reflexion import (
    ReflexionTimeout,
    classify_failure,
    execute_with_reflexion,
    parse_reflected_sql,
    reflection_prompt,
)


def test_rbac_denial_aborts():
    reason = "Table is outside RBAC scope: pg.public.hr_payroll"
    assert classify_failure("ast", reason) == "abort"


def test_read_only_and_ddl_denials_abort():
    assert classify_failure("ast", "Only SELECT queries are allowed") == "abort"
    assert classify_failure("ast", "DML or DDL statements are not allowed") == "abort"
    assert classify_failure("ast", "CROSS JOIN is not allowed") == "abort"
    assert (
        classify_failure("ast", "SQL must contain exactly one statement without semicolons")
        == "abort"
    )


def test_parse_and_join_shape_errors_retry():
    assert classify_failure("ast", "SQL parse error: Expecting )") == "retry"
    assert classify_failure("ast", "JOIN requires an ON or USING condition") == "retry"


def test_column_and_table_errors_retry():
    message = (
        "TrinoUserError(type=USER_ERROR, name=COLUMN_NOT_FOUND, "
        "message=\"Column 'revnue' cannot be resolved\")"
    )
    assert classify_failure("engine", message) == "retry"
    assert (
        classify_failure("engine", "TABLE_NOT_FOUND: Table 'pg.public.order' cannot be resolved")
        == "retry"
    )
    assert classify_failure("engine", "SYNTAX_ERROR: mismatched input 'FORM'") == "retry"


def test_security_marker_aborts_before_a_technical_marker():
    message = "Error: role is not allowed to read 'pg.public.hr_payroll'. cannot be resolved"
    assert classify_failure("engine", message) == "abort"


def test_unknown_engine_error_aborts():
    assert classify_failure("engine", "connection reset by peer") == "abort"


def test_timeout_messages_stop_the_loop():
    assert classify_failure("timeout", "anything") == "timeout"
    assert classify_failure("engine", "Trino query timed out") == "timeout"
    assert classify_failure("engine", "Trino query exceeded timeout of 5.000 seconds") == "timeout"


def test_reflection_prompt_keeps_the_question_and_forbids_table_evasion():
    prompt = reflection_prompt(
        "doanh thu tháng này",
        "SELECT revnue FROM pg.public.orders",
        "COLUMN_NOT_FOUND",
    )
    assert "doanh thu tháng này" in prompt
    assert "SELECT revnue FROM pg.public.orders" in prompt
    assert "COLUMN_NOT_FOUND" in prompt
    assert '"query"' in prompt
    assert "Do not change tables" in prompt
    assert "output_file" not in prompt


def test_parse_reflected_sql_reads_query_only():
    raw = '{"query": "SELECT 1", "output_file": "/etc/passwd"}'
    assert parse_reflected_sql(raw) == "SELECT 1"


def test_parse_reflected_sql_strips_fence_semicolon_and_rejects_empty():
    assert parse_reflected_sql('```json\n{"query": "SELECT 1;"}\n```') == "SELECT 1"
    assert parse_reflected_sql('{"query": "  "}') is None
    assert parse_reflected_sql("not json") is None
    assert parse_reflected_sql('{"thought": "no query"}') is None


def _run(coro):
    return asyncio.run(coro)


def test_security_denial_does_not_call_reflector_or_engine():
    async def scenario():
        async def plan(_feedback):
            return "SELECT * FROM pg.public.hr_payroll"

        async def validate(_sql):
            return False, "Table is outside RBAC scope: pg.public.hr_payroll"

        async def execute(_sql):
            raise AssertionError("query must not run after a security denial")

        async def reflect(_sql, _error):
            raise AssertionError("reflector must not run after a security denial")

        return await execute_with_reflexion(
            "lương nhân viên",
            plan=plan,
            validate=validate,
            execute=execute,
            reflect=reflect,
            max_iterations=3,
        )

    trace = _run(scenario())
    assert trace.status == "aborted"
    assert len(trace.attempts) == 1
    assert trace.attempts[0].status == "error_ast"
    assert trace.data is None


def test_timeout_aborts_without_reflection():
    calls = {"reflect": 0}

    async def scenario():
        async def plan(_feedback):
            return "SELECT 1"

        async def validate(_sql):
            return True, ""

        async def execute(_sql):
            raise ReflexionTimeout("Trino query timed out", 5.0)

        async def reflect(_sql, _error):
            calls["reflect"] += 1
            return "SELECT 1"

        return await execute_with_reflexion(
            "doanh thu",
            plan=plan,
            validate=validate,
            execute=execute,
            reflect=reflect,
            max_iterations=3,
        )

    trace = _run(scenario())
    assert calls["reflect"] == 0
    assert trace.status == "circuit_breaker_timeout"
    assert trace.execution_time_seconds == 5.0
    assert trace.attempts[0].status == "circuit_breaker_timeout"


def test_unknown_engine_error_aborts_without_reflection():
    calls = {"reflect": 0, "execute": 0}

    async def scenario():
        async def plan(_feedback):
            return "SELECT 1"

        async def validate(_sql):
            return True, ""

        async def execute(_sql):
            calls["execute"] += 1
            raise RuntimeError("connection reset by peer")

        async def reflect(_sql, _error):
            calls["reflect"] += 1
            return "SELECT 2"

        return await execute_with_reflexion(
            "doanh thu",
            plan=plan,
            validate=validate,
            execute=execute,
            reflect=reflect,
            max_iterations=3,
        )

    trace = _run(scenario())
    assert calls == {"reflect": 0, "execute": 1}
    assert trace.status == "aborted"
    assert trace.attempts[0].status == "error_engine"


def test_empty_rewrite_aborts_without_another_execution():
    calls = {"execute": 0}

    async def scenario():
        async def plan(_feedback):
            return "SELECT 1 FROM pg.public.order"

        async def validate(_sql):
            return True, ""

        async def execute(_sql):
            calls["execute"] += 1
            raise RuntimeError(
                "TABLE_NOT_FOUND: Table 'pg.public.order' cannot be resolved"
            )

        async def reflect(_sql, _error):
            return "   "

        return await execute_with_reflexion(
            "đơn hàng",
            plan=plan,
            validate=validate,
            execute=execute,
            reflect=reflect,
            max_iterations=3,
        )

    trace = _run(scenario())
    assert calls["execute"] == 1
    assert trace.status == "aborted"
    assert len(trace.attempts) == 1


def test_technical_error_retries_then_stops_at_max_iterations():
    seen: list[str] = []

    async def scenario():
        async def plan(_feedback):
            return "SELECT revnue FROM pg.public.orders"

        async def validate(_sql):
            return True, ""

        revisions = iter(
            [
                "SELECT revenue FROM pg.public.orders",
                "SELECT total_amount FROM pg.public.orders",
                "SELECT should_not_be_used FROM pg.public.orders",
            ]
        )

        async def execute(sql):
            seen.append(sql)
            raise RuntimeError("COLUMN_NOT_FOUND: Column 'revnue' cannot be resolved")

        async def reflect(_sql, _error):
            return next(revisions)

        return await execute_with_reflexion(
            "doanh thu",
            plan=plan,
            validate=validate,
            execute=execute,
            reflect=reflect,
            max_iterations=3,
        )

    trace = _run(scenario())
    assert seen == [
        "SELECT revnue FROM pg.public.orders",
        "SELECT revenue FROM pg.public.orders",
        "SELECT total_amount FROM pg.public.orders",
    ]
    assert trace.status == "failed_after_max_iterations"
    assert trace.attempts[-1].generated_sql == "SELECT total_amount FROM pg.public.orders"


def test_rewritten_sql_succeeds_and_ignores_extra_reflector_keys():
    async def scenario():
        async def plan(_feedback):
            return "SELECT revnue FROM pg.public.orders"

        async def validate(_sql):
            return True, ""

        async def execute(sql):
            if sql == "SELECT total_amount FROM pg.public.orders":
                return [{"total_amount": 10}], 0.02
            raise RuntimeError("COLUMN_NOT_FOUND: Column 'revnue' cannot be resolved")

        async def reflect(_sql, _error):
            return parse_reflected_sql(
                '{"query": "SELECT total_amount FROM pg.public.orders", "output_file": "/etc/passwd"}'
            )

        return await execute_with_reflexion(
            "doanh thu",
            plan=plan,
            validate=validate,
            execute=execute,
            reflect=reflect,
            max_iterations=3,
        )

    trace = _run(scenario())
    assert trace.status == "success"
    assert trace.data == [{"total_amount": 10}]
    assert len(trace.attempts) == 2
    assert trace.attempts[-1].status == "success"


def test_reflected_sql_that_escapes_rbac_aborts_without_execution():
    executed: list[str] = []

    async def scenario():
        async def plan(_feedback):
            return "SELECT totl FORM pg.public.orders"

        async def validate(sql):
            if "hr_payroll" in sql:
                return False, "Table is outside RBAC scope: pg.public.hr_payroll"
            return True, ""

        async def execute(sql):
            executed.append(sql)
            raise RuntimeError("SYNTAX_ERROR: mismatched input 'FORM'")

        async def reflect(_sql, _error):
            return "SELECT salary FROM pg.public.hr_payroll"

        return await execute_with_reflexion(
            "doanh thu",
            plan=plan,
            validate=validate,
            execute=execute,
            reflect=reflect,
            max_iterations=3,
        )

    trace = _run(scenario())
    assert executed == ["SELECT totl FORM pg.public.orders"]
    assert trace.status == "aborted"
    assert trace.attempts[-1].status == "error_ast"


def test_plan_failures_retry_the_planner_not_the_sql_reflector():
    calls = {"plan": 0, "reflect": 0}

    async def scenario():
        async def plan(_feedback):
            calls["plan"] += 1
            if calls["plan"] == 1:
                raise ValueError("Gemini returned invalid JSON")
            return "SELECT 1"

        async def validate(_sql):
            return True, ""

        async def execute(_sql):
            return [{"ok": 1}], 0.0

        async def reflect(_sql, _error):
            calls["reflect"] += 1
            return "SELECT 2"

        return await execute_with_reflexion(
            "một",
            plan=plan,
            validate=validate,
            execute=execute,
            reflect=reflect,
            max_iterations=3,
        )

    trace = _run(scenario())
    assert calls == {"plan": 2, "reflect": 0}
    assert trace.status == "success"
    assert trace.attempts[0].status == "error_llm"
