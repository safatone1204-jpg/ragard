# Script to fully restart the backend server with clean cache

Write-Host "Stopping any running Python processes..." -ForegroundColor Yellow
Get-Process python -ErrorAction SilentlyContinue | Where-Object { $_.CommandLine -like "*uvicorn*" } | Stop-Process -Force -ErrorAction SilentlyContinue

Write-Host "Clearing Python cache..." -ForegroundColor Yellow
Get-ChildItem -Path . -Recurse -Filter "__pycache__" -ErrorAction SilentlyContinue | Remove-Item -Recurse -Force -ErrorAction SilentlyContinue
Get-ChildItem -Path . -Recurse -Filter "*.pyc" -ErrorAction SilentlyContinue | Remove-Item -Force -ErrorAction SilentlyContinue

Write-Host "Verifying environment configuration..." -ForegroundColor Cyan
python -c "from app.core.config import settings; print('ENVIRONMENT:', settings.ENVIRONMENT); print('SUPABASE_URL set:', 'Yes' if settings.SUPABASE_URL else 'No')"

Write-Host ""
Write-Host "Starting server..." -ForegroundColor Green
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

