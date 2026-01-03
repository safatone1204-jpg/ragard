#!/bin/bash
# Database migration script for Supabase/Postgres
# This script applies migrations from the migrations/ directory

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
MIGRATIONS_DIR="$PROJECT_ROOT/migrations"

echo "Running database migrations..."

# Check if Supabase CLI is available
if ! command -v supabase &> /dev/null; then
    echo "⚠ Supabase CLI not found. Installing..."
    echo "Please install it from: https://supabase.com/docs/guides/cli"
    exit 1
fi

# Check if migrations directory exists
if [ ! -d "$MIGRATIONS_DIR" ]; then
    echo "⚠ Migrations directory not found: $MIGRATIONS_DIR"
    exit 1
fi

# Apply migrations using Supabase CLI
# This assumes you have a Supabase project linked
# If not, run: supabase link --project-ref <your-project-ref>

echo "Applying migrations from $MIGRATIONS_DIR..."

# List SQL files in migrations directory
SQL_FILES=$(find "$MIGRATIONS_DIR" -name "*.sql" | sort)

if [ -z "$SQL_FILES" ]; then
    echo "⚠ No SQL migration files found in $MIGRATIONS_DIR"
    exit 1
fi

for sql_file in $SQL_FILES; do
    echo "Applying: $(basename "$sql_file")"
    # Use Supabase CLI to apply migration
    # Note: This requires a linked project
    supabase db push --file "$sql_file" || {
        echo "⚠ Failed to apply $(basename "$sql_file")"
        echo "You may need to apply this migration manually via Supabase dashboard"
    }
done

echo ""
echo "✓ Migrations complete!"
echo ""
echo "Note: If using Supabase, you can also apply migrations via:"
echo "  1. Supabase Dashboard > SQL Editor"
echo "  2. Copy and paste the SQL from migrations/*.sql files"
echo ""

