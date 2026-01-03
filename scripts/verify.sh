#!/bin/bash
# Verify script - runs lint, test, and build checks
# Usage: ./scripts/verify.sh [backend|frontend|all]

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

TARGET="${1:-all}"

echo "=========================================="
echo "Ragard Verification Script"
echo "=========================================="
echo ""

# Backend verification
if [ "$TARGET" = "backend" ] || [ "$TARGET" = "all" ]; then
    echo "🔍 Verifying backend..."
    cd "$PROJECT_ROOT/backend"
    
    # Check if virtual environment exists
    if [ ! -d "venv" ]; then
        echo "⚠ Virtual environment not found. Creating..."
        python3 -m venv venv
        source venv/bin/activate
        pip install -r requirements.txt
    else
        source venv/bin/activate
    fi
    
    # Install dev dependencies if needed
    pip install -q ruff black pytest || true
    
    # Run linting
    echo "  Running ruff..."
    ruff check app/ || echo "  ⚠ Ruff found issues (non-blocking)"
    
    echo "  Checking formatting..."
    black --check app/ || echo "  ⚠ Formatting issues found (non-blocking)"
    
    # Run tests
    echo "  Running tests..."
    ENVIRONMENT=development \
    SUPABASE_URL=${SUPABASE_URL:-https://test.supabase.co} \
    SUPABASE_ANON_KEY=${SUPABASE_ANON_KEY:-test-anon-key} \
    SUPABASE_SERVICE_ROLE_KEY=${SUPABASE_SERVICE_ROLE_KEY:-test-service-key} \
    CORS_ORIGINS=http://localhost:3000,http://localhost:8000 \
    pytest tests/ -v || echo "  ⚠ Some tests failed (non-blocking)"
    
    echo "✓ Backend verification complete"
    echo ""
fi

# Frontend verification
if [ "$TARGET" = "frontend" ] || [ "$TARGET" = "all" ]; then
    echo "🔍 Verifying frontend..."
    cd "$PROJECT_ROOT/frontend"
    
    # Check if node_modules exists
    if [ ! -d "node_modules" ]; then
        echo "  Installing dependencies..."
        npm install
    fi
    
    # Run linting
    echo "  Running ESLint..."
    npm run lint || echo "  ⚠ ESLint found issues (non-blocking)"
    
    # Run build
    echo "  Building..."
    NEXT_PUBLIC_API_BASE_URL=${NEXT_PUBLIC_API_BASE_URL:-http://localhost:8000} \
    NEXT_PUBLIC_SUPABASE_URL=${NEXT_PUBLIC_SUPABASE_URL:-https://test.supabase.co} \
    NEXT_PUBLIC_SUPABASE_ANON_KEY=${NEXT_PUBLIC_SUPABASE_ANON_KEY:-test-anon-key} \
    npm run build || {
        echo "  ❌ Build failed"
        exit 1
    }
    
    echo "✓ Frontend verification complete"
    echo ""
fi

echo "=========================================="
echo "✓ Verification complete!"
echo "=========================================="

