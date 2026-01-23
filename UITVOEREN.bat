@echo off
REM ============================================
REM PDF Extractor - ALES Metaaltechniek
REM Dubbelklik om te starten of sleep een map hierop
REM ============================================
setlocal EnableDelayedExpansion

REM Configuratie - pas dit pad aan indien nodig
set "UNC_PATH=\\ALESWS1\temp\PDF_EXTRACTOR2"
set "DRIVE_LETTER=Z:"

REM Koppel UNC pad aan drive letter (negeer als al gekoppeld)
net use %DRIVE_LETTER% "%UNC_PATH%" 2>nul

REM Ga naar de drive
cd /d %DRIVE_LETTER%

REM Check of er een argument meegegeven is (map met PDFs)
if "%~1"=="" (
    echo.
    echo ========================================
    echo PDF Extractor - ALES Metaaltechniek
    echo ========================================
    echo.
    echo Gebruik:
    echo   1. Sleep een map met PDFs op dit bestand
    echo   2. Of voer uit: UITVOEREN.bat "pad\naar\map"
    echo.
    echo Voorbeeld:
    echo   UITVOEREN.bat "\\ALESWS1\temp\PDF_EXTRACTOR2\10014675_2"
    echo.
    set /p INPUT_PATH="Voer het pad naar de PDF map in: "
) else (
    set "INPUT_PATH=%~1"
)

REM Check of het pad bestaat
if not exist "!INPUT_PATH!" (
    echo.
    echo [FOUT] Map niet gevonden: !INPUT_PATH!
    echo.
    pause
    exit /b 1
)

echo.
echo ========================================
echo PDF Extractor wordt gestart...
echo ========================================
echo Input map: !INPUT_PATH!
echo.

REM Activeer venv en voer uit
call %DRIVE_LETTER%\venv\Scripts\activate.bat
python -m extractor.main "!INPUT_PATH!" -c auto

echo.
echo ========================================
if %ERRORLEVEL% EQU 0 (
    echo Klaar! XML bestand is aangemaakt.
) else (
    echo Er is een fout opgetreden.
)
echo ========================================
echo.
pause
