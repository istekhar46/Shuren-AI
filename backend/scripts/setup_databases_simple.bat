@echo off
echo ========================================
echo Shuren - Local Database Setup
echo ========================================
echo.
echo Creating local databases...
echo.

REM Try to create databases using psql
psql -U postgres -c "CREATE DATABASE shuren_dev_db;" 2>nul
if %errorlevel% equ 0 (
    echo ✓ Created database 'shuren_dev_db' ^(development^)
) else (
    echo ✓ Database 'shuren_dev_db' already exists ^(development^)
)

psql -U postgres -c "CREATE DATABASE shuren_test_db;" 2>nul
if %errorlevel% equ 0 (
    echo ✓ Created database 'shuren_test_db' ^(testing^)
) else (
    echo ✓ Database 'shuren_test_db' already exists ^(testing^)
)

echo.
echo ========================================
echo ✅ Database setup complete!
echo ========================================
echo.
echo Next steps:
echo   1. Run migrations: poetry run alembic upgrade head
echo   2. Start server: run_local.bat
echo.
pause
