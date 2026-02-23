@echo off
title GPT CRM Outreach Server
cd /d "%~dp0"

:: Activate virtual environment
call venv\Scripts\activate

:: Run server
echo Starting server at http://localhost:8000
echo Press Ctrl+C to stop
echo.
uvicorn app.main:app --reload

pause
