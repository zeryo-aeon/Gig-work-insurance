# ShieldGig Run Script
# Usage: .\run.ps1

Write-Host "🚀 Starting ShieldGig Server..." -ForegroundColor Cyan

# Check for environment
if (Test-Path "env") {
    Write-Host "📦 Using virtual environment..." -ForegroundColor Green
    & .\env\Scripts\python.exe -m uvicorn main:app --app-dir src --host 127.0.0.1 --port 8000 --reload
} else {
    Write-Host "⚠️ No 'env' folder found. Attempting global python..." -ForegroundColor Yellow
    python -m uvicorn main:app --app-dir src --host 127.0.0.1 --port 8000 --reload
}
