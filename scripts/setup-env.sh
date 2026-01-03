#!/bin/bash
# Setup environment files from examples
# This script copies env.example files to .env/.env.local if they don't exist

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

echo "Setting up environment files..."

# Backend .env
BACKEND_ENV_EXAMPLE="$PROJECT_ROOT/backend/env.example"
BACKEND_ENV="$PROJECT_ROOT/backend/.env"

if [ ! -f "$BACKEND_ENV" ]; then
    if [ -f "$BACKEND_ENV_EXAMPLE" ]; then
        cp "$BACKEND_ENV_EXAMPLE" "$BACKEND_ENV"
        echo "✓ Created backend/.env from env.example"
    else
        echo "⚠ Warning: backend/env.example not found"
    fi
else
    echo "✓ backend/.env already exists (skipping)"
fi

# Frontend .env.local
FRONTEND_ENV_EXAMPLE="$PROJECT_ROOT/frontend/env.example"
FRONTEND_ENV="$PROJECT_ROOT/frontend/.env.local"

if [ ! -f "$FRONTEND_ENV" ]; then
    if [ -f "$FRONTEND_ENV_EXAMPLE" ]; then
        cp "$FRONTEND_ENV_EXAMPLE" "$FRONTEND_ENV"
        echo "✓ Created frontend/.env.local from env.example"
    else
        echo "⚠ Warning: frontend/env.example not found"
    fi
else
    echo "✓ frontend/.env.local already exists (skipping)"
fi

echo ""
echo "=========================================="
echo "Environment files setup complete!"
echo "=========================================="
echo ""
echo "IMPORTANT: Please edit the following files and fill in your values:"
echo "  - backend/.env"
echo "  - frontend/.env.local"
echo ""
echo "See the example files for documentation on each variable:"
echo "  - backend/env.example"
echo "  - frontend/env.example"
echo ""

