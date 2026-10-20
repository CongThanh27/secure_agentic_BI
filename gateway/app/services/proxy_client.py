import asyncio
import os
from contextlib import AsyncExitStack
from typing import Any

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
from mcp.types import CallToolResult, Tool

from app.config import Settings
from app.core.exceptions import GatewayError


ALLOWED_TOOLS = frozenset(
    {
        "list_catalogs",
        "list_schemas",
        "list_tables",
        "describe_table",
        "execute_query_read_only",
        "show_create_table",
        "get_table_stats",
    }
)


class MCPProxyClient:
    def __init__(self, config: Settings) -> None:
        self._config = config
        self._stack = AsyncExitStack()
        self._session: ClientSession | None = None

    async def connect(self) -> None:
        if not self._config.mcp_server_command:
            raise RuntimeError("MCP_SERVER_COMMAND must configure the upstream MCP server")
        source_path = self._config.mcp_server_cwd / "src"
        child_env = os.environ.copy()
        inherited_pythonpath = child_env.get("PYTHONPATH")
        child_env["PYTHONPATH"] = os.pathsep.join(
            part
            for part in (str(source_path), inherited_pythonpath)
            if part
        )
        parameters = StdioServerParameters(
            command=self._config.mcp_server_command,
            args=self._config.mcp_server_args,
            env=child_env,
            cwd=self._config.mcp_server_cwd,
        )
        read_stream, write_stream = await asyncio.wait_for(
            self._stack.enter_async_context(stdio_client(parameters)),
            timeout=self._config.mcp_timeout_seconds,
        )
        self._session = await self._stack.enter_async_context(
            ClientSession(read_stream, write_stream)
        )
        await asyncio.wait_for(
            self._session.initialize(),
            timeout=self._config.mcp_timeout_seconds,
        )

    async def list_allowed_tools(self) -> list[Tool]:
        session = self._require_session()
        upstream = await asyncio.wait_for(
            session.list_tools(),
            timeout=self._config.mcp_timeout_seconds,
        )
        return [tool for tool in upstream.tools if tool.name in ALLOWED_TOOLS]

    async def call_tool(self, name: str, arguments: dict[str, Any]) -> CallToolResult:
        if name not in ALLOWED_TOOLS:
            raise GatewayError("TOOL_NOT_ALLOWED", "Requested tool is not allowed")
        result = await asyncio.wait_for(
            self._require_session().call_tool(name, arguments=arguments),
            timeout=self._config.mcp_timeout_seconds,
        )
        return result

    def _require_session(self) -> ClientSession:
        if self._session is None:
            raise RuntimeError("Upstream MCP client is not connected")
        return self._session

    async def close(self) -> None:
        await self._stack.aclose()
        self._session = None
