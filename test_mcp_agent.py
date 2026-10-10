#!/usr/bin/env python3
"""
MCP Client Script — Data Analyst Agent Test
Giao tiếp với trino-mcp server qua MCP SDK (stdio transport).
"""
import asyncio
import json
import sys
import os

# Đảm bảo chạy từ thư mục trino-mcp để load_dotenv() đọc đúng .env
os.chdir(os.path.join(os.path.dirname(os.path.abspath(__file__)), "trino-mcp"))

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client


async def call_tool(session: ClientSession, tool_name: str, arguments: dict) -> str:
    """Gọi một MCP tool và trả về text content."""
    print(f"\n{'='*60}")
    print(f"🔧 Calling MCP Tool: {tool_name}")
    print(f"   Arguments: {json.dumps(arguments, ensure_ascii=False)}")
    print(f"{'='*60}")

    result = await session.call_tool(tool_name, arguments=arguments)

    # Trích xuất text từ result
    texts = []
    for content in result.content:
        if hasattr(content, 'text'):
            texts.append(content.text)
    output = "\n".join(texts)
    print(f"📋 Result:\n{output}")
    return output


async def main():
    # Cấu hình server parameters — chạy trino-mcp qua .venv python
    server_params = StdioServerParameters(
        command=sys.executable,  # Python hiện tại (trong .venv)
        args=["-m", "trino_mcp"],
        cwd=os.getcwd(),  # trino-mcp/
    )

    print("🚀 Starting MCP Server (trino-mcp) via stdio transport...")
    print(f"   CWD: {os.getcwd()}")
    print(f"   Python: {sys.executable}")

    async with stdio_client(server_params) as (read, write):
        async with ClientSession(read, write) as session:
            # Khởi tạo session
            await session.initialize()
            print("\n✅ MCP Session initialized successfully!")

            # ============================================
            # STEP 1: list_tables — Liệt kê bảng
            # ============================================
            print("\n" + "🔹"*30)
            print("STEP 1a: Liệt kê các bảng trong pg.public")
            print("🔹"*30)

            await call_tool(session, "list_tables", {
                "catalog": "pg",
                "schema": "public",
            })

            # ============================================
            # STEP 1b: describe_table — Cấu trúc orders
            # ============================================
            print("\n" + "🔹"*30)
            print("STEP 1b: Mô tả cấu trúc bảng orders")
            print("🔹"*30)

            await call_tool(session, "describe_table", {
                "table": "orders",
                "catalog": "pg",
                "schema": "public",
            })

            # ============================================
            # STEP 2+3: execute_query_read_only → CSV file
            # ============================================
            print("\n" + "🔹"*30)
            print("STEP 2+3: Query doanh thu → ghi ra temp_revenue.csv")
            print("🔹"*30)

            # output_file path tuyệt đối trỏ về workspace root
            workspace = os.path.dirname(os.getcwd())  # secure_agentic_BI/
            output_path = os.path.join(workspace, "temp_revenue.csv")

            await call_tool(session, "execute_query_read_only", {
                "query": """
                    SELECT
                        product_name,
                        SUM(amount) AS total_revenue
                    FROM pg.public.orders
                    GROUP BY product_name
                    ORDER BY total_revenue DESC
                """,
                "output_file": output_path,
            })

            # Xác minh file đã tạo
            print("\n" + "🔹"*30)
            print("VERIFICATION: Nội dung file temp_revenue.csv")
            print("🔹"*30)
            if os.path.exists(output_path):
                with open(output_path, "r") as f:
                    content = f.read()
                print(f"📄 File: {output_path}")
                print(f"📦 Size: {os.path.getsize(output_path)} bytes")
                print(f"📋 Content:\n{content}")
            else:
                print(f"❌ File not found: {output_path}")

    print("\n✅ All MCP tool calls completed successfully!")


if __name__ == "__main__":
    asyncio.run(main())
