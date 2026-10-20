from dataclasses import dataclass
from typing import Any

import pymysql
from pymysql.cursors import DictCursor

from app.config import Settings
from app.core.exceptions import PolicyError


@dataclass(frozen=True)
class RolePolicy:
    policy_id: int
    role_name: str
    allowed_catalogs: frozenset[str]
    allowed_tables: frozenset[str]
    denied_tables: frozenset[str]
    can_export_file: bool
    max_row_limit: int
    can_execute_ddl: bool
    can_access_pii: bool

    def allows_catalog(self, catalog: str) -> bool:
        return catalog.lower() in self.allowed_catalogs

    def allows_table(self, table: str) -> bool:
        normalized = table.lower()
        if normalized in self.denied_tables:
            return False
        return "*" in self.allowed_tables or normalized in self.allowed_tables


def _split_values(value: Any, separator: str = ";") -> frozenset[str]:
    if value is None:
        return frozenset()
    if isinstance(value, bytes):
        value = value.decode("utf-8")
    return frozenset(
        part.strip().lower() for part in str(value).split(separator) if part.strip()
    )


def policy_from_row(row: dict[str, Any]) -> RolePolicy:
    allowed_catalogs = _split_values(row["allowed_catalogs"], separator=",")
    max_row_limit = int(row["max_row_limit"])
    if max_row_limit < 1:
        raise PolicyError("INVALID_ROLE_POLICY", "Policy row limit must be positive")
    return RolePolicy(
        policy_id=int(row["id"]),
        role_name=str(row["role_name"]),
        allowed_catalogs=allowed_catalogs,
        allowed_tables=_split_values(row["allowed_tables"]),
        denied_tables=_split_values(row["denied_tables"]),
        can_export_file=bool(row["can_export_file"]),
        max_row_limit=max_row_limit,
        can_execute_ddl=bool(row["can_execute_ddl"]),
        can_access_pii=bool(row["can_access_pii"]),
    )


class RBACEngine:
    def __init__(self, config: Settings) -> None:
        self._config = config

    def get_policy_for_principal(self, principal_id: str) -> RolePolicy:
        role = self._config.principal_roles.get(principal_id)
        if not principal_id or not role:
            raise PolicyError("PRINCIPAL_NOT_MAPPED", "Principal has no configured role")

        connection = None
        try:
            connection = pymysql.connect(
                host=self._config.mysql_host,
                port=self._config.mysql_port,
                user=self._config.mysql_user,
                password=self._config.mysql_password,
                database=self._config.mysql_database,
                cursorclass=DictCursor,
                connect_timeout=5,
                read_timeout=5,
                write_timeout=5,
                autocommit=True,
            )
            with connection.cursor() as cursor:
                cursor.execute(
                    """
                    SELECT id, role_name, allowed_catalogs, allowed_tables,
                           denied_tables, can_export_file, max_row_limit,
                           can_execute_ddl, can_access_pii
                    FROM agent_role_permissions
                    WHERE role_name = %s
                    ORDER BY id DESC
                    LIMIT 1
                    """,
                    (role,),
                )
                row = cursor.fetchone()
                print(row)
        except Exception as exc:
            raise PolicyError("POLICY_SOURCE_UNAVAILABLE", "Could not load access policy") from exc
        finally:
            if connection is not None:
                connection.close()

        if row is None:
            raise PolicyError("ROLE_POLICY_NOT_FOUND", "No policy exists for configured role")
        return policy_from_row(row)
