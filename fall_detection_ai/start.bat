@echo off
REM Khởi động Fall Detection AI System
REM Chạy backend (FastAPI) + frontend đã build

echo ====================================
echo Fall Detection AI - Starting...
echo ====================================

REM Start backend
echo [1/2] Starting backend on port 8000...
cd /d "%~dp0"
start "FallDetection-Backend" cmd /c "python -m uvicorn backend.main:app --host 0.0.0.0 --port 8000"

echo [2/2] Backend started.
echo.
echo ====================================
echo Dashboard: http://localhost:8000
echo API docs:  http://localhost:8000/docs
echo ====================================
echo.
pause