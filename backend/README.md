# Ragard Backend API

FastAPI backend for Ragard - meme/small-cap stock analysis platform.

## Setup

1. **Create a virtual environment:**
   ```bash
   python -m venv venv
   ```

2. **Activate the virtual environment:**
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

3. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

4. **Create a `.env` file** (see `env.example` for all options):
   ```env
   ENVIRONMENT=development
   SUPABASE_URL=your_supabase_url
   SUPABASE_ANON_KEY=your_anon_key
   SUPABASE_SERVICE_ROLE_KEY=your_service_role_key
   CORS_ORIGINS=http://localhost:3000,http://localhost:8000
   ```

## Running the API

Start the development server:
```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

The API will be available at `http://localhost:8000`

- API docs (Swagger UI): `http://localhost:8000/docs`
- Alternative docs (ReDoc): `http://localhost:8000/redoc`
- Health check: `http://localhost:8000/health`

## Data Sources

The API uses real data sources:
- **Market Data**: yfinance for stock prices and market data
- **Reddit Data**: Async PRAW for Reddit post analysis (optional - works in read-only mode)
- **Scoring**: Centralized regard score calculation using real market fundamentals

