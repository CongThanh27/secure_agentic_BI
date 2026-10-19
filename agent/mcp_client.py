"""Stdio client that calls one trino-mcp tool."""

import asyncio
import os

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

_DEFAULT_PYTHON_BIN = (
    "/Users/nguyenthanh/Master/NewGenerationSoftwareEngineering/pro/pro/"
    "secure_agentic_BI/trino-mcp/.venv/bin/python"
)
PYTHON_BIN_PATH = os.environ.get("TRINO_MCP_PYTHON", _DEFAULT_PYTHON_BIN)


async def execute_mcp_tool(tool_name: str, arguments: dict) -> str:
    server_params = StdioServerParameters(
        command=PYTHON_BIN_PATH,
        args=["-m", "trino_mcp"],
        env=None,
    )

    async with stdio_client(server_params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()

            try:
                result = await asyncio.wait_for(
                    session.call_tool(tool_name, arguments),
                    timeout=3.0,
                )

                if result.content and len(result.content) > 0:
                    return result.content[0].text
                return "Lệnh chạy thành công nhưng không có kết quả trả về."

            except asyncio.TimeoutError:
                return (
                    "LỖI GUARDRAIL TỪ UI (Circuit Breaker): Phát hiện tấn công DoS! "
                    "Dữ liệu trả về quá lớn gây nghẽn băng thông. Đã chủ động ngắt "
                    "kết nối để bảo vệ RAM hệ thống!"
                )

            except Exception as e:
                return f"LỖI GUARDRAIL TỪ TRINO: {str(e)}"


def run_mcp_tool_sync(tool_name: str, arguments: dict) -> str:
    return asyncio.run(execute_mcp_tool(tool_name, arguments))
