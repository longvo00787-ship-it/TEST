#!/bin/bash
# Start dev mode: backend + frontend hot-reload

echo "Starting backend..."
cd "$(dirname "$0")"
python -m uvicorn backend.main:app --reload --port 8000 &
sleep 2

echo "Starting frontend dev server..."
cd frontend
npm run dev

wait