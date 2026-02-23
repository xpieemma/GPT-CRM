@echo off
title Seed Demo Data
cd /d "%~dp0"
call venv\Scripts\activate
echo Seeding demo database (rich multi-tenant data)...
echo.
python scripts/seed_demo.py --force
echo.
pause
