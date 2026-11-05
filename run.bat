@echo off
setlocal

echo ==============================================================================
echo   AI Stock Market Research ^& Ranking Agent (NSE ^& BSE)
echo   Starting Institutional FinTech Platform...
echo ==============================================================================
echo.

if not exist ".venv\Scripts\python.exe" (
    echo [ERROR] Virtual environment not found!
    echo Please run 'setup.bat' first to initialize the environment and dependencies.
    echo.
    pause
    exit /b 1
)

:: Activate virtual environment
call .venv\Scripts\activate.bat

echo Server is starting...
echo Dashboard URL: http://127.0.0.1:8000/
echo Press Ctrl + C to stop the server anytime.
echo.

python manage.py runserver 0.0.0.0:8000

pause
