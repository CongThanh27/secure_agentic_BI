import asyncio
import json
import logging
import re
import time
from collections.abc import Mapping
from pathlib import Path
from typing import Any

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

from app.core.config import settings

logger = logging.getLogger(__name__)


class MCPQueryTimeoutError(RuntimeError):
    """Raised when a Trino query exceeds the caller's circuit-breaker timeout."""

    def __init__(self, message: str, elapsed_seconds: float = 0.0) -> None:
        super().__init__(message)
        self.elapsed_seconds = elapsed_seconds


METADATA_QUERY_TEMPLATE = """
SELECT
    table_cat AS table_catalog,
    table_schem AS table_schema,
    table_name,
    column_name,
    type_name AS data_type
FROM system.jdbc.columns
WHERE table_schem != 'information_schema'
ORDER BY table_cat, table_schem, table_name, ordinal_position
""".strip()

_CATALOG_IDENTIFIER = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*$")


def _parse_tool_result(result: Any, result_description: str) -> Any:
    """Convert a Trino MCP JSON text result into a Python value."""
    text_parts = [
        content.text
        for content in getattr(result, "content", [])
        if hasattr(content, "text")
    ]
    if getattr(result, "isError", False):
        detail = "\n".join(text_parts).strip()
        raise RuntimeError(
            f"Trino MCP {result_description} failed"
            + (f": {detail}" if detail else "")
        )
    if not text_parts:
        raise RuntimeError(f"Trino MCP returned an empty {result_description} response")

    response_text = "\n".join(text_parts).strip()
    if response_text.lower().startswith("error"):
        raise RuntimeError(
            f"Trino MCP {result_description} query failed: {response_text}"
        )

    try:
        payload: Any = json.loads(response_text)
    except json.JSONDecodeError as exc:
        logger.error("Trino MCP returned non-JSON metadata: %s", response_text)
        raise RuntimeError(
            f"Trino MCP returned an invalid {result_description} response"
        ) from exc
    return payload


def _parse_schema_result(result: Any) -> list[dict[str, str]]:
    payload = _parse_tool_result(result, "metadata")
    if not isinstance(payload, list):
        raise RuntimeError("Trino MCP metadata response must be a JSON list")

    schema: list[dict[str, str]] = []
    required_keys = (
        "table_catalog",
        "table_schema",
        "table_name",
        "column_name",
        "data_type",
    )
    for row in payload:
        if not isinstance(row, Mapping) or not all(
            isinstance(row.get(key), str) and row[key].strip()
            for key in required_keys
        ):
            raise RuntimeError("Trino MCP returned an invalid metadata row")
        schema.append({key: row[key].strip() for key in required_keys})
    return schema


async def fetch_trino_schema(
    catalogs: list[str], timeout_seconds: float = 15.0
) -> list[dict[str, str]]:
    """Fetch table metadata from the Trino MCP server over stdio."""
    normalized_catalogs = [
        item.strip()
        for value in catalogs
        for item in value.split(",")
        if item.strip()
    ]
    if not normalized_catalogs:
        raise ValueError("At least one catalog is required for metadata discovery")
    invalid_catalogs = [
        catalog
        for catalog in normalized_catalogs
        if not _CATALOG_IDENTIFIER.fullmatch(catalog)
    ]
    if invalid_catalogs:
        raise ValueError("Invalid Trino catalog identifier")

    server = StdioServerParameters(
        command=settings.python_bin_path,
        args=["-m", "trino_mcp.server"],
        cwd=Path(settings.trino_mcp_dir) if settings.trino_mcp_dir else None,
    )

    async def call_mcp() -> list[dict[str, str]]:
        async with stdio_client(server) as (read_stream, write_stream):
            async with ClientSession(read_stream, write_stream) as session:
                await session.initialize()
                result = await session.call_tool(
                    "execute_query_read_only",
                    {"query": METADATA_QUERY_TEMPLATE},
                    read_timeout_seconds=timeout_seconds,
                )
                schema = _parse_schema_result(result)
                allowed_catalogs = {catalog.lower() for catalog in normalized_catalogs}
                return [
                    row
                    for row in schema
                    if row["table_catalog"].lower() in allowed_catalogs
                ]

    try:
        return await asyncio.wait_for(call_mcp(), timeout=timeout_seconds)
    except asyncio.TimeoutError:
        logger.error("Trino MCP metadata discovery timed out")
        raise RuntimeError("Trino MCP metadata discovery timed out") from None
    except (OSError, RuntimeError, ValueError):
        logger.exception("Trino MCP metadata discovery failed")
        raise


async def execute_trino_query(
    query: str, timeout_seconds: float = 10.0
) -> Any:
    """Execute one read-only SQL query through Trino MCP with a hard timeout."""
    server = StdioServerParameters(
        command=settings.python_bin_path,
        args=["-m", "trino_mcp.server"],
        cwd=Path(settings.trino_mcp_dir) if settings.trino_mcp_dir else None,
    )

    async def call_mcp() -> Any:
        async with stdio_client(server) as (read_stream, write_stream):
            async with ClientSession(read_stream, write_stream) as session:
                await session.initialize()
                result = await session.call_tool(
                    "execute_query_read_only",
                    {"query": query},
                    read_timeout_seconds=timeout_seconds,
                )
                return _parse_tool_result(result, "query")

    try:
        return await asyncio.wait_for(call_mcp(), timeout=timeout_seconds)
    except asyncio.TimeoutError:
        logger.error("Trino MCP query timed out")
        raise MCPQueryTimeoutError("Trino query timed out") from None
    except (OSError, RuntimeError, ValueError):
        logger.exception("Trino MCP query execution failed")
        raise


async def execute_sql_with_timeout(
    sql: str, timeout_seconds: float
) -> tuple[Any, float]:
    """Execute SQL through MCP and return raw data plus DB execution time."""
    if timeout_seconds <= 0:
        raise ValueError("timeout_seconds must be greater than zero")

    started_at = time.perf_counter()
    try:
        raw_data = await asyncio.wait_for(
            execute_trino_query(sql, timeout_seconds=timeout_seconds),
            timeout=timeout_seconds,
        )
    except (MCPQueryTimeoutError, asyncio.TimeoutError) as exc:
        elapsed = time.perf_counter() - started_at
        logger.warning(
            "Circuit breaker stopped Trino query after %.3f seconds",
            elapsed,
        )
        raise MCPQueryTimeoutError(
            f"Trino query exceeded timeout of {timeout_seconds:.3f} seconds",
            elapsed_seconds=elapsed,
        ) from exc
    elapsed = time.perf_counter() - started_at
    return raw_data, elapsed
