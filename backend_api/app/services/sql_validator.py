import logging
import re
from collections.abc import Mapping
from typing import Any

import sqlglot
from sqlglot import expressions as exp
from sqlglot.errors import ParseError

from app.services.rbac_service import RolePermissions

logger = logging.getLogger(__name__)

_DANGEROUS_NODES = (
    exp.Insert,
    exp.Update,
    exp.Delete,
    exp.Drop,
    exp.Alter,
    exp.Create,
    exp.Grant,
    exp.Revoke,
)
_IDENTIFIER_PATTERN = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*$")


def _policy_values(permissions: Mapping[str, Any], key: str) -> set[str]:
    value = permissions.get(key, [])
    if isinstance(value, str):
        values = value.split(",")
    else:
        values = [
            item
            for policy_value in value
            for item in str(policy_value).split(",")
        ]
    return {item.strip().lower() for item in values if item.strip()}


def _default_namespace(
    permissions: RolePermissions,
) -> tuple[str | None, str | None]:
    catalogs = _policy_values(permissions, "allowed_catalogs")
    default_catalog = next(iter(catalogs), None) if len(catalogs) == 1 else None
    return default_catalog, "public"


def _qualified_table_name(
    table: exp.Table, permissions: RolePermissions
) -> str:
    default_catalog, default_schema = _default_namespace(permissions)
    catalog = table.catalog or default_catalog
    schema = table.db or default_schema
    if not table.catalog:
        allowed_tables = _policy_values(permissions, "allowed_tables")
        suffix = f".{schema}.{table.name}".lower()
        matches = [
            identifier
            for identifier in allowed_tables
            if identifier.endswith(suffix)
        ]
        if len(matches) == 1:
            return matches[0]
    if not catalog or not schema or not table.name:
        return ".".join(
            part for part in (catalog, schema, table.name) if part
        ).lower()
    return f"{catalog}.{schema}.{table.name}".lower()


def _is_allowed_table(
    identifier: str,
    permissions: RolePermissions,
) -> bool:
    allowed_tables = _policy_values(permissions, "allowed_tables")
    allowed_catalogs = _policy_values(permissions, "allowed_catalogs")
    denied_tables = _policy_values(permissions, "denied_tables")
    if identifier in denied_tables:
        return False
    if "*" in allowed_tables or identifier in allowed_tables:
        return True
    catalog = identifier.split(".", maxsplit=1)[0]
    return catalog in allowed_catalogs


def _reject(reason: str) -> tuple[bool, str]:
    logger.warning("SQL AST guardrail blocked query: %s", reason)
    return False, reason


def validate_sql_ast(
    sql: str, role_permissions: RolePermissions
) -> tuple[bool, str]:
    """Parse and enforce read-only, RBAC, and resource-control policies."""
    if not sql or not sql.strip():
        return _reject("SQL query is empty")
    if ";" in sql:
        return _reject("SQL must contain exactly one statement without semicolons")

    try:
        parsed = sqlglot.parse_one(sql, read="trino")
    except ParseError as exc:
        return _reject(f"SQL parse error: {exc}")

    if not isinstance(parsed, exp.Select):
        return _reject("Only SELECT queries are allowed")
    for node_type in _DANGEROUS_NODES:
        if next(parsed.find_all(node_type), None) is not None:
            return _reject("DML or DDL statements are not allowed")

    for with_clause in parsed.find_all(exp.With):
        if with_clause.args.get("recursive") is True:
            return _reject("Recursive WITH queries are not allowed")

    for join in parsed.find_all(exp.Join):
        if (
            str(join.args.get("side", "")).upper() == "CROSS"
            or join.args.get("kind") == "CROSS"
        ):
            return _reject("CROSS JOIN is not allowed")
        if not join.args.get("on") and not join.args.get("using"):
            return _reject("JOIN requires an ON or USING condition")

    cte_names = {
        cte.alias_or_name.lower() for cte in parsed.find_all(exp.CTE)
    }
    for table in parsed.find_all(exp.Table):
        if not table.catalog and not table.db and table.name.lower() in cte_names:
            continue
        identifier = _qualified_table_name(table, role_permissions)
        if not _is_allowed_table(identifier, role_permissions):
            return _reject(f"Table is outside RBAC scope: {identifier}")

    return True, ""
