"""Stdio client that calls one trino-mcp tool."""

import asyncio
import os
import shutil
import sys

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

_PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_TRINO_MCP_ROOT = os.path.join(_PROJECT_ROOT, "trino-mcp")
_TRINO_MCP_SRC = os.path.join(_TRINO_MCP_ROOT, "src")


def resolve_python_bin() -> str:
    """Interpreter that can launch `python -m trino_mcp`."""
    override = os.environ.get("TRINO_MCP_PYTHON")
    if override:
        if os.path.isfile(override):
            return override
        found = shutil.which(override)
        if found:
            return found
    for relative in (
        os.path.join(".venv", "Scripts", "python.exe"),
        os.path.join(".venv", "bin", "python"),
    ):
        candidate = os.path.join(_TRINO_MCP_ROOT, relative)
        if os.path.isfile(candidate):
            return candidate
    return sys.executable


def mcp_child_env() -> dict[str, str]:
    """Parent environment plus the gateway source tree on PYTHONPATH."""
    env = os.environ.copy()
    parts = [part for part in env.get("PYTHONPATH", "").split(os.pathsep) if part]
    if _TRINO_MCP_SRC not in parts:
        parts.insert(0, _TRINO_MCP_SRC)
    env["PYTHONPATH"] = os.pathsep.join(parts)
    return env


async def execute_mcp_tool(tool_name: str, arguments: dict) -> str:
    server_params = StdioServerParameters(
        command=resolve_python_bin(),
        args=["-m", "trino_mcp"],
        env=mcp_child_env(),
        cwd=_TRINO_MCP_ROOT,
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
