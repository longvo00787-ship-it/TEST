#!/bin/bash
# Khởi động Fall Detection AI System

echo "============================================="
echo "Fall Detection AI - Starting..."
echo "============================================="

# Start backend
cd "$(dirname "$0")"
echo "[1/2] Starting backend on port 8000..."
python -m uvicorn backend.main:app --host 0.0.0.0 --port 8000 &
BACKEND_PID=$!

echo "[2/2] Backend started (PID: $BACKEND_PID)"
echo ""
echo "============================================="
echo "Dashboard: http://localhost:8000"
echo "API docs:  http://localhost:8000/docs"
echo "============================================="
echo "Press Ctrl+C to stop"

wait $BACKEND_PID