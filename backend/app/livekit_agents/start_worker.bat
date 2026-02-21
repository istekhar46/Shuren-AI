@echo off
REM LiveKit Voice Agent Worker Startup Script for Windows
REM This script starts the voice agent worker in development mode with hot-reload

echo ========================================
echo Starting LiveKit Voice Agent Worker
echo ========================================
echo.

REM Check if we're in the correct directory
if not exist "app\livekit_agents\voice_agent_worker.py" (
    echo ERROR: Must run from backend directory
    echo Current directory: %CD%
    echo Please run: cd backend
    pause
    exit /b 1
)

REM Check if .env file exists
if not exist ".env" (
    echo ERROR: .env file not found
    echo Please create .env file with LiveKit credentials
    echo See .env.example for reference
    pause
    exit /b 1
)

echo Starting worker in development mode...
echo Press Ctrl+C to stop the worker
echo.

poetry run python app/livekit_agents/voice_agent_worker.py dev

pause
