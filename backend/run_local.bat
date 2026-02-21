@echo off
echo ==========================================
echo Shuren Backend - Local Development
echo ==========================================
echo.

REM Check if .env exists
if not exist .env (
    echo Error: .env file not found!
    echo Please copy .env.example to .env and configure it.
    exit /b 1
)

echo Installing dependencies...
poetry install --no-root

echo.
echo Running database migrations...
poetry run alembic upgrade head

echo.
echo Starting API server...
echo    API: http://localhost:8000
echo    Docs: http://localhost:8000/api/docs
echo.
echo Press Ctrl+C to stop
echo ==========================================
echo.

poetry run uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
