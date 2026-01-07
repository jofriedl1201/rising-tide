# Rising Tide - Local Development Server
# This script starts the FastAPI backend with auto-reload for rapid iteration

Write-Host "Starting Rising Tide Development Server..." -ForegroundColor Green

# Set working directory to backend
Set-Location $PSScriptRoot\backend

# Set Python path to include backend directory
$env:PYTHONPATH = "$PSScriptRoot\backend"

# Set environment to development so config.py loads .env file
$env:ENV = "development"

# Activate virtual environment if it exists
if (Test-Path "$PSScriptRoot\.venv\Scripts\Activate.ps1") {
    Write-Host "Activating virtual environment..." -ForegroundColor Yellow
    & "$PSScriptRoot\.venv\Scripts\Activate.ps1"
}
else {
    Write-Host "WARNING: Virtual environment not found at .venv\" -ForegroundColor Red
    Write-Host "Please run: python -m venv .venv" -ForegroundColor Yellow
    exit 1
}

# Check if .env file exists
if (-not (Test-Path "$PSScriptRoot\.env")) {
    Write-Host "WARNING: .env file not found!" -ForegroundColor Red
    Write-Host "Please copy .env.example to .env and configure it" -ForegroundColor Yellow
    exit 1
}

Write-Host "`nStarting Uvicorn server with auto-reload..." -ForegroundColor Green
Write-Host "API will be available at: http://localhost:8000" -ForegroundColor Cyan
Write-Host "API docs will be available at: http://localhost:8000/docs" -ForegroundColor Cyan
Write-Host "`nPress Ctrl+C to stop the server`n" -ForegroundColor Yellow

# Start uvicorn with auto-reload
python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
