import asyncio
import hashlib
import json
import logging
from pathlib import Path
from time import monotonic
from typing import Any
from uuid import uuid4

from mcp.types import CallToolResult, TextContent, Tool

from app.config import Settings
from app.core.context import RequestContext
from app.core.exceptions import GatewayError, PolicyError
from app.services.proxy_client import ALLOWED_TOOLS, MCPProxyClient
from app.services.rbac_engine import RBACEngine, RolePolicy
from app.services.sql_engine import SQLAnalysis, SQLSecurityEngine
from app.utils.audit_logger import audit

logger = logging.getLogger("secure_gateway")


class GatewayService:
    def __init__(
        self,
        config: Settings,
        proxy: MCPProxyClient,
        rbac: RBACEngine | None = None,
        sql_engine: SQLSecurityEngine | None = None,
    ) -> None:
        self._config = config
        self._proxy = proxy
        self._rbac = rbac or RBACEngine(config)
        self._sql_engine = sql_engine or SQLSecurityEngine(config)

    def _context(self) -> RequestContext:
        return RequestContext.create(
            self._config.principal_id,
            self._config.role or "unmapped",
        )

    async def list_tools(self) -> list[Tool]:
        context = self._context()
        try:
            policy = await asyncio.to_thread(
                self._rbac.get_policy_for_principal, context.principal_id
            )
            tools = await self._proxy.list_allowed_tools()
            visible: list[Tool] = []
            for tool in tools:
                if tool.name not in ALLOWED_TOOLS:
                    continue
                cloned = tool.model_copy(deep=True)
                schema = dict(cloned.inputSchema)
                properties = dict(schema.get("properties", {}))
                properties.pop("role", None)
                schema["properties"] = properties
                cloned.inputSchema = schema
                visible.append(cloned)
            audit(
                request_id=context.request_id,
                principal_id=context.principal_id,
                role=policy.role_name,
                tool_name="tools/list",
                decision="ALLOW",
                reason_code="POLICY_APPLIED",
                policy_id=policy.policy_id,
            )
            return visible
        except GatewayError as exc:
            audit(
                request_id=context.request_id,
                principal_id=context.principal_id,
                role=context.role,
                tool_name="tools/list",
                decision="DENY",
                reason_code=exc.code,
            )
            raise
        except Exception:
            logger.exception("Tool discovery failed")
            audit(
                request_id=context.request_id,
                principal_id=context.principal_id,
                role=context.role,
                tool_name="tools/list",
                decision="ERROR",
                reason_code="TOOL_DISCOVERY_FAILURE",
            )
            raise

    async def call_tool(self, name: str, arguments: dict[str, Any]) -> CallToolResult:
        context = self._context()
        started_at = monotonic()
        logger.info(
            json.dumps(
                {
                    "event": "tool_call_started",
                    "request_id": context.request_id,
                    "principal_id": context.principal_id,
                    "tool_name": name,
                    "arguments": self._summarize_arguments(arguments),
                },
                ensure_ascii=False,
                separators=(",", ":"),
            )
        )
        query = arguments.get("query")
        policy: RolePolicy | None = None
        analysis = None
        try:
            if name not in ALLOWED_TOOLS:
                raise GatewayError("TOOL_NOT_ALLOWED", "Requested tool is not allowed")
            policy = await asyncio.to_thread(
                self._rbac.get_policy_for_principal, context.principal_id
            )
            forwarded = dict(arguments)
            if name == "execute_query_read_only":
                analysis = self._sql_engine.analyze(forwarded.get("query", ""), policy)
                forwarded["query"] = analysis.query
                if "role" in forwarded:
                    raise GatewayError("UNTRUSTED_ROLE_ARGUMENT", "Caller-supplied role is forbidden")
                forwarded["role"] = policy.role_name
                self._validate_export(forwarded, policy)
            elif name == "list_schemas":
                self._require_catalog(policy, forwarded.get("catalog"))
            elif name == "list_tables":
                self._require_catalog(policy, forwarded.get("catalog"))
                if not forwarded.get("schema"):
                    raise GatewayError("SCHEMA_REQUIRED", "A schema is required")
            elif name in {"describe_table", "show_create_table", "get_table_stats"}:
                self._validate_table_arguments(forwarded, policy)

            audit(
                request_id=context.request_id,
                principal_id=context.principal_id,
                role=policy.role_name,
                tool_name=name,
                decision="ALLOW",
                reason_code="POLICY_GRANTED",
                query=query if isinstance(query, str) else None,
                policy_id=policy.policy_id,
            )
            result = await self._proxy.call_tool(name, forwarded)
            if result.isError:
                audit(
                    request_id=context.request_id,
                    principal_id=context.principal_id,
                    role=policy.role_name,
                    tool_name=name,
                    decision="ERROR",
                    reason_code="UPSTREAM_TOOL_ERROR",
                    query=query if isinstance(query, str) else None,
                    policy_id=policy.policy_id,
                )
                self._log_tool_result(context.request_id, name, result, started_at)
                return result
            result = self._filter_metadata_result(
                name, forwarded, result, policy, analysis
            )
            self._log_tool_result(context.request_id, name, result, started_at)
            return result
        except GatewayError as exc:
            audit(
                request_id=context.request_id,
                principal_id=context.principal_id,
                role=policy.role_name if policy else context.role,
                tool_name=name,
                decision="DENY",
                reason_code=exc.code,
                query=query if isinstance(query, str) else None,
                policy_id=policy.policy_id if policy else None,
            )
            result = self._error_result(exc.code, exc.message)
            self._log_tool_result(context.request_id, name, result, started_at)
            return result
        except Exception:
            logger.exception("Upstream tool call failed")
            audit(
                request_id=context.request_id,
                principal_id=context.principal_id,
                role=policy.role_name if policy else context.role,
                tool_name=name,
                decision="ERROR",
                reason_code="UPSTREAM_FAILURE",
                query=query if isinstance(query, str) else None,
                policy_id=policy.policy_id if policy else None,
            )
            result = self._error_result(
                "UPSTREAM_FAILURE", "The upstream MCP request failed"
            )
            self._log_tool_result(context.request_id, name, result, started_at)
            return result

    @staticmethod
    def _summarize_arguments(arguments: dict[str, Any]) -> dict[str, Any]:
        summary: dict[str, Any] = {}
        query = arguments.get("query")
        if isinstance(query, str):
            summary["query_sha256"] = hashlib.sha256(
                query.encode("utf-8")
            ).hexdigest()
            summary["query_chars"] = len(query)
        for key in ("catalog", "schema", "table"):
            value = arguments.get(key)
            if isinstance(value, str):
                summary[key] = value[:128]
        if "output_file" in arguments:
            summary["output_file_requested"] = bool(arguments["output_file"])
        return summary

    def _log_tool_result(
        self,
        request_id: str,
        name: str,
        result: CallToolResult,
        started_at: float,
    ) -> None:
        text_content = [
            item.text for item in result.content if isinstance(item, TextContent)
        ]
        event: dict[str, Any] = {
            "event": "tool_call_completed",
            "request_id": request_id,
            "tool_name": name,
            "is_error": result.isError,
            "content_blocks": len(result.content),
            "text_chars": sum(len(text) for text in text_content),
            "duration_ms": round((monotonic() - started_at) * 1000),
        }
        if self._config.log_tool_results:
            combined_text = "\n".join(text_content)
            event["result_preview"] = combined_text[:2000]
            event["result_truncated"] = len(combined_text) > 2000
        logger.info(
            json.dumps(event, ensure_ascii=False, separators=(",", ":"))
        )

    @staticmethod
    def _error_result(code: str, message: str) -> CallToolResult:
        return CallToolResult(
            isError=True,
            content=[TextContent(type="text", text=f"{code}: {message}")],
        )

    @staticmethod
    def _require_catalog(policy: RolePolicy, catalog: Any) -> None:
        if not isinstance(catalog, str) or not catalog.strip():
            raise GatewayError("CATALOG_REQUIRED", "A catalog is required")
        if not policy.allows_catalog(catalog.strip()):
            raise GatewayError("CATALOG_ACCESS_DENIED", "Catalog access is not permitted")

    def _validate_table_arguments(
        self, arguments: dict[str, Any], policy: RolePolicy
    ) -> None:
        table_value = arguments.get("table")
        catalog = str(arguments.get("catalog") or "").strip()
        schema = str(arguments.get("schema") or "").strip()
        if not isinstance(table_value, str) or not table_value.strip():
            raise GatewayError("TABLE_REQUIRED", "A table is required")
        parts = table_value.strip().split(".")
        if len(parts) == 3:
            catalog, schema, table_value = parts
        elif len(parts) == 2:
            schema, table_value = parts
        if not catalog or not schema or not table_value:
            raise GatewayError(
                "QUALIFIED_TABLE_REQUIRED",
                "Provide catalog, schema, and table for metadata access",
            )
        qualified = f"{catalog}.{schema}.{table_value}".lower()
        self._require_catalog(policy, catalog)
        if not policy.allows_table(qualified):
            raise GatewayError("TABLE_ACCESS_DENIED", "Table access is not permitted")
        if (
            not policy.can_access_pii
            and table_value.lower() in self._config.pii_tables
        ):
            raise GatewayError("PII_ACCESS_DENIED", "PII access is not permitted")

    def _validate_export(
        self, arguments: dict[str, Any], policy: RolePolicy
    ) -> None:
        output_file = arguments.get("output_file")
        if output_file is None or output_file == "":
            return
        if not isinstance(output_file, str) or not policy.can_export_file:
            raise GatewayError("FILE_EXPORT_DENIED", "File export is not permitted")
        root = self._config.export_root
        candidate = Path(output_file)
        if not candidate.is_absolute():
            candidate = root / candidate
        resolved = candidate.resolve()
        if resolved == root or root not in resolved.parents:
            raise GatewayError("INVALID_EXPORT_PATH", "Export path must stay under the export directory")
        resolved.parent.mkdir(parents=True, exist_ok=True)
        arguments["output_file"] = str(resolved)

    def _filter_metadata_result(
        self,
        name: str,
        arguments: dict[str, Any],
        result: CallToolResult,
        policy: RolePolicy,
        analysis: SQLAnalysis | None = None,
    ) -> CallToolResult:
        metadata_kind = analysis.metadata_kind if analysis is not None else None
        if result.isError and name not in {"list_catalogs", "list_tables"}:
            return result
        if name not in {"list_catalogs", "list_tables"} and not metadata_kind:
            return result
        filtered_content = []
        for item in result.content:
            if not isinstance(item, TextContent):
                filtered_content.append(item)
                continue
            if metadata_kind:
                try:
                    rows = json.loads(item.text)
                except json.JSONDecodeError as exc:
                    raise GatewayError(
                        "INVALID_METADATA_RESPONSE",
                        "Upstream metadata could not be safely filtered",
                    ) from exc
                if not isinstance(rows, list) or not all(
                    isinstance(row, dict) for row in rows
                ):
                    raise GatewayError(
                        "INVALID_METADATA_RESPONSE",
                        "Upstream metadata had an unexpected format",
                    )
                if metadata_kind == "catalogs":
                    rows = [
                        row
                        for row in rows
                        if isinstance(row.get("Catalog"), str)
                        and policy.allows_catalog(row["Catalog"])
                    ]
                elif metadata_kind == "tables":
                    catalog = analysis.metadata_catalog
                    schema = analysis.metadata_schema
                    rows = [
                        row
                        for row in rows
                        if isinstance(row.get("Table"), str)
                        and GatewayService._table_visible(
                            policy,
                            f"{catalog}.{schema}.{row['Table']}",
                            self._config.pii_tables,
                        )
                    ]
                filtered_content.append(
                    TextContent(
                        type="text",
                        text=json.dumps(rows, ensure_ascii=False, indent=2),
                    )
                )
                continue
            values = item.text.splitlines()
            if name == "list_catalogs":
                values = [value for value in values if policy.allows_catalog(value.strip())]
            elif name == "list_tables":
                catalog = str(arguments["catalog"]).strip().lower()
                schema = str(arguments["schema"]).strip().lower()
                values = [
                    value
                    for value in values
                    if GatewayService._table_visible(
                        policy,
                        f"{catalog}.{schema}.{value.strip()}",
                        self._config.pii_tables,
                    )
                ]
            filtered_content.append(
                TextContent(type="text", text="\n".join(values))
            )
        return result.model_copy(update={"content": filtered_content})

    @staticmethod
    def _table_visible(
        policy: RolePolicy, table: str, pii_tables: frozenset[str]
    ) -> bool:
        table_name = table.rsplit(".", 1)[-1].lower()
        return policy.allows_table(table) and (
            policy.can_access_pii or table_name not in pii_tables
        )
