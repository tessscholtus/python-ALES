@echo off
REM ============================================
REM PDF Extractor - Windows Installatie Script
REM ============================================
echo.
echo ========================================
echo PDF Extractor Installatie
echo ========================================
echo.

REM Check of Python geinstalleerd is
python --version >nul 2>&1
if errorlevel 1 (
    echo [FOUT] Python is niet geinstalleerd of niet in PATH
    echo Download Python van: https://www.python.org/downloads/
    pause
    exit /b 1
)

echo [OK] Python gevonden
python --version

REM Maak virtual environment aan als die niet bestaat
if not exist "venv" (
    echo.
    echo [INFO] Virtual environment aanmaken...
    python -m venv venv
    if errorlevel 1 (
        echo [FOUT] Kon virtual environment niet aanmaken
        pause
        exit /b 1
    )
    echo [OK] Virtual environment aangemaakt
) else (
    echo [OK] Virtual environment bestaat al
)

REM Activeer virtual environment
echo.
echo [INFO] Virtual environment activeren...
call venv\Scripts\activate.bat

REM Upgrade pip eerst
echo.
echo [INFO] Pip upgraden...
python -m pip install --upgrade pip

REM Installeer alle requirements
echo.
echo [INFO] Packages installeren...
pip install -r requirements.txt

if errorlevel 1 (
    echo [FOUT] Package installatie mislukt
    pause
    exit /b 1
)

REM Verificeer installatie
echo.
echo [INFO] Installatie verifieren...
echo.
echo Geinstalleerde packages:
pip list

REM Test of alle benodigde modules werken
echo.
echo [INFO] Modules testen...
python -c "import click; import google.genai; import yaml; import dotenv; import pydantic; import rich; print('[OK] Alle modules succesvol geladen!')"

if errorlevel 1 (
    echo [FOUT] Niet alle modules konden geladen worden
    pause
    exit /b 1
)

REM Check .env bestand
echo.
if not exist ".env" (
    echo [WAARSCHUWING] .env bestand ontbreekt!
    echo Maak een .env bestand aan met:
    echo GEMINI_API_KEY=jouw_api_key_hier
    echo.
) else (
    echo [OK] .env bestand gevonden
)

echo.
echo ========================================
echo Installatie voltooid!
echo ========================================
echo.
echo Gebruik:
echo   1. Open PowerShell in deze map
echo   2. Activeer venv: .\venv\Scripts\Activate.ps1
echo   3. Voer uit: python -m extractor.main "pad\naar\map" -c auto
echo.
pause
