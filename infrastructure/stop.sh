#!/bin/bash
cd "$(dirname "$0")" || exit 1
echo "🛑 Đang tắt toàn bộ cụm Database..."
docker compose down -v
echo "🧹 Đã tắt an toàn và giải phóng RAM!"
# ./stop.sh

