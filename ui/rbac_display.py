"""Role cards for the sidebar.

Values mirror the first five rows of agent_role_permissions in
docker/mysql/init/01_init_mysql.sql. The MCP gateway still enforces policy.
This module only explains the selected role on screen.
"""

ROLES = ["analyst", "sales", "support", "hr", "admin"]

ROLE_POLICY = {
    "analyst": {
        "allowed_catalogs": ["pg", "mysql"],
        "allowed_tables": [
            "pg.public.regions",
            "pg.public.categories",
            "pg.public.products",
            "pg.public.orders",
            "pg.public.order_items",
            "mysql.agentic_bi.customer_profiles",
            "mysql.agentic_bi.customer_reviews",
        ],
        "denied_tables": [
            "pg.public.hr_payroll",
            "pg.public.api_keys_config",
            "pg.public.financial_transactions",
        ],
        "can_export": False,
        "max_rows": 5000,
        "can_access_pii": False,
    },
    "sales": {
        "allowed_catalogs": ["pg", "mysql"],
        "allowed_tables": [
            "pg.public.customers",
            "pg.public.products",
            "pg.public.orders",
            "pg.public.order_items",
            "pg.public.payments",
            "mysql.agentic_bi.customer_profiles",
        ],
        "denied_tables": [
            "pg.public.hr_payroll",
            "pg.public.api_keys_config",
        ],
        "can_export": True,
        "max_rows": 2000,
        "can_access_pii": True,
    },
    "support": {
        "allowed_catalogs": ["mysql", "pg"],
        "allowed_tables": [
            "mysql.agentic_bi.customer_profiles",
            "mysql.agentic_bi.support_tickets",
            "mysql.agentic_bi.customer_reviews",
            "pg.public.orders",
        ],
        "denied_tables": [
            "pg.public.hr_payroll",
            "pg.public.api_keys_config",
            "pg.public.financial_transactions",
        ],
        "can_export": False,
        "max_rows": 1000,
        "can_access_pii": True,
    },
    "hr": {
        "allowed_catalogs": ["pg", "mysql"],
        "allowed_tables": [
            "pg.public.employees",
            "mysql.agentic_bi.agent_query_history",
        ],
        "denied_tables": [
            "pg.public.api_keys_config",
            "pg.public.financial_transactions",
        ],
        "can_export": False,
        "max_rows": 1000,
        "can_access_pii": True,
    },
    "admin": {
        "allowed_catalogs": ["pg", "mysql"],
        "allowed_tables": ["*"],
        "denied_tables": [],
        "can_export": True,
        "max_rows": 10000,
        "can_access_pii": True,
    },
}


def policy_for(role: str) -> dict:
    return ROLE_POLICY.get(role, ROLE_POLICY["analyst"])
