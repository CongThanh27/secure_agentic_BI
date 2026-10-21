"""The MCP child must be a Python that exists on this machine."""

import os
import subprocess

from agent.mcp_client import _TRINO_MCP_SRC, mcp_child_env, resolve_python_bin


def test_resolve_python_bin_uses_local_venv(monkeypatch):
    monkeypatch.delenv("TRINO_MCP_PYTHON", raising=False)
    path = resolve_python_bin()
    assert os.path.isfile(path)
    assert "trino-mcp" in path.replace("\\", "/")


def test_missing_override_falls_back_to_venv(monkeypatch):
    monkeypatch.setenv("TRINO_MCP_PYTHON", r"C:\missing\python.exe")
    path = resolve_python_bin()
    assert os.path.isfile(path)


def test_child_env_includes_gateway_source():
    assert _TRINO_MCP_SRC in mcp_child_env()["PYTHONPATH"].split(os.pathsep)


def test_resolved_python_can_import_gateway():
    completed = subprocess.run(
        [resolve_python_bin(), "-c", "import trino_mcp"],
        env=mcp_child_env(),
        capture_output=True,
        text=True,
        timeout=30,
        check=False,
    )
    assert completed.returncode == 0, completed.stderr
