@echo off
echo Setting up GPT CRM Outreach...
echo.

:: Create virtual environment
echo Creating virtual environment...
python -m venv venv

:: Activate and install
echo Installing dependencies...
call venv\Scripts\activate
pip install -r requirements.txt
pip install -r requirements-test.txt

:: Create data directory
if not exist data mkdir data

:: Initialize database
echo Initializing database...
sqlite3 data/outreach.db < migrations\init.sql

:: Copy .env file
if not exist .env copy .env.example .env

echo.
echo ====================================================
echo ✅ SETUP COMPLETE!
echo ====================================================
echo.
echo 🔑 NEXT STEP: Get your FREE API key
echo.
echo Choose your provider (all have free tiers):
echo.
echo   1. Groq 🚀 (Recommended - Fastest, no credit card)
echo      - Go to: https://console.groq.com
echo      - Sign up with Google/GitHub
echo      - Copy your API key
echo      - Models: mixtral-8x7b, llama3-70b
echo.
echo   2. Google Gemini ✨ (60 requests/min free)
echo      - Go to: https://makersuite.google.com/app/apikey
echo      - Create API key (free, requires Google account)
echo      - Model: gemini-1.5-flash
echo.
echo   3. OpenAI 💰 (Paid - $5 minimum)
echo      - Only if you already have credits
echo.
echo ====================================================
echo 📝 Edit .env file with your chosen provider:
echo.
echo    Example for Groq:
echo    PROVIDER=groq
echo    GROQ_API_KEY=gsk_your_key_here
echo    MODEL=mixtral-8x7b-32768
echo.
echo ====================================================
echo.
echo 🚀 Next commands:
echo   1. Edit .env - notepad .env
echo   2. Run server - run.bat
echo   3. Run tests - test.bat
echo   4. Seed demo data - seed-demo.bat
echo.
pause