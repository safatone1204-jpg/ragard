# Ragard

Meme and small-cap stock analysis platform built with FastAPI and Next.js.

## Architecture

This is a monorepo containing:
- `backend/` - FastAPI backend API
- `frontend/` - Next.js 14 frontend with TypeScript and Tailwind CSS

## Quick Start

### Prerequisites

- Python 3.10+
- Node.js 18+
- npm or yarn

### Backend Setup

1. Navigate to the backend directory:
   ```bash
   cd backend
   ```

2. Create a virtual environment:
   ```bash
   python -m venv venv
   ```

3. Activate the virtual environment:
   - Windows (PowerShell):
     ```powershell
     .\venv\Scripts\Activate.ps1
     ```
   - Windows (CMD):
     ```cmd
     venv\Scripts\activate.bat
     ```
   - Linux/Mac:
     ```bash
     source venv/bin/activate
     ```

4. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

5. Run the backend server:
   ```bash
   uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
   ```

The backend API will be available at `http://localhost:8000`

### Frontend Setup

1. Navigate to the frontend directory:
   ```bash
   cd frontend
   ```

2. Install dependencies:
   ```bash
   npm install
   ```

3. Run the frontend development server:
   ```bash
   npm run dev
   ```

The frontend will be available at `http://localhost:3000`

## Data Sources

The application uses real data sources:
- **Market Data**: yfinance for stock prices, market cap, and other metrics
- **Reddit Data**: Async PRAW for Reddit post analysis (optional - works in read-only mode without credentials)
- **Scoring**: Centralized regard score calculation using real market fundamentals and AI analysis

## Project Structure

```
Ragard/
├── backend/
│   ├── app/
│   │   ├── api/          # API endpoints
│   │   ├── core/         # Configuration
│   │   ├── models/       # Pydantic models
│   │   ├── schemas/      # API schemas
│   │   ├── services/     # Business logic
│   │   └── main.py       # FastAPI app
│   ├── requirements.txt
│   └── README.md
├── frontend/
│   ├── app/              # Next.js App Router
│   ├── components/       # React components
│   ├── lib/              # Utilities and API client
│   └── package.json
└── README.md
```

## Environment Variables

### Quick Setup (Recommended)

Use the setup scripts to automatically create environment files:

- **Linux/Mac**: `bash scripts/setup-env.sh`
- **Windows**: 
  ```powershell
  powershell -ExecutionPolicy Bypass -File scripts/setup-env.ps1
  ```
  
  **Note**: If you get an execution policy error, use the command above with `-ExecutionPolicy Bypass`.

These scripts will:
- Copy `backend/env.example` → `backend/.env` (if missing)
- Copy `frontend/env.example` → `frontend/.env.local` (if missing)
- Never overwrite existing files

### Manual Setup

#### Backend Setup

1. Copy the example environment file:
   ```bash
   cd backend
   cp env.example .env
   ```

2. Edit `.env` and fill in your values:
   - **REQUIRED**: `ENVIRONMENT`, `SUPABASE_URL`, `SUPABASE_ANON_KEY`, `SUPABASE_SERVICE_ROLE_KEY`, `CORS_ORIGINS`
   - **REQUIRED for production**: `ENVIRONMENT=production`
   - **OPTIONAL**: `OPENAI_API_KEY` (required for AI features), `REDDIT_CLIENT_ID`, `REDDIT_CLIENT_SECRET`, `SENTRY_DSN`

See `backend/env.example` for detailed comments on each variable.

**Note**: The backend will validate required environment variables on startup and exit with a clear error message if any are missing.

#### Frontend Setup

1. Copy the example environment file:
   ```bash
   cd frontend
   cp env.example .env.local
   ```

2. Edit `.env.local` and fill in your values:
   - **REQUIRED**: `NEXT_PUBLIC_API_BASE_URL`, `NEXT_PUBLIC_SUPABASE_URL`, `NEXT_PUBLIC_SUPABASE_ANON_KEY`
   - **OPTIONAL**: `NEXT_PUBLIC_SENTRY_DSN`

See `frontend/env.example` for detailed comments on each variable.

**⚠️ IMPORTANT**: Never commit `.env` or `.env.local` files to version control. They contain secrets. The CI pipeline will fail if environment files are tracked by git.

## Development

- Backend API docs: `http://localhost:8000/docs`
- Frontend: `http://localhost:3000`

## Scripts

### Setup Scripts

- **Linux/Mac**: `bash scripts/setup-env.sh`
- **Windows**: `powershell scripts/setup-env.ps1`

Creates `.env` files from examples (never overwrites existing files).

### Verification Scripts

Run lint, test, and build checks:

- **Linux/Mac**: `bash scripts/verify.sh [backend|frontend|all]`
- **Windows**: `powershell scripts/verify.ps1 [backend|frontend|all]`

Example:
```bash
# Verify everything
bash scripts/verify.sh

# Verify only backend
bash scripts/verify.sh backend

# Verify only frontend
bash scripts/verify.sh frontend
```

### Migration Scripts

Apply database migrations (Supabase/Postgres):

- **Linux/Mac**: `bash scripts/migrate.sh`
- **Windows**: `powershell scripts/migrate.ps1`

**Note**: Requires Supabase CLI and a linked project. See `migrations/` directory for SQL files.

### Clean Scripts

Remove development artifacts before committing:

- **Linux/Mac**: `bash scripts/clean.sh`
- **Windows**: `powershell scripts/clean.ps1`

This removes:
- `node_modules/`, `.next/`, `build/`, `out/` (frontend)
- `venv/`, `__pycache__/`, `*.pyc` (backend)
- `ragard.db`, `ragard.db-journal` (database files)

## Migrations

Database migrations are stored in the `migrations/` directory as SQL files.

### Applying Migrations

**Using Supabase CLI** (recommended):
```bash
bash scripts/migrate.sh
# or
powershell scripts/migrate.ps1
```

**Manual Application**:
1. Open Supabase Dashboard → SQL Editor
2. Copy the contents of each `.sql` file from `migrations/`
3. Run them in order

### Migration Files

- `add_benchmark_fields_to_user_regard_summaries.sql`
- `create_open_positions_table.sql`

**Note**: SQLite (`ragard.db`) is only used in development. Production deployments must use Supabase/Postgres. The backend will refuse to use SQLite when `ENVIRONMENT=production`.

## Production Readiness Checklist

Before deploying to production:

- [ ] Set `ENVIRONMENT=production` in backend `.env`
- [ ] Configure all required environment variables (see `backend/env.example`)
- [ ] Set `CORS_ORIGINS` to your production domain(s)
- [ ] Ensure Supabase/Postgres is configured (SQLite is disabled in production)
- [ ] Apply all database migrations
- [ ] Configure `NEXT_PUBLIC_API_BASE_URL` in frontend `.env.local`
- [ ] Run verification scripts: `bash scripts/verify.sh`
- [ ] Test the `/health` endpoint
- [ ] Verify no environment files are tracked by git (CI will check this)

## Chrome Extension

### Loading the Extension

1. Open Chrome and navigate to `chrome://extensions`
2. Enable "Developer mode" (toggle in top right)
3. Click "Load unpacked"
4. Select the `extension/ragard-chrome-ext/` directory

### Configuration

The extension can be configured via:
- **Options Page**: Right-click extension icon → Options (or `chrome://extensions` → Ragard → Options)
- **Side Panel Settings**: Click the settings icon in the side panel

Settings include:
- API Base URL (default: `http://localhost:8000`)
- Web App Base URL (default: `http://localhost:3000`)
- Test Connection button (pings `/health` endpoint)

### Permissions

The extension uses `optional_host_permissions` - it will request permission to access the current tab's URL only when you click "Analyze". This is more secure than requesting `<all_urls>` upfront.

