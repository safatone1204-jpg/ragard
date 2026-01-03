# Quick Start Guide

## How to Open the Web App

Follow these steps in **two separate terminal windows** (one for backend, one for frontend):

### Step 1: Start the Backend (Terminal 1)

1. Open a terminal/PowerShell window
2. Navigate to the backend directory:
   ```powershell
   cd C:\Users\safat\Desktop\Ragard\backend
   ```
3. Create a Python virtual environment:
   ```powershell
   python -m venv venv
   ```
4. Activate the virtual environment:
   ```powershell
   .\venv\Scripts\Activate.ps1
   ```
   (If you get an error, try: `venv\Scripts\activate.bat`)
5. Install dependencies:
   ```powershell
   pip install -r requirements.txt
   ```
6. Start the backend server:
   ```powershell
   uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
   ```
   
   You should see: `Uvicorn running on http://0.0.0.0:8000`

### Step 2: Start the Frontend (Terminal 2)

1. Open a **new** terminal/PowerShell window
2. Navigate to the frontend directory:
   ```powershell
   cd C:\Users\safat\Desktop\Ragard\frontend
   ```
3. Install dependencies (only needed the first time):
   ```powershell
   npm install
   ```
4. Start the frontend development server:
   ```powershell
   npm run dev
   ```
   
   You should see: `- Local: http://localhost:3000`

### Step 3: Open the Web App

Once both servers are running:
- **Open your browser** and go to: **http://localhost:3000**
- You should see the Ragard dashboard with trending stocks!

### What You'll See

- **Dashboard page** (`/`) - Shows a table of trending stocks
- **Ticker detail pages** (`/ticker/[symbol]`) - Click any stock symbol to see details
- All data comes from real market data sources (yfinance, Reddit, etc.)

### Troubleshooting

- **Backend won't start?** Make sure Python 3.10+ is installed and the virtual environment is activated
- **Frontend won't start?** Make sure Node.js 18+ and npm are installed
- **Can't see data?** Make sure the backend is running on port 8000 before starting the frontend
- **CORS errors?** Ensure the backend is running and accessible at `http://localhost:8000`

