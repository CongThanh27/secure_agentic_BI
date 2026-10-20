import asyncio
import logging
import sys

import uvicorn
from mcp.server import Server
from mcp.server.sse import SseServerTransport
from mcp.types import CallToolResult, Tool
from starlette.applications import Starlette
from starlette.types import ASGIApp, Receive, Scope, Send

from app.config import settings
from app.services.gateway import GatewayService
from app.services.proxy_client import MCPProxyClient


def configure_logging() -> None:
    logging.basicConfig(
        level=settings.log_level,
        stream=sys.stderr,
        format="%(asctime)s %(levelname)s %(name)s %(message)s",
    )
    audit_logger = logging.getLogger("secure_gateway.audit")
    audit_logger.handlers.clear()
    audit_handler = logging.StreamHandler(sys.stderr)
    audit_handler.setFormatter(logging.Formatter("%(message)s"))
    audit_logger.addHandler(audit_handler)
    audit_logger.setLevel(settings.log_level)
    audit_logger.propagate = False


def create_mcp_server(gateway: GatewayService) -> Server:
    server = Server("secure-agentic-bi-gateway")

    @server.list_tools()
    async def list_tools() -> list[Tool]:
        return await gateway.list_tools()

    @server.call_tool()
    async def call_tool(name: str, arguments: dict) -> CallToolResult:
        return await gateway.call_tool(name, arguments)

    return server


def create_sse_app(server: Server) -> ASGIApp:
    transport = SseServerTransport("/messages/")
    fallback_app = Starlette()

    async def app(scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] == "http":
            path = scope["path"]
            method = scope["method"]
            if path == "/sse" and method == "GET":
                async with transport.connect_sse(scope, receive, send) as (
                    read_stream,
                    write_stream,
                ):
                    await server.run(
                        read_stream,
                        write_stream,
                        server.create_initialization_options(),
                    )
                return
            if path.startswith("/messages/") and method == "POST":
                await transport.handle_post_message(scope, receive, send)
                return

        await fallback_app(scope, receive, send)

    return app


async def run() -> None:
    configure_logging()
    proxy = MCPProxyClient(settings)
    try:
        await proxy.connect()
        gateway = GatewayService(settings, proxy)
        server = create_mcp_server(gateway)
        app = create_sse_app(server)
        config = uvicorn.Config(
            app,
            host=settings.gateway_host,
            port=settings.gateway_port,
            log_level=settings.log_level.lower(),
        )
        await uvicorn.Server(config).serve()
    finally:
        await proxy.close()


def main() -> None:
    asyncio.run(run())


if __name__ == "__main__":
    main()
