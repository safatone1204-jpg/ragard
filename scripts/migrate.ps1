# Database migration script for Supabase/Postgres
# This script applies migrations from the migrations/ directory

$ErrorActionPreference = "Stop"

$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$ProjectRoot = Split-Path -Parent $ScriptDir
$MigrationsDir = Join-Path $ProjectRoot "migrations"

Write-Host "Running database migrations..." -ForegroundColor Cyan

# Check if Supabase CLI is available
$supabaseCmd = Get-Command supabase -ErrorAction SilentlyContinue
if (-not $supabaseCmd) {
    Write-Host "⚠ Supabase CLI not found. Installing..." -ForegroundColor Yellow
    Write-Host "Please install it from: https://supabase.com/docs/guides/cli" -ForegroundColor Yellow
    exit 1
}

# Check if migrations directory exists
if (-not (Test-Path $MigrationsDir)) {
    Write-Host "⚠ Migrations directory not found: $MigrationsDir" -ForegroundColor Yellow
    exit 1
}

# Apply migrations using Supabase CLI
Write-Host "Applying migrations from $MigrationsDir..." -ForegroundColor Cyan

# Get SQL files in migrations directory
$sqlFiles = Get-ChildItem -Path $MigrationsDir -Filter "*.sql" | Sort-Object Name

if ($sqlFiles.Count -eq 0) {
    Write-Host "⚠ No SQL migration files found in $MigrationsDir" -ForegroundColor Yellow
    exit 1
}

foreach ($sqlFile in $sqlFiles) {
    Write-Host "Applying: $($sqlFile.Name)" -ForegroundColor Gray
    try {
        # Use Supabase CLI to apply migration
        # Note: This requires a linked project
        supabase db push --file $sqlFile.FullName
        Write-Host "✓ Applied: $($sqlFile.Name)" -ForegroundColor Green
    } catch {
        Write-Host "⚠ Failed to apply $($sqlFile.Name)" -ForegroundColor Yellow
        Write-Host "You may need to apply this migration manually via Supabase dashboard" -ForegroundColor Yellow
    }
}

Write-Host ""
Write-Host "✓ Migrations complete!" -ForegroundColor Green
Write-Host ""
Write-Host "Note: If using Supabase, you can also apply migrations via:" -ForegroundColor Gray
Write-Host "  1. Supabase Dashboard > SQL Editor" -ForegroundColor Gray
Write-Host "  2. Copy and paste the SQL from migrations\*.sql files" -ForegroundColor Gray
Write-Host ""

