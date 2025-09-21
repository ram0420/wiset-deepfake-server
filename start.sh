#!/usr/bin/env bash
set -euo pipefail

PORT="${PORT:-8000}"   # Render가 주는 포트 사용, 없으면 8000
echo "Starting app on port $PORT"

# 메모리 아끼려면 workers=1 권장
exec uvicorn app.main:app --host 0.0.0.0 --port "$PORT" --workers 1
