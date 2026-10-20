from app.services.rbac_engine import policy_from_row


def test_denied_tables_override_allowlist_and_star() -> None:
    policy = policy_from_row(
        {
            "id": 7,
            "role_name": "analyst",
            "allowed_catalogs": "pg,mysql",
            "allowed_tables": "*",
            "denied_tables": "pg.public.hr_payroll",
            "can_export_file": 0,
            "max_row_limit": 100,
            "can_execute_ddl": 0,
            "can_access_pii": 0,
        }
    )

    assert policy.allows_catalog("pg")
    assert policy.allows_table("pg.public.orders")
    assert not policy.allows_table("pg.public.hr_payroll")


def test_policy_table_lists_are_normalized() -> None:
    policy = policy_from_row(
        {
            "id": 8,
            "role_name": "analyst",
            "allowed_catalogs": "PG, mysql",
            "allowed_tables": "PG.public.orders; mysql.agentic_bi.customer_profiles",
            "denied_tables": "",
            "can_export_file": 0,
            "max_row_limit": 25,
            "can_execute_ddl": 0,
            "can_access_pii": 0,
        }
    )

    assert policy.allows_catalog("pg")
    assert policy.allows_table("pg.public.orders")
    assert not policy.allows_table("pg.public.hr_payroll")
