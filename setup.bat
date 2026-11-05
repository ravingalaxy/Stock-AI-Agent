@echo off
setlocal enabledelayedexpansion

echo ==============================================================================
echo   AI Stock Market Research ^& Ranking Agent (NSE ^& BSE)
echo   Automated Windows Setup
echo ==============================================================================
echo.

:: 1. Verify Python Installation
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] Python is not installed or not in your PATH!
    echo Please install Python 3.10, 3.11, or 3.12 from https://www.python.org/
    echo Make sure to check "Add Python to PATH" during installation.
    pause
    exit /b 1
)

for /f "tokens=2 delims= " %%v in ('python --version 2^>^&1') do set PYTHON_VERSION=%%v
echo [1/6] Found Python %PYTHON_VERSION%

:: 2. Create Virtual Environment (.venv)
if not exist ".venv" (
    echo [2/6] Creating Python virtual environment in .venv...
    python -m venv .venv
    if %errorlevel% neq 0 (
        echo [ERROR] Failed to create virtual environment!
        pause
        exit /b 1
    )
) else (
    echo [2/6] Virtual environment .venv already exists.
)

:: 3. Upgrade pip and Install Dependencies
echo [3/6] Installing dependencies from requirements.txt...
call .venv\Scripts\activate.bat
python -m pip install --upgrade pip
pip install -r requirements.txt
if %errorlevel% neq 0 (
    echo [ERROR] Dependency installation encountered issues.
    pause
    exit /b 1
)

:: 4. Environment Configuration
echo [4/6] Setting up environment configuration...
if not exist ".env" (
    if exist ".env.example" (
        copy .env.example .env >nul
        echo       Created .env from .env.example.
    )
)
if not exist "config\.env" (
    if exist "config\.env.example" (
        copy config\.env.example config\.env >nul
        echo       Created config\.env from config\.env.example.
    )
)

:: 5. Ensure Runtime Folders Exist
if not exist "data" mkdir data
if not exist "data\reports" mkdir data\reports
if not exist "data\logs" mkdir data\logs

:: 6. Run Database Migrations and Seed Universe
echo [5/6] Applying database migrations...
python manage.py migrate --noinput
if %errorlevel% neq 0 (
    echo [ERROR] Failed to apply database migrations!
    pause
    exit /b 1
)

echo [6/6] Seeding baseline Indian equity universe ^& IPO data...
python manage.py seed_universe

echo.
echo ==============================================================================
echo   Setup Completed Successfully!
echo   To launch the application:
echo     - Double click 'run.bat'
echo     - Or run: .venv\Scripts\python manage.py runserver 127.0.0.1:8000
echo ==============================================================================
echo.
pause
