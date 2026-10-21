#!/bin/bash
# ==============================================================================
# Secure Agentic BI Framework - Root Shutdown Script
# ==============================================================================
set -e

PROJECT_ROOT="$(cd "$(dirname "$0")" && pwd)"

echo "🛑 Đang tắt cụm CSDL phân tán và giải phóng tài nguyên..."
cd "$PROJECT_ROOT/infrastructure" || exit 1
./stop.sh

echo "🧹 Toàn bộ hạ tầng CSDL đã được dừng và giải phóng an toàn!"
