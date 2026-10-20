# Secure MCP Gateway

Gateway implements an MCP stdio server and starts the existing `trino-mcp`
server as its upstream MCP client. It does not modify the upstream repository.
The Gateway fails closed if the trusted principal has no configured role or
the MySQL policy source is unavailable.

## Configure and run locally

The repository's Docker Compose stack provides MySQL on host port `13306`.
Ensure the `agent_role_permissions` table is initialized, then create a local
environment file and set the upstream server command:

```bash
cd gateway
cp .env.example .env
# Set MYSQL_PASSWORD to the existing MySQL credential.
uv run --with-requirements requirements.txt python -m app
```

`GATEWAY_PRINCIPAL_ID` and `GATEWAY_PRINCIPAL_ROLES_JSON` are trusted
server-side configuration. Do not accept the principal or role from tool
arguments or an unverified client header. For another principal, map that
principal to a role in the JSON object and launch a separately configured MCP
server process.

The default starts `python -m trino_mcp` directly from the existing
`trino-mcp/src` checkout (with the upstream directory as its working directory).
This avoids building/installing the upstream editable package and lets that
process load its own `trino-mcp/.env`. If your checkout is elsewhere, set
`MCP_SERVER_CWD` to its absolute path. Change `MCP_SERVER_COMMAND` and
`MCP_SERVER_ARGS_JSON` only when using another trusted MCP stdio command. The
MySQL user should have read-only access to `agent_role_permissions`; never
expose its credentials to the Agent.

### Connect from VS Code over SSE

Start the Gateway as an HTTP/SSE service from the `gateway` directory:

```bash
uv run --with-requirements requirements.txt python -m app
```

Set `GATEWAY_HOST` and `GATEWAY_PORT` in `gateway/.env` if needed. The defaults
are `127.0.0.1:8000`; the MCP SSE endpoint is
`http://localhost:8000/sse`. Open the repository root folder in VS Code, where
`.vscode/mcp.json` connects to that endpoint, and restart
`secure-agentic-bi-gateway` after starting the service. In Copilot Chat, enable
the server's tools from the tool picker.

The default loopback bind keeps this trusted-principal gateway local to the
machine. Only set `GATEWAY_HOST=0.0.0.0` when access from outside the host is
needed and separately protected by an authenticated, trusted network layer.

Tool calls are logged with the tool name, a query hash (not SQL text), result
status, text length, and duration. To also log up to 2,000 characters of each
tool result, set `GATEWAY_LOG_TOOL_RESULTS=true` in `gateway/.env`. Tool output
may contain sensitive data, so this option is disabled by default.

Do not also enable a direct `trino-mcp` server for the same agent: connecting
to upstream directly bypasses the Gateway's policy checks.

## Security behavior

- Discovery and execution expose only read-only tools from the fixed Gateway
  allowlist. The upstream `execute_query` write-capable tool is never exposed
  or forwarded.
- Every discovery and tool call loads the latest role policy from
  `agent_role_permissions`. Missing policy or database errors fail closed.
- Read queries are parsed with the Trino SQL dialect. Invalid SQL, multiple
  statements, writes, DDL, `CROSS JOIN`, unqualified tables, unauthorized
  catalogs/tables, and restricted PII tables are denied.
- Query row limits are inserted or capped at the role's `max_row_limit`.
- Table and catalog metadata calls are checked at execution time, and list
  results are filtered to the role's permitted scope.
- File exports require `can_export_file` and are confined to
  `GATEWAY_EXPORT_ROOT`.
- Structured audit records go to stderr and contain a SHA-256 query hash
  rather than SQL text.

The role policy table has no principal column. The trusted
`GATEWAY_PRINCIPAL_ROLES_JSON` mapping binds the configured process principal
to the role whose policy is read from MySQL. Each Gateway process has a single
trusted identity, so use one process per principal.

## Tests

```bash
uv run --with-requirements requirements.txt pytest -q
```

Build the image from the repository root with:

```bash
docker build -f gateway/Dockerfile -t secure-agentic-bi-gateway .
```
