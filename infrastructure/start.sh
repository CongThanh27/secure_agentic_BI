#!/bin/bash
cd "$(dirname "$0")" || exit 1
echo "🚀 Đang khởi động Trino và PostgreSQL..."
docker compose up -d
echo "✅ Hệ thống Database đã chạy nền thành công!"
echo "👉 Tiếp theo: Mở Cursor -> Customize -> MCPs -> Bật (Enable) trino-local-proxy."
# ./start.sh

# cd /Users/nguyenthanh/Master/NewGenerationSoftwareEngineering/pro/pro/secure_agentic_BI/backend_api
# source .venv/bin/activate
# uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# cd /Users/nguyenthanh/Master/NewGenerationSoftwareEngineering/pro/pro/secure_agentic_BI/frontend
# npm run dev