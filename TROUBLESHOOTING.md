# Troubleshooting Guide

## Port Already in Use (EADDRINUSE)

### Error Message
```
Error: listen EADDRINUSE: address already in use :::3000
```

### Solution 1: Find and Kill the Process (Recommended)

**Windows PowerShell:**
```powershell
# Find what's using port 3000
netstat -ano | findstr :3000

# You'll see output like:
# TCP    0.0.0.0:3000           0.0.0.0:0              LISTENING       12345
# The last number (12345) is the Process ID (PID)

# Kill the process (replace 12345 with your actual PID)
taskkill /PID 12345 /F
```

**Windows Command Prompt:**
```cmd
netstat -ano | findstr :3000
taskkill /PID <PID_NUMBER> /F
```

**Linux/Mac:**
```bash
# Find what's using port 3000
lsof -i :3000
# or
sudo netstat -tulpn | grep :3000

# Kill the process (replace PID with actual process ID)
kill -9 <PID>
```

### Solution 2: Use a Different Port

**Option A: Change Next.js port via command line**
```bash
# Use port 3001 instead
npm run dev -- -p 3001

# Or set it in package.json scripts
```

**Option B: Change the port in package.json**

Edit `frontend/package.json`:
```json
{
  "scripts": {
    "dev": "next dev -p 3001"
  }
}
```

**Option C: Use environment variable**
```bash
# Windows PowerShell
$env:PORT=3001; npm run dev

# Linux/Mac
PORT=3001 npm run dev
```

### Solution 3: Quick PowerShell One-Liner (Windows)

```powershell
# Find and kill process on port 3000 in one command
Get-NetTCPConnection -LocalPort 3000 -ErrorAction SilentlyContinue | Select-Object -ExpandProperty OwningProcess | ForEach-Object { Stop-Process -Id $_ -Force }
```

## Other Common Issues

### Backend Port 8000 Already in Use

**Windows:**
```powershell
netstat -ano | findstr :8000
taskkill /PID <PID_NUMBER> /F
```

**Linux/Mac:**
```bash
lsof -i :8000
kill -9 <PID>
```

### Environment Variables Not Loading

1. **Check file location**: Make sure `.env` is in `backend/` and `.env.local` is in `frontend/`
2. **Check file name**: Must be exactly `.env` (not `.env.txt` or `env`)
3. **Restart the server**: Environment variables are loaded on startup
4. **Check for typos**: Variable names are case-sensitive

### Supabase Connection Errors

1. **Verify URL format**: Should be `https://xxxxx.supabase.co` (no trailing slash)
2. **Check key length**: JWT tokens are very long (200+ characters)
3. **Verify project is active**: Check Supabase dashboard
4. **Check network**: Make sure you can access Supabase from your network

### CORS Errors

1. **Check CORS_ORIGINS**: Must include your frontend URL
2. **No spaces in list**: `http://localhost:3000,http://localhost:8000` (no spaces)
3. **Restart backend**: Changes require server restart
4. **Check protocol**: `http://` vs `https://` must match

### Frontend Build Errors

1. **Check env vars**: Run `npm run build` to see validation errors
2. **Clear cache**: `rm -rf .next` (Linux/Mac) or `Remove-Item -Recurse -Force .next` (Windows)
3. **Reinstall dependencies**: `rm -rf node_modules && npm install`

### Extension Not Working

1. **Check backend is running**: Test `http://localhost:8000/health`
2. **Check extension options**: Right-click extension → Options → Test Connection
3. **Check browser console**: Open DevTools (F12) → Console tab
4. **Reload extension**: `chrome://extensions` → Click reload icon

