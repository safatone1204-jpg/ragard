# Clean script for Windows PowerShell
# Removes development artifacts

Write-Host "Cleaning development artifacts..." -ForegroundColor Green

# Backend artifacts
if (Test-Path "backend\venv") {
    Write-Host "Removing backend\venv..." -ForegroundColor Yellow
    Remove-Item -Recurse -Force "backend\venv"
}

if (Test-Path "backend\ragard.db") {
    Write-Host "Removing backend\ragard.db..." -ForegroundColor Yellow
    Remove-Item -Force "backend\ragard.db"
}

if (Test-Path "backend\ragard.db-journal") {
    Write-Host "Removing backend\ragard.db-journal..." -ForegroundColor Yellow
    Remove-Item -Force "backend\ragard.db-journal"
}

# Frontend artifacts
if (Test-Path "frontend\node_modules") {
    Write-Host "Removing frontend\node_modules..." -ForegroundColor Yellow
    Remove-Item -Recurse -Force "frontend\node_modules"
}

if (Test-Path "frontend\.next") {
    Write-Host "Removing frontend\.next..." -ForegroundColor Yellow
    Remove-Item -Recurse -Force "frontend\.next"
}

if (Test-Path "frontend\out") {
    Write-Host "Removing frontend\out..." -ForegroundColor Yellow
    Remove-Item -Recurse -Force "frontend\out"
}

if (Test-Path "frontend\build") {
    Write-Host "Removing frontend\build..." -ForegroundColor Yellow
    Remove-Item -Recurse -Force "frontend\build"
}

# Python cache
Get-ChildItem -Path . -Recurse -Directory -Filter "__pycache__" | Remove-Item -Recurse -Force
Get-ChildItem -Path . -Recurse -File -Filter "*.pyc" | Remove-Item -Force

Write-Host "Clean complete!" -ForegroundColor Green

