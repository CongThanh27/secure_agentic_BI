import asyncio

from mcp.server import Server
from app.main import create_sse_app


def test_sse_app_returns_not_found_for_unknown_routes() -> None:
    app = create_sse_app(Server("test-gateway"))
    sent = []

    async def receive():
        return {"type": "http.request", "body": b"", "more_body": False}

    async def send(message):
        sent.append(message)

    asyncio.run(
        app(
            {
                "type": "http",
                "asgi": {"version": "3.0"},
                "http_version": "1.1",
                "method": "GET",
                "scheme": "http",
                "path": "/unknown",
                "raw_path": b"/unknown",
                "query_string": b"",
                "headers": [],
                "client": ("127.0.0.1", 1234),
                "server": ("127.0.0.1", 8000),
            },
            receive,
            send,
        )
    )

    assert sent[0]["status"] == 404


def test_sse_disconnect_does_not_send_a_second_http_response() -> None:
    class FakeServer:
        @staticmethod
        def create_initialization_options():
            return None

        @staticmethod
        async def run(read_stream, write_stream, options):
            return None

    app = create_sse_app(FakeServer())
    sent = []
    receive_count = 0

    async def receive():
        nonlocal receive_count
        receive_count += 1
        if receive_count == 1:
            return {"type": "http.request", "body": b"", "more_body": False}
        await asyncio.sleep(0.05)
        return {"type": "http.disconnect"}

    async def send(message):
        sent.append(message)

    asyncio.run(
        app(
            {
                "type": "http",
                "asgi": {"version": "3.0"},
                "http_version": "1.1",
                "method": "GET",
                "scheme": "http",
                "path": "/sse",
                "raw_path": b"/sse",
                "query_string": b"",
                "headers": [
                    (b"host", b"localhost:8000"),
                    (b"accept", b"text/event-stream"),
                ],
                "client": ("127.0.0.1", 1234),
                "server": ("127.0.0.1", 8000),
            },
            receive,
            send,
        )
    )

    response_starts = [
        message for message in sent if message["type"] == "http.response.start"
    ]
    assert len(response_starts) == 1
    assert response_starts[0]["status"] == 200


def test_sse_app_supports_asgi_lifespan() -> None:
    app = create_sse_app(Server("test-gateway"))
    sent = []
    messages = iter(
        [
            {"type": "lifespan.startup"},
            {"type": "lifespan.shutdown"},
        ]
    )

    async def receive():
        return next(messages)

    async def send(message):
        sent.append(message)

    asyncio.run(
        app(
            {"type": "lifespan", "asgi": {"version": "3.0"}},
            receive,
            send,
        )
    )

    assert [message["type"] for message in sent] == [
        "lifespan.startup.complete",
        "lifespan.shutdown.complete",
    ]
