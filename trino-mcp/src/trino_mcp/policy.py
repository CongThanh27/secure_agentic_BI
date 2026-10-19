"""Role table permissions loaded from agent_role_permissions."""

import re
from dataclasses import dataclass

from .utils import referenced_tables

_ROLE_NAME = re.compile(r"^[a-z][a-z0-9_]{0,40}$")

_POLICY_SQL = """
SELECT allowed_tables, denied_tables, can_export_file
FROM mysql.agentic_bi.agent_role_permissions
WHERE role_name = '{role}'
ORDER BY id DESC
LIMIT 1
"""


@dataclass(frozen=True)
class RolePolicy:
    allowed_tables: frozenset[str]
    denied_tables: frozenset[str]
    can_export_file: bool
    allow_all: bool


def _split_tables(raw: str) -> frozenset[str]:
    return frozenset(part.strip().lower() for part in raw.split(";") if part.strip())


def policy_from_row(row: dict) -> RolePolicy:
    allowed_raw = str(row.get("allowed_tables") or "").strip()
    denied_raw = str(row.get("denied_tables") or "").strip()
    export_raw = row.get("can_export_file", False)
    can_export = export_raw is True or str(export_raw).lower() in {"true", "1"}
    return RolePolicy(
        allowed_tables=_split_tables(allowed_raw) if allowed_raw != "*" else frozenset(),
        denied_tables=_split_tables(denied_raw),
        can_export_file=can_export,
        allow_all=allowed_raw == "*",
    )


def load_role_policy(client, role: str) -> RolePolicy | None:
    """Load the newest permission row for a role. Unknown or unsafe names are None."""
    if not role or not _ROLE_NAME.fullmatch(role):
        return None
    rows = client.execute_query(_POLICY_SQL.format(role=role))
    if not isinstance(rows, list) or not rows:
        return None
    return policy_from_row(rows[0])


def check_table_access(query: str, policy: RolePolicy, output_file: str = "") -> str | None:
    """Return an error string when the query is outside the role, else None."""
    if output_file and not policy.can_export_file:
        return "Error: role is not allowed to export files."

    tables = referenced_tables(query)
    if tables is None:
        return "Error: SQL could not be parsed for permission check."

    for table in tables:
        if table.count(".") != 2:
            return (
                f"Error: table '{table}' must be fully qualified as catalog.schema.table."
            )
        if table in policy.denied_tables:
            return f"Error: role is not allowed to read '{table}'."
        if not policy.allow_all and table not in policy.allowed_tables:
            return f"Error: role is not allowed to read '{table}'."
    return None
