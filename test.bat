@echo off
title GPT CRM Tests
cd /d "%~dp0"

:: Set color for better readability
color 0A

:: Activate virtual environment
echo Activating virtual environment...
call venv\Scripts\activate
if %errorlevel% neq 0 (
    echo Failed to activate virtual environment!
    pause
    exit /b 1
)

:: Set test environment
set ENVIRONMENT=test
set RATE_LIMIT_WINDOW=1
set DATABASE_PATH=data/test.db

:: Clean up any old test database files
echo Cleaning up old test databases...
if exist data\test*.db del /q data\test*.db 2>nul

:: Run tests
echo.
echo ========================================
echo    Running Test Suite
echo ========================================
echo.

pytest tests/ -v --cov=app --cov-report=term --cov-report=html --tb=short

:: Check if tests passed
if %errorlevel% equ 0 (
    echo.
    echo ========================================
    echo    ✅ ALL TESTS PASSED!
    echo ========================================
) else (
    echo.
    echo ========================================
    echo    ❌ SOME TESTS FAILED
    echo ========================================
)

:: Show coverage report
echo.
echo ========================================
echo    Coverage Report
echo ========================================
echo.
coverage report -m

:: Open HTML coverage report in browser
echo.
echo Opening HTML coverage report...
start htmlcov\index.html

:: Keep window open
echo.
echo Press any key to exit...
pause > nul

:: Deactivate virtual environment
deactivate