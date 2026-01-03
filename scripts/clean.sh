#!/bin/bash
# Clean script to remove development artifacts

set -e

echo "Cleaning development artifacts..."

# Backend artifacts
if [ -d "backend/venv" ]; then
    echo "Removing backend/venv..."
    rm -rf backend/venv
fi

if [ -f "backend/ragard.db" ]; then
    echo "Removing backend/ragard.db..."
    rm -f backend/ragard.db
fi

if [ -f "backend/ragard.db-journal" ]; then
    echo "Removing backend/ragard.db-journal..."
    rm -f backend/ragard.db-journal
fi

# Frontend artifacts
if [ -d "frontend/node_modules" ]; then
    echo "Removing frontend/node_modules..."
    rm -rf frontend/node_modules
fi

if [ -d "frontend/.next" ]; then
    echo "Removing frontend/.next..."
    rm -rf frontend/.next
fi

if [ -d "frontend/out" ]; then
    echo "Removing frontend/out..."
    rm -rf frontend/out
fi

if [ -d "frontend/build" ]; then
    echo "Removing frontend/build..."
    rm -rf frontend/build
fi

# Python cache
find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
find . -type f -name "*.pyc" -delete 2>/dev/null || true

echo "Clean complete!"

