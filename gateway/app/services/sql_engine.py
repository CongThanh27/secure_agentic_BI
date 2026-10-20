from dataclasses import dataclass
import re

import sqlglot
from sqlglot import exp
from sqlglot.errors import SqlglotError

from app.config import Settings
from app.core.exceptions import GatewayError
from app.services.rbac_engine import RolePolicy


@dataclass(frozen=True)
class SQLAnalysis:
    query: str
    tables: frozenset[str]
    metadata_kind: str | None = None
    metadata_catalog: str | None = None
    metadata_schema: str | None = None


class SQLSecurityEngine:
    _WRITE_NODES = (
        exp.Insert,
        exp.Update,
        exp.Delete,
        exp.Merge,
        exp.Create,
        exp.Drop,
        exp.Alter,
        exp.Command,
        exp.Grant,
        exp.Revoke,
    )

    def __init__(self, config: Settings) -> None:
        self._config = config

    def analyze(self, query: str, policy: RolePolicy) -> SQLAnalysis:
        if not isinstance(query, str) or not query.strip():
            raise GatewayError("INVALID_SQL", "A non-empty SQL query is required")
        try:
            statements = sqlglot.parse(query, read="trino")
        except SqlglotError as exc:
            raise GatewayError("UNPARSEABLE_SQL", "SQL could not be safely parsed") from exc
        if len(statements) != 1 or statements[0] is None:
            raise GatewayError("MULTI_STATEMENT_FORBIDDEN", "Only one SQL statement is allowed")

        statement = statements[0]
        if isinstance(statement, exp.Command):
            command = str(statement.this).upper()
            expression = statement.expression
            command_text = (
                str(expression.this).strip()
                if isinstance(expression, exp.Literal) and expression.is_string
                else ""
            )
            if command == "EXPLAIN":
                explained = self.analyze(command_text, policy)
                if explained.metadata_kind is not None:
                    raise GatewayError("UNSAFE_EXPLAIN", "EXPLAIN only accepts SELECT queries")
                return SQLAnalysis(
                    query=f"EXPLAIN {explained.query}",
                    tables=explained.tables,
                )
            if command == "SHOW":
                return self._analyze_show(statement, command_text, policy)
            raise GatewayError("READ_ONLY_STATEMENT_REQUIRED", "Only read-only SQL is allowed")
        if isinstance(statement, self._WRITE_NODES) or statement.find(*self._WRITE_NODES):
            raise GatewayError("WRITE_OR_DDL_FORBIDDEN", "Write and DDL statements are forbidden")
        if not isinstance(statement, (exp.Select, exp.Describe)):
            raise GatewayError("READ_ONLY_STATEMENT_REQUIRED", "Only read-only SQL is allowed")

        if any(self._is_risky_join(join) for join in statement.find_all(exp.Join)):
            raise GatewayError("CROSS_JOIN_FORBIDDEN", "CROSS JOIN is not allowed")

        tables = self._referenced_tables(statement)
        if isinstance(statement, exp.Select):
            if not tables:
                raise GatewayError("TABLE_REFERENCE_REQUIRED", "Queries must reference an authorized table")
            for table in tables:
                catalog = table.split(".", 1)[0]
                if not policy.allows_catalog(catalog):
                    raise GatewayError("CATALOG_ACCESS_DENIED", "Catalog access is not permitted")
                if not policy.allows_table(table):
                    raise GatewayError("TABLE_ACCESS_DENIED", "Table access is not permitted")
                table_name = table.rsplit(".", 1)[-1]
                if (
                    not policy.can_access_pii
                    and (table_name in self._config.pii_tables or table in self._config.pii_tables)
                ):
                    raise GatewayError("PII_ACCESS_DENIED", "PII access is not permitted")

            self._apply_row_limit(statement, policy.max_row_limit)
            query = statement.sql(dialect="trino")
        else:
            query = statement.sql(dialect="trino")
            tables = self._referenced_tables(statement)
            for table in tables:
                catalog = table.split(".", 1)[0]
                if not policy.allows_catalog(catalog) or not policy.allows_table(table):
                    raise GatewayError("TABLE_ACCESS_DENIED", "Metadata access is not permitted")
        return SQLAnalysis(query=query, tables=frozenset(tables))

    @staticmethod
    def _is_risky_join(join: exp.Join) -> bool:
        return (
            (join.args.get("kind") or "").upper() == "CROSS"
            or (
                not join.args.get("on")
                and not join.args.get("using")
                and not join.args.get("method")
            )
        )

    @staticmethod
    def _analyze_show(
        statement: exp.Command, command_text: str, policy: RolePolicy
    ) -> SQLAnalysis:
        normalized_command = command_text.upper()
        if normalized_command == "CATALOGS":
            return SQLAnalysis(
                query=statement.sql(dialect="trino"),
                tables=frozenset(),
                metadata_kind="catalogs",
            )
        schema_match = re.fullmatch(
            r"SCHEMAS\s+FROM\s+([A-Za-z_][A-Za-z0-9_$]*)",
            command_text,
            flags=re.IGNORECASE,
        )
        if schema_match:
            catalog = schema_match.group(1).lower()
            if not policy.allows_catalog(catalog):
                raise GatewayError("CATALOG_ACCESS_DENIED", "Catalog access is not permitted")
            return SQLAnalysis(
                query=statement.sql(dialect="trino"),
                tables=frozenset(),
                metadata_kind="schemas",
                metadata_catalog=catalog,
            )
        tables_match = re.fullmatch(
            r"TABLES\s+FROM\s+([A-Za-z_][A-Za-z0-9_$]*)\.([A-Za-z_][A-Za-z0-9_$]*)",
            command_text,
            flags=re.IGNORECASE,
        )
        if tables_match:
            catalog, schema = (part.lower() for part in tables_match.groups())
            if not policy.allows_catalog(catalog):
                raise GatewayError("CATALOG_ACCESS_DENIED", "Catalog access is not permitted")
            return SQLAnalysis(
                query=statement.sql(dialect="trino"),
                tables=frozenset(),
                metadata_kind="tables",
                metadata_catalog=catalog,
                metadata_schema=schema,
            )
        raise GatewayError("UNSUPPORTED_SHOW_COMMAND", "This SHOW command is not allowed")

    @staticmethod
    def _referenced_tables(statement: exp.Expression) -> set[str]:
        cte_names = {
            cte.alias_or_name.lower() for cte in statement.find_all(exp.CTE)
        }
        result: set[str] = set()
        for table in statement.find_all(exp.Table):
            if not table.name:
                raise GatewayError("QUALIFIED_TABLE_REQUIRED", "Table name is required")
            if not table.catalog or not table.db:
                if table.name.lower() in cte_names and not table.catalog and not table.db:
                    continue
                raise GatewayError(
                    "QUALIFIED_TABLE_REQUIRED",
                    "Tables must be fully qualified as catalog.schema.table",
                )
            result.add(
                ".".join((table.catalog, table.db, table.name)).lower()
            )
        return result

    @staticmethod
    def _apply_row_limit(statement: exp.Select, maximum: int) -> None:
        limit = statement.args.get("limit")
        if limit is None:
            statement.set("limit", exp.Limit(expression=exp.Literal.number(maximum)))
            return
        expression = limit.args.get("expression")
        if not isinstance(expression, exp.Literal) or not expression.is_int:
            raise GatewayError("INVALID_ROW_LIMIT", "LIMIT must be an integer literal")
        if int(expression.this) > maximum:
            limit.set("expression", exp.Literal.number(maximum))
