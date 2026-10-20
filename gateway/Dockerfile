FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /opt/secure-agentic-bi
COPY gateway/requirements.txt /tmp/requirements.txt
RUN pip install --no-cache-dir -r /tmp/requirements.txt

COPY gateway/app /opt/secure-agentic-bi/app
COPY trino-mcp/src/trino_mcp /opt/trino-mcp/src/trino_mcp
ENV PYTHONPATH=/opt/trino-mcp/src \
    MCP_SERVER_COMMAND=python \
    MCP_SERVER_ARGS_JSON="[\"-m\",\"trino_mcp\"]"

CMD ["python", "-m", "app"]
