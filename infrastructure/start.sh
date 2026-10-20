#!/bin/bash
cd "$(dirname "$0")" || exit 1
echo "🚀 Đang khởi động Trino và PostgreSQL..."
docker compose up -d
echo "✅ Hệ thống Database đã chạy nền thành công!"
echo "👉 Tiếp theo: Mở Cursor -> Customize -> MCPs -> Bật (Enable) trino-local-proxy."
# ./start.sh