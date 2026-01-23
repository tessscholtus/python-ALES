# ============================================
# PDF Extractor - PowerShell Installatie Script
# ============================================
# Dit script werkt ook met UNC paden (\\server\share)
# ============================================

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "PDF Extractor Installatie" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Bewaar huidige locatie
$scriptPath = $PSScriptRoot
if (-not $scriptPath) {
    $scriptPath = (Get-Location).Path
}

# Check of Python geinstalleerd is
try {
    $pythonVersion = python --version 2>&1
    Write-Host "[OK] Python gevonden: $pythonVersion" -ForegroundColor Green
} catch {
    Write-Host "[FOUT] Python is niet geinstalleerd of niet in PATH" -ForegroundColor Red
    Write-Host "Download Python van: https://www.python.org/downloads/" -ForegroundColor Yellow
    Read-Host "Druk op Enter om af te sluiten"
    exit 1
}

# Maak virtual environment aan als die niet bestaat
$venvPath = Join-Path $scriptPath "venv"
if (-not (Test-Path $venvPath)) {
    Write-Host ""
    Write-Host "[INFO] Virtual environment aanmaken..." -ForegroundColor Yellow
    python -m venv $venvPath
    if ($LASTEXITCODE -ne 0) {
        Write-Host "[FOUT] Kon virtual environment niet aanmaken" -ForegroundColor Red
        Read-Host "Druk op Enter om af te sluiten"
        exit 1
    }
    Write-Host "[OK] Virtual environment aangemaakt" -ForegroundColor Green
} else {
    Write-Host "[OK] Virtual environment bestaat al" -ForegroundColor Green
}

# Activeer virtual environment
Write-Host ""
Write-Host "[INFO] Virtual environment activeren..." -ForegroundColor Yellow
$activateScript = Join-Path $venvPath "Scripts\Activate.ps1"
& $activateScript

# Upgrade pip eerst
Write-Host ""
Write-Host "[INFO] Pip upgraden..." -ForegroundColor Yellow
python -m pip install --upgrade pip

# Installeer alle requirements
Write-Host ""
Write-Host "[INFO] Packages installeren..." -ForegroundColor Yellow
$requirementsPath = Join-Path $scriptPath "requirements.txt"
pip install -r $requirementsPath

if ($LASTEXITCODE -ne 0) {
    Write-Host "[FOUT] Package installatie mislukt" -ForegroundColor Red
    Read-Host "Druk op Enter om af te sluiten"
    exit 1
}

# Verificeer installatie
Write-Host ""
Write-Host "[INFO] Installatie verifieren..." -ForegroundColor Yellow
Write-Host ""
Write-Host "Geinstalleerde packages:" -ForegroundColor Cyan
pip list

# Test of alle benodigde modules werken
Write-Host ""
Write-Host "[INFO] Modules testen..." -ForegroundColor Yellow
$testCode = @"
import click
import google.genai
import yaml
import dotenv
import pydantic
import rich
print('[OK] Alle modules succesvol geladen!')
"@

python -c $testCode

if ($LASTEXITCODE -ne 0) {
    Write-Host "[FOUT] Niet alle modules konden geladen worden" -ForegroundColor Red
    Read-Host "Druk op Enter om af te sluiten"
    exit 1
}

# Check .env bestand
Write-Host ""
$envPath = Join-Path $scriptPath ".env"
if (-not (Test-Path $envPath)) {
    Write-Host "[WAARSCHUWING] .env bestand ontbreekt!" -ForegroundColor Yellow
    Write-Host "Maak een .env bestand aan met:" -ForegroundColor Yellow
    Write-Host "GEMINI_API_KEY=jouw_api_key_hier" -ForegroundColor White
    Write-Host ""
    
    # Vraag of gebruiker API key wil invoeren
    $apiKey = Read-Host "Voer je GEMINI_API_KEY in (of druk Enter om over te slaan)"
    if ($apiKey) {
        "GEMINI_API_KEY=$apiKey" | Out-File -FilePath $envPath -Encoding UTF8
        Write-Host "[OK] .env bestand aangemaakt" -ForegroundColor Green
    }
} else {
    Write-Host "[OK] .env bestand gevonden" -ForegroundColor Green
}

Write-Host ""
Write-Host "========================================" -ForegroundColor Green
Write-Host "Installatie voltooid!" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Green
Write-Host ""
Write-Host "Gebruik:" -ForegroundColor Cyan
Write-Host "  python -m extractor.main `"pad\naar\map`" -c auto" -ForegroundColor White
Write-Host ""
Write-Host "Voorbeeld:" -ForegroundColor Cyan
Write-Host "  python -m extractor.main `"C:\Data\10014675_2`" -c auto" -ForegroundColor White
Write-Host ""

Read-Host "Druk op Enter om af te sluiten"
