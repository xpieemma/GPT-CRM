@echo off
title Seed Development Data
cd /d "%~dp0"
call venv\Scripts\activate
echo Seeding development database (minimal data)...
echo.
python scripts/seed_dev.py --force
echo.
pause
