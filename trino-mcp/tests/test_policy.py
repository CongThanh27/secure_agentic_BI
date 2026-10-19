"""Role permission checks. No live Trino connection."""

from unittest.mock import MagicMock

from trino_mcp.policy import check_table_access, load_role_policy, policy_from_row
from trino_mcp.utils import referenced_tables

ANALYST_ROW = {
    "allowed_tables": (
        "pg.public.regions;pg.public.categories;pg.public.products;"
        "pg.public.orders;pg.public.order_items;"
        "mysql.agentic_bi.customer_profiles;mysql.agentic_bi.customer_reviews"
    ),
    "denied_tables": (
        "pg.public.hr_payroll;pg.public.api_keys_config;pg.public.financial_transactions"
    ),
    "can_export_file": False,
}

ADMIN_ROW = {
    "allowed_tables": "*",
    "denied_tables": "",
    "can_export_file": True,
}


def test_referenced_tables_skips_cte_alias():
    names = referenced_tables(
        "WITH cte AS (SELECT * FROM pg.public.orders) SELECT * FROM cte"
    )
    assert names == ["pg.public.orders"]


def test_analyst_can_read_orders():
    policy = policy_from_row(ANALYST_ROW)
    assert check_table_access("SELECT * FROM pg.public.orders", policy) is None


def test_analyst_cannot_read_hr_payroll():
    policy = policy_from_row(ANALYST_ROW)
    denial = check_table_access("SELECT * FROM pg.public.hr_payroll", policy)
    assert denial is not None
    assert "hr_payroll" in denial


def test_analyst_cannot_export():
    policy = policy_from_row(ANALYST_ROW)
    denial = check_table_access(
        "SELECT * FROM pg.public.orders", policy, output_file="out.csv"
    )
    assert denial is not None
    assert "export" in denial


def test_unqualified_table_rejected():
    policy = policy_from_row(ANALYST_ROW)
    denial = check_table_access("SELECT * FROM orders", policy)
    assert denial is not None
    assert "fully qualified" in denial


def test_admin_wildcard_can_read_restricted_table():
    policy = policy_from_row(ADMIN_ROW)
    assert check_table_access("SELECT * FROM pg.public.hr_payroll", policy) is None


def test_unknown_role_rejected():
    client = MagicMock()
    client.execute_query.return_value = []
    assert load_role_policy(client, "intern") is None


def test_unsafe_role_name_is_not_queried():
    client = MagicMock()
    assert load_role_policy(client, "admin' OR '1'='1") is None
    client.execute_query.assert_not_called()
