@echo off
REM ============================================
REM PDF Extractor - Eenmalige Installatie
REM ALES Metaaltechniek
REM ============================================
setlocal

echo.
echo ========================================
echo PDF Extractor - Installatie
echo ========================================
echo.

REM Configuratie
set "UNC_PATH=\\ALESWS1\temp\PDF_EXTRACTOR2"
set "DRIVE_LETTER=Z:"

REM Check of Python geinstalleerd is
python --version >nul 2>&1
if errorlevel 1 (
    echo [FOUT] Python is niet geinstalleerd!
    echo.
    echo Download Python van: https://www.python.org/downloads/
    echo Zorg dat je "Add Python to PATH" aanvinkt tijdens installatie!
    echo.
    pause
    exit /b 1
)

echo [OK] Python gevonden:
python --version
echo.

REM Koppel UNC pad aan drive letter
echo [INFO] Netwerkpad koppelen aan %DRIVE_LETTER%...
net use %DRIVE_LETTER% /delete 2>nul
net use %DRIVE_LETTER% "%UNC_PATH%"
if errorlevel 1 (
    echo [FOUT] Kon netwerkpad niet koppelen
    echo Controleer of je toegang hebt tot %UNC_PATH%
    pause
    exit /b 1
)
echo [OK] %DRIVE_LETTER% gekoppeld aan %UNC_PATH%

REM Ga naar de drive
cd /d %DRIVE_LETTER%

REM Verwijder oude venv als die bestaat
if exist "venv" (
    echo.
    echo [INFO] Oude virtual environment verwijderen...
    rmdir /s /q venv
)

REM Maak nieuwe venv
echo.
echo [INFO] Virtual environment aanmaken...
python -m venv venv
if errorlevel 1 (
    echo [FOUT] Kon virtual environment niet aanmaken
    pause
    exit /b 1
)
echo [OK] Virtual environment aangemaakt

REM Activeer en installeer packages
echo.
echo [INFO] Packages installeren (dit kan even duren)...
call venv\Scripts\activate.bat
python -m pip install --upgrade pip
pip install -r requirements.txt

if errorlevel 1 (
    echo [FOUT] Package installatie mislukt
    pause
    exit /b 1
)

REM Test installatie
echo.
echo [INFO] Installatie testen...
python -c "import click; import google.genai; import yaml; import dotenv; import pydantic; import rich; print('[OK] Alle modules succesvol geladen!')"

if errorlevel 1 (
    echo [FOUT] Niet alle modules werken
    pause
    exit /b 1
)

REM Check .env
echo.
if not exist ".env" (
    echo [INFO] .env bestand aanmaken...
    set /p API_KEY="Voer je GEMINI_API_KEY in: "
    echo GEMINI_API_KEY=!API_KEY!> .env
    echo [OK] .env bestand aangemaakt
) else (
    echo [OK] .env bestand bestaat al
)

echo.
echo ========================================
echo Installatie voltooid!
echo ========================================
echo.
echo Je kunt nu UITVOEREN.bat gebruiken om PDFs te verwerken.
echo.
echo Gebruik:
echo   - Sleep een map met PDFs op UITVOEREN.bat
echo   - Of: UITVOEREN.bat "pad\naar\map"
echo.
pause
