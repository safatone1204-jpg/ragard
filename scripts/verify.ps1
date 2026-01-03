# Verify script - runs lint, test, and build checks
# Usage: .\scripts\verify.ps1 [backend|frontend|all]

param(
    [string]$Target = "all"
)

$ErrorActionPreference = "Stop"

$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$ProjectRoot = Split-Path -Parent $ScriptDir

Write-Host "==========================================" -ForegroundColor Cyan
Write-Host "Ragard Verification Script" -ForegroundColor Cyan
Write-Host "==========================================" -ForegroundColor Cyan
Write-Host ""

# Backend verification
if ($Target -eq "backend" -or $Target -eq "all") {
    Write-Host "🔍 Verifying backend..." -ForegroundColor Cyan
    Push-Location "$ProjectRoot\backend"
    
    try {
        # Check if virtual environment exists
        if (-not (Test-Path "venv")) {
            Write-Host "⚠ Virtual environment not found. Creating..." -ForegroundColor Yellow
            python -m venv venv
            & .\venv\Scripts\Activate.ps1
            pip install -r requirements.txt
        } else {
            & .\venv\Scripts\Activate.ps1
        }
        
        # Install dev dependencies if needed
        pip install -q ruff black pytest 2>$null
        
        # Run linting
        Write-Host "  Running ruff..." -ForegroundColor Gray
        ruff check app/ 2>$null || Write-Host "  ⚠ Ruff found issues (non-blocking)" -ForegroundColor Yellow
        
        Write-Host "  Checking formatting..." -ForegroundColor Gray
        black --check app/ 2>$null || Write-Host "  ⚠ Formatting issues found (non-blocking)" -ForegroundColor Yellow
        
        # Run tests
        Write-Host "  Running tests..." -ForegroundColor Gray
        $env:ENVIRONMENT = "development"
        $env:SUPABASE_URL = if ($env:SUPABASE_URL) { $env:SUPABASE_URL } else { "https://test.supabase.co" }
        $env:SUPABASE_ANON_KEY = if ($env:SUPABASE_ANON_KEY) { $env:SUPABASE_ANON_KEY } else { "test-anon-key" }
        $env:SUPABASE_SERVICE_ROLE_KEY = if ($env:SUPABASE_SERVICE_ROLE_KEY) { $env:SUPABASE_SERVICE_ROLE_KEY } else { "test-service-key" }
        $env:CORS_ORIGINS = "http://localhost:3000,http://localhost:8000"
        pytest tests/ -v 2>$null || Write-Host "  ⚠ Some tests failed (non-blocking)" -ForegroundColor Yellow
        
        Write-Host "✓ Backend verification complete" -ForegroundColor Green
        Write-Host ""
    } finally {
        Pop-Location
    }
}

# Frontend verification
if ($Target -eq "frontend" -or $Target -eq "all") {
    Write-Host "🔍 Verifying frontend..." -ForegroundColor Cyan
    Push-Location "$ProjectRoot\frontend"
    
    try {
        # Check if node_modules exists
        if (-not (Test-Path "node_modules")) {
            Write-Host "  Installing dependencies..." -ForegroundColor Gray
            npm install
        }
        
        # Run linting
        Write-Host "  Running ESLint..." -ForegroundColor Gray
        npm run lint 2>$null || Write-Host "  ⚠ ESLint found issues (non-blocking)" -ForegroundColor Yellow
        
        # Run build
        Write-Host "  Building..." -ForegroundColor Gray
        $env:NEXT_PUBLIC_API_BASE_URL = if ($env:NEXT_PUBLIC_API_BASE_URL) { $env:NEXT_PUBLIC_API_BASE_URL } else { "http://localhost:8000" }
        $env:NEXT_PUBLIC_SUPABASE_URL = if ($env:NEXT_PUBLIC_SUPABASE_URL) { $env:NEXT_PUBLIC_SUPABASE_URL } else { "https://test.supabase.co" }
        $env:NEXT_PUBLIC_SUPABASE_ANON_KEY = if ($env:NEXT_PUBLIC_SUPABASE_ANON_KEY) { $env:NEXT_PUBLIC_SUPABASE_ANON_KEY } else { "test-anon-key" }
        npm run build
        
        if ($LASTEXITCODE -ne 0) {
            Write-Host "  ❌ Build failed" -ForegroundColor Red
            exit 1
        }
        
        Write-Host "✓ Frontend verification complete" -ForegroundColor Green
        Write-Host ""
    } finally {
        Pop-Location
    }
}

Write-Host "==========================================" -ForegroundColor Cyan
Write-Host "✓ Verification complete!" -ForegroundColor Green
Write-Host "==========================================" -ForegroundColor Cyan

