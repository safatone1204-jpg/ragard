# Setup environment files from examples
# This script copies env.example files to .env/.env.local if they don't exist

$ErrorActionPreference = "Stop"

$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$ProjectRoot = Split-Path -Parent $ScriptDir

Write-Host "Setting up environment files..." -ForegroundColor Cyan

# Backend .env
$BackendEnvExample = Join-Path $ProjectRoot "backend\env.example"
$BackendEnv = Join-Path $ProjectRoot "backend\.env"

if (-not (Test-Path $BackendEnv)) {
    if (Test-Path $BackendEnvExample) {
        Copy-Item $BackendEnvExample $BackendEnv
        Write-Host "[OK] Created backend\.env from env.example" -ForegroundColor Green
    }
    else {
        Write-Host "[WARN] Warning: backend\env.example not found" -ForegroundColor Yellow
    }
}
else {
    Write-Host "[OK] backend\.env already exists (skipping)" -ForegroundColor Green
}

# Frontend .env.local
$FrontendEnvExample = Join-Path $ProjectRoot "frontend\env.example"
$FrontendEnv = Join-Path $ProjectRoot "frontend\.env.local"

if (-not (Test-Path $FrontendEnv)) {
    if (Test-Path $FrontendEnvExample) {
        Copy-Item $FrontendEnvExample $FrontendEnv
        Write-Host "[OK] Created frontend\.env.local from env.example" -ForegroundColor Green
    }
    else {
        Write-Host "[WARN] Warning: frontend\env.example not found" -ForegroundColor Yellow
    }
}
else {
    Write-Host "[OK] frontend\.env.local already exists (skipping)" -ForegroundColor Green
}

Write-Host ""
Write-Host "==========================================" -ForegroundColor Cyan
Write-Host "Environment files setup complete!" -ForegroundColor Cyan
Write-Host "==========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "IMPORTANT: Please edit the following files and fill in your values:" -ForegroundColor Yellow
Write-Host "  - backend\.env"
Write-Host "  - frontend\.env.local"
Write-Host ""
Write-Host "See the example files for documentation on each variable:" -ForegroundColor Gray
Write-Host "  - backend\env.example"
Write-Host "  - frontend\env.example"
Write-Host ""
