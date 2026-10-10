#!/bin/bash
echo "🛑 Đang tắt toàn bộ cụm Database..."
docker compose down
echo "🧹 Đã tắt an toàn và giải phóng RAM!"
# ./stop.sh