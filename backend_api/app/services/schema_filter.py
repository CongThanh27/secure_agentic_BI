import logging
from collections.abc import Mapping
from typing import Any

from app.services.rbac_service import RolePermissions

logger = logging.getLogger(__name__)


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


def filter_schema_by_rbac(
    raw_schema: list[dict[str, Any]], permissions: RolePermissions
) -> str:
    """Return Markdown metadata allowed by RBAC, with deny rules taking precedence."""
    allowed_tables = _policy_values(permissions, "allowed_tables")
    allowed_catalogs = _policy_values(permissions, "allowed_catalogs")
    denied_tables = _policy_values(permissions, "denied_tables")
    grouped_tables: dict[str, list[str]] = {}

    for table in raw_schema:
        catalog = str(table.get("table_catalog", "")).strip()
        schema = str(table.get("table_schema", "")).strip()
        name = str(table.get("table_name", "")).strip()
        if not catalog or not schema or not name:
            logger.warning("Skipping malformed metadata row: %r", table)
            continue

        identifier = f"{catalog}.{schema}.{name}"
        normalized_identifier = identifier.lower()
        if normalized_identifier in denied_tables:
            logger.info(
                "RBAC filtered denied table role=%s table=%s",
                permissions["role_name"],
                identifier,
            )
            continue

        is_allowed = (
            "*" in allowed_tables
            or normalized_identifier in allowed_tables
            or catalog.lower() in allowed_catalogs
        )
        if is_allowed:
            column_name = str(table.get("column_name", "")).strip()
            data_type = str(table.get("data_type", "")).strip()
            if not column_name or not data_type:
                logger.warning("Skipping metadata row without column details: %r", table)
                continue
            grouped_tables.setdefault(identifier, []).append(
                f"{column_name} {data_type}"
            )

    if not grouped_tables:
        return "No permitted tables found."

    return "\n".join(
        f"{index}. {identifier} ({', '.join(columns)})"
        for index, (identifier, columns) in enumerate(grouped_tables.items(), 1)
    )
