#!/bin/bash
# ==============================================================================
# Secure Agentic BI Framework - Root Startup Script
# ==============================================================================
set -e

PROJECT_ROOT="$(cd "$(dirname "$0")" && pwd)"

echo "🚀 [1/3] Khởi động cụm CSDL phân tán (PostgreSQL, MySQL, Trino Coordinator)..."
cd "$PROJECT_ROOT/infrastructure" || exit 1
./start.sh

echo ""
echo "================================================================================"
echo "✅ Cụm Database (Docker) đã khởi động thành công!"
echo "   - Trino Coordinator : http://localhost:8080"
echo "   - PostgreSQL (pg)   : localhost:5432 (DB: analytics_db)"
echo "   - MySQL (mysql)     : localhost:13306 (DB: agentic_bi)"
echo "================================================================================"
echo "👉 Hướng dẫn chạy tiếp các dịch vụ ứng dụng:"
echo "   1. Khởi động Backend API (Terminal 1):"
echo "      cd backend_api"
echo "      source .venv/bin/activate"
echo "      uvicorn app.main:app --reload --host 0.0.0.0 --port 8000"
echo ""
echo "   2. Khởi động Frontend Console (Terminal 2):"
echo "      cd frontend"
echo "      npm run dev"
echo "================================================================================"
