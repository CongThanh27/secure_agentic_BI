import json
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Mapping

from dotenv import load_dotenv


def _json_string_list(value: str, setting: str) -> list[str]:
    try:
        decoded = json.loads(value)
    except json.JSONDecodeError as exc:
        raise ValueError(f"{setting} must be valid JSON") from exc
    if not isinstance(decoded, list) or not all(isinstance(item, str) for item in decoded):
        raise ValueError(f"{setting} must be a JSON array of strings")
    return decoded


def _principal_roles(value: str) -> dict[str, str]:
    try:
        decoded = json.loads(value)
    except json.JSONDecodeError as exc:
        raise ValueError("GATEWAY_PRINCIPAL_ROLES_JSON must be valid JSON") from exc
    if not isinstance(decoded, dict) or not all(
        isinstance(principal, str)
        and principal
        and isinstance(role, str)
        and role
        for principal, role in decoded.items()
    ):
        raise ValueError("GATEWAY_PRINCIPAL_ROLES_JSON must map non-empty strings to roles")
    return decoded


@dataclass(frozen=True)
class Settings:
    principal_id: str
    principal_roles: Mapping[str, str]
    mysql_host: str
    mysql_port: int
    mysql_database: str
    mysql_user: str
    mysql_password: str
    mcp_server_command: str
    mcp_server_args: list[str]
    mcp_server_cwd: Path
    mcp_timeout_seconds: float
    export_root: Path
    pii_tables: frozenset[str]
    log_level: str
    gateway_host: str = "127.0.0.1"
    gateway_port: int = 8000
    log_tool_results: bool = False

    @property
    def role(self) -> str | None:
        return self.principal_roles.get(self.principal_id)


def load_settings() -> Settings:
    load_dotenv()
    repository_root = Path(__file__).resolve().parents[2]
    principal_id = os.getenv("GATEWAY_PRINCIPAL_ID", "").strip()
    pii_tables = frozenset(
        item.strip().lower()
        for item in os.getenv(
            "GATEWAY_PII_TABLES", "customers,employees,customer_profiles"
        ).split(",")
        if item.strip()
    )
    return Settings(
        principal_id=principal_id,
        principal_roles=_principal_roles(
            os.getenv("GATEWAY_PRINCIPAL_ROLES_JSON", "{}")
        ),
        mysql_host=os.getenv("MYSQL_HOST", "127.0.0.1"),
        mysql_port=int(os.getenv("MYSQL_PORT", "13306")),
        mysql_database=os.getenv("MYSQL_DATABASE", "agentic_bi"),
        mysql_user=os.getenv("MYSQL_USER", "bi_agent"),
        mysql_password=os.getenv("MYSQL_PASSWORD", ""),
        mcp_server_command=os.getenv("MCP_SERVER_COMMAND", "").strip(),
        mcp_server_args=_json_string_list(
            os.getenv("MCP_SERVER_ARGS_JSON", "[]"), "MCP_SERVER_ARGS_JSON"
        ),
        mcp_server_cwd=Path(
            os.getenv("MCP_SERVER_CWD", str(repository_root / "trino-mcp"))
        ).resolve(),
        mcp_timeout_seconds=float(os.getenv("MCP_TIMEOUT_SECONDS", "30")),
        export_root=Path(os.getenv("GATEWAY_EXPORT_ROOT", "./exports")).resolve(),
        pii_tables=pii_tables,
        log_level=os.getenv("LOG_LEVEL", "INFO").upper(),
        gateway_host=os.getenv("GATEWAY_HOST", "127.0.0.1"),
        gateway_port=int(os.getenv("GATEWAY_PORT", "8000")),
        log_tool_results=os.getenv("GATEWAY_LOG_TOOL_RESULTS", "").lower()
        in {"1", "true", "yes"},
    )


settings = load_settings()
