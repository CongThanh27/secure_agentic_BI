import logging
from dataclasses import replace
from pathlib import Path

import pytest
from mcp.types import CallToolResult, TextContent, Tool

from app.config import Settings
from app.services.gateway import GatewayService
from app.services.rbac_engine import policy_from_row


class FakeRBAC:
    def get_policy_for_principal(self, principal_id):
        assert principal_id == "test-agent"
        return policy_from_row(
            {
                "id": 1,
                "role_name": "analyst",
                "allowed_catalogs": "pg",
                "allowed_tables": "pg.public.orders",
                "denied_tables": "pg.public.hr_payroll",
                "can_export_file": 0,
                "max_row_limit": 10,
                "can_execute_ddl": 0,
                "can_access_pii": 0,
            }
        )


class FakeProxy:
    def __init__(self):
        self.calls = []
        self.result_text = "ok"

    async def call_tool(self, name, arguments):
        self.calls.append((name, arguments))
        return CallToolResult(
            isError=False,
            content=[TextContent(type="text", text=self.result_text)],
        )

    async def list_allowed_tools(self):
        return [
            Tool(
                name="execute_query_read_only",
                description="Read-only query",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "query": {"type": "string"},
                        "role": {"type": "string"},
                    },
                },
            ),
            Tool(
                name="execute_query",
                description="Write query",
                inputSchema={"type": "object", "properties": {}},
            ),
        ]


@pytest.fixture
def service(tmp_path):
    config = Settings(
        principal_id="test-agent",
        principal_roles={"test-agent": "analyst"},
        mysql_host="localhost",
        mysql_port=3306,
        mysql_database="agentic_bi",
        mysql_user="",
        mysql_password="",
        mcp_server_command="",
        mcp_server_args=[],
        mcp_server_cwd=Path("/tmp/trino-mcp"),
        mcp_timeout_seconds=30,
        export_root=Path(tmp_path),
        pii_tables=frozenset({"customers", "employees"}),
        log_level="INFO",
    )
    proxy = FakeProxy()
    return GatewayService(config, proxy, rbac=FakeRBAC()), proxy


@pytest.mark.asyncio
async def test_denied_query_never_reaches_upstream(service) -> None:
    gateway, proxy = service

    result = await gateway.call_tool(
        "execute_query_read_only",
        {"query": "SELECT * FROM pg.public.hr_payroll"},
    )

    assert result.isError
    assert proxy.calls == []


@pytest.mark.asyncio
async def test_allowed_query_uses_trusted_role_and_policy_limit(service) -> None:
    gateway, proxy = service

    result = await gateway.call_tool(
        "execute_query_read_only",
        {"query": "SELECT * FROM pg.public.orders"},
    )

    assert not result.isError
    assert proxy.calls[0][1]["role"] == "analyst"
    assert "LIMIT 10" in proxy.calls[0][1]["query"].upper()


@pytest.mark.asyncio
async def test_caller_cannot_select_role(service) -> None:
    gateway, proxy = service

    result = await gateway.call_tool(
        "execute_query_read_only",
        {"query": "SELECT * FROM pg.public.orders", "role": "admin"},
    )

    assert result.isError
    assert proxy.calls == []


@pytest.mark.asyncio
async def test_show_tables_filters_denied_tables(service) -> None:
    gateway, proxy = service
    proxy.result_text = '[\n  {"Table": "orders"},\n  {"Table": "hr_payroll"}\n]'

    result = await gateway.call_tool(
        "execute_query_read_only",
        {"query": "SHOW TABLES FROM pg.public"},
    )

    assert not result.isError
    assert '"Table": "orders"' in result.content[0].text
    assert "hr_payroll" not in result.content[0].text


@pytest.mark.asyncio
async def test_tool_discovery_hides_write_tool_and_trusted_role(service) -> None:
    gateway, _ = service

    tools = await gateway.list_tools()

    assert [tool.name for tool in tools] == ["execute_query_read_only"]
    assert "role" not in tools[0].inputSchema["properties"]


@pytest.mark.asyncio
async def test_tool_call_logs_result_summary_without_result_data(
    service, caplog
) -> None:
    gateway, _ = service

    with caplog.at_level(logging.INFO, logger="secure_gateway"):
        await gateway.call_tool(
            "execute_query_read_only",
            {"query": "SELECT * FROM pg.public.orders"},
        )

    assert '"event":"tool_call_started"' in caplog.text
    assert '"event":"tool_call_completed"' in caplog.text
    assert '"tool_name":"execute_query_read_only"' in caplog.text
    assert '"text_chars":2' in caplog.text
    assert '"result_preview"' not in caplog.text


@pytest.mark.asyncio
async def test_tool_call_can_log_result_preview_when_enabled(
    service, caplog
) -> None:
    gateway, _ = service
    gateway._config = replace(gateway._config, log_tool_results=True)

    with caplog.at_level(logging.INFO, logger="secure_gateway"):
        await gateway.call_tool(
            "execute_query_read_only",
            {"query": "SELECT * FROM pg.public.orders"},
        )

    assert '"result_preview":"ok"' in caplog.text
