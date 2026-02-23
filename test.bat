@echo off
title GPT CRM Tests
cd /d "%~dp0"

:: Activate virtual environment
call venv\Scripts\activate

:: Set test environment
set ENVIRONMENT=test
set RATE_LIMIT_WINDOW=1
set DATABASE_PATH=data/test.db

:: Run tests
echo Running test suite...
echo.
pytest tests/ -v --cov=app --cov-report=term

:: Show coverage report
echo.
echo Test coverage report:
coverage report -m

pause
