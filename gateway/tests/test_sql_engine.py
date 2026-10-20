from pathlib import Path

import pytest

from app.config import Settings
from app.core.exceptions import GatewayError
from app.services.rbac_engine import policy_from_row
from app.services.sql_engine import SQLSecurityEngine


@pytest.fixture
def policy():
    return policy_from_row(
        {
            "id": 1,
            "role_name": "analyst",
            "allowed_catalogs": "pg",
            "allowed_tables": "pg.public.orders;pg.public.products",
            "denied_tables": "pg.public.hr_payroll",
            "can_export_file": 0,
            "max_row_limit": 100,
            "can_execute_ddl": 0,
            "can_access_pii": 0,
        }
    )


@pytest.fixture
def engine():
    return SQLSecurityEngine(
        Settings(
            principal_id="test",
            principal_roles={"test": "analyst"},
            mysql_host="localhost",
            mysql_port=3306,
            mysql_database="agentic_bi",
            mysql_user="",
            mysql_password="",
            mcp_server_command="",
            mcp_server_args=[],
            mcp_server_cwd=Path("/tmp/trino-mcp"),
            mcp_timeout_seconds=30,
            export_root=Path("/tmp/gateway-exports"),
            pii_tables=frozenset({"customers", "employees"}),
            log_level="INFO",
        )
    )


def test_safe_select_adds_policy_row_limit(engine, policy) -> None:
    analysis = engine.analyze("SELECT * FROM pg.public.orders", policy)

    assert "LIMIT 100" in analysis.query.upper()
    assert analysis.tables == frozenset({"pg.public.orders"})


def test_existing_limit_is_capped(engine, policy) -> None:
    analysis = engine.analyze(
        "SELECT * FROM pg.public.orders LIMIT 999", policy
    )

    assert "LIMIT 100" in analysis.query.upper()


@pytest.mark.parametrize(
    "query",
    [
        "DELETE FROM pg.public.orders",
        "SELECT * FROM pg.public.orders; DROP TABLE pg.public.orders",
        "SELECT * FROM pg.public.orders CROSS JOIN pg.public.products",
        "SELECT * FROM pg.public.orders, pg.public.products",
    ],
)
def test_write_multi_statement_and_cross_join_are_rejected(engine, policy, query) -> None:
    with pytest.raises(GatewayError):
        engine.analyze(query, policy)


def test_cte_authorizes_underlying_table(engine, policy) -> None:
    analysis = engine.analyze(
        "WITH recent AS (SELECT * FROM pg.public.orders) SELECT * FROM recent",
        policy,
    )

    assert analysis.tables == frozenset({"pg.public.orders"})


def test_explain_validates_and_limits_inner_select(engine, policy) -> None:
    analysis = engine.analyze(
        "EXPLAIN SELECT * FROM pg.public.orders", policy
    )

    assert analysis.query.upper().startswith("EXPLAIN SELECT")
    assert "LIMIT 100" in analysis.query.upper()
    assert analysis.tables == frozenset({"pg.public.orders"})


def test_show_tables_is_limited_to_allowed_metadata_scope(engine, policy) -> None:
    analysis = engine.analyze("SHOW TABLES FROM pg.public", policy)

    assert analysis.metadata_kind == "tables"
    assert analysis.metadata_catalog == "pg"
    assert analysis.metadata_schema == "public"


def test_unsafe_show_commands_are_rejected(engine, policy) -> None:
    with pytest.raises(GatewayError):
        engine.analyze("SHOW CREATE TABLE pg.public.orders", policy)


def test_unauthorized_join_table_is_rejected(engine, policy) -> None:
    with pytest.raises(GatewayError, match="Table access"):
        engine.analyze(
            "SELECT * FROM pg.public.orders JOIN pg.public.hr_payroll "
            "ON orders.id = hr_payroll.id",
            policy,
        )
