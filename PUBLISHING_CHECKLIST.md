# Publishing Checklist - Manual Steps

This is your step-by-step guide to publish Ragard to production.

## Prerequisites Checklist

- [ ] Domain name purchased and DNS configured
- [ ] Server/hosting provider chosen (VPS, AWS, DigitalOcean, etc.)
- [ ] Supabase project created and configured
- [ ] All API keys obtained (OpenAI, Reddit, etc.)

---

## Step 1: Supabase Database Setup ✅ (You've done this)

- [x] Supabase project created
- [x] Database migrations applied (user_trades, watchlists, etc.)
- [x] Supabase credentials obtained

**Status**: ✅ Already completed based on your earlier setup

---

## Step 2: Environment Variables Configuration

### 2.1 Backend Environment (`backend/.env`)

Edit `backend/.env` and set:

```bash
# REQUIRED - Change this to production
ENVIRONMENT=production

# REQUIRED - Your Supabase credentials (you already have these)
SUPABASE_URL=https://gyaqeaehpehbrrlrdsvz.supabase.co
SUPABASE_ANON_KEY=your_anon_key_here
SUPABASE_SERVICE_ROLE_KEY=your_service_role_key_here

# REQUIRED - Set to your production domain(s)
CORS_ORIGINS=https://yourdomain.com,https://www.yourdomain.com

# OPTIONAL but recommended
OPENAI_API_KEY=your_openai_key
REDDIT_CLIENT_ID=your_reddit_client_id
REDDIT_CLIENT_SECRET=your_reddit_secret
```

**Action Items:**
- [ ] Change `ENVIRONMENT=development` to `ENVIRONMENT=production`
- [ ] Update `CORS_ORIGINS` with your actual production domain(s)
- [ ] Verify all Supabase keys are correct
- [ ] Add OpenAI API key (if using AI features)
- [ ] Add Reddit credentials (if using Reddit API)

### 2.2 Frontend Environment (`frontend/.env.local`)

Edit `frontend/.env.local` and set:

```bash
# REQUIRED - Your production API URL
NEXT_PUBLIC_API_BASE_URL=https://api.yourdomain.com

# REQUIRED - Same as backend
NEXT_PUBLIC_SUPABASE_URL=https://gyaqeaehpehbrrlrdsvz.supabase.co
NEXT_PUBLIC_SUPABASE_ANON_KEY=your_anon_key_here
```

**Action Items:**
- [ ] Change `NEXT_PUBLIC_API_BASE_URL` from `http://localhost:8000` to your production API URL
- [ ] Verify Supabase URLs match backend

---

## Step 3: Choose Deployment Method

### Option A: Docker Deployment (Recommended)

**Best for**: VPS, dedicated servers, cloud providers

**Requirements:**
- Docker and Docker Compose installed on server
- Domain DNS pointing to server IP

**Steps:**
1. Copy your project to the server
2. Set up environment variables on server
3. Build and run with Docker Compose

### Option B: Platform-as-a-Service (Easier)

**Best for**: Quick deployment, managed infrastructure

**Options:**
- **Vercel** (Frontend) + **Railway/Render** (Backend)
- **Netlify** (Frontend) + **Fly.io** (Backend)
- **AWS Amplify** (Frontend) + **AWS ECS/Lambda** (Backend)

### Option C: Traditional Server

**Best for**: Full control, custom setup

**Requirements:**
- Linux server (Ubuntu recommended)
- Nginx or Apache
- Node.js 18+ and Python 3.11+
- PM2 or systemd for process management

---

## Step 4: Deploy Backend

### If Using Docker:

```bash
# On your server
cd /path/to/ragard
docker-compose -f docker-compose.prod.yml build
docker-compose -f docker-compose.prod.yml up -d

# Check logs
docker-compose -f docker-compose.prod.yml logs -f
```

### If Using Platform (Railway/Render/Fly.io):

1. Connect your GitHub repo
2. Set environment variables in platform dashboard
3. Platform will auto-deploy
4. Get the deployment URL (e.g., `https://ragard-api.railway.app`)

### If Using Traditional Server:

```bash
# Install dependencies
cd backend
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Run with production server
uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 4
```

**Action Items:**
- [ ] Backend deployed and accessible
- [ ] Test `/health` endpoint: `https://api.yourdomain.com/health`
- [ ] Verify no SQLite errors (should use Supabase)

---

## Step 5: Deploy Frontend

### If Using Docker:

```bash
# Already included in docker-compose.prod.yml
# Frontend will build and run automatically
```

### If Using Vercel/Netlify:

1. Connect GitHub repo
2. Set build command: `cd frontend && npm install && npm run build`
3. Set output directory: `frontend/.next`
4. Add environment variables in platform dashboard
5. Deploy

### If Using Traditional Server:

```bash
cd frontend
npm install
npm run build
npm start  # Runs on port 3000
```

**Action Items:**
- [ ] Frontend deployed and accessible
- [ ] Test homepage: `https://yourdomain.com`
- [ ] Verify API calls work (check browser console)

---

## Step 6: Configure Reverse Proxy & SSL

### 6.1 DNS Configuration

Point your domain to your server:
- `yourdomain.com` → Server IP
- `api.yourdomain.com` → Server IP (or separate backend server)

### 6.2 Nginx Setup (if using traditional server)

Create Nginx config files:

**Backend** (`/etc/nginx/sites-available/api.yourdomain.com`):
```nginx
server {
    listen 80;
    server_name api.yourdomain.com;
    
    location / {
        proxy_pass http://localhost:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

**Frontend** (`/etc/nginx/sites-available/yourdomain.com`):
```nginx
server {
    listen 80;
    server_name yourdomain.com www.yourdomain.com;
    
    location / {
        proxy_pass http://localhost:3000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

### 6.3 SSL Certificate (Let's Encrypt)

```bash
# Install certbot
sudo apt-get install certbot python3-certbot-nginx

# Get certificates
sudo certbot --nginx -d yourdomain.com -d www.yourdomain.com -d api.yourdomain.com
```

**Action Items:**
- [ ] DNS configured and propagated
- [ ] Nginx/Apache configured
- [ ] SSL certificates installed
- [ ] HTTPS working on both frontend and backend

---

## Step 7: Update Extension Configuration

After deployment, update the Chrome extension:

1. Open extension options page
2. Set **API Base URL** to: `https://api.yourdomain.com`
3. Set **Web App Base URL** to: `https://yourdomain.com`
4. Click "Test Connection" to verify
5. Save settings

**Action Items:**
- [ ] Extension configured with production URLs
- [ ] Test connection successful
- [ ] Extension works with production backend

---

## Step 8: Final Verification

### 8.1 Backend Checks

```bash
# Health check
curl https://api.yourdomain.com/health

# Should return: {"status":"healthy",...}
```

### 8.2 Frontend Checks

- [ ] Homepage loads: `https://yourdomain.com`
- [ ] No console errors
- [ ] API calls work (check Network tab)
- [ ] Authentication works (Supabase login)

### 8.3 Extension Checks

- [ ] Extension connects to production API
- [ ] Analysis features work
- [ ] No CORS errors

### 8.4 Security Checks

- [ ] HTTPS enforced
- [ ] Environment variables not exposed
- [ ] CORS configured correctly
- [ ] No SQLite in production (check logs)

---

## Step 9: Monitoring & Maintenance

### Set Up Monitoring

- [ ] Health check monitoring (UptimeRobot, Pingdom)
- [ ] Error tracking (Sentry - optional)
- [ ] Log aggregation (if needed)

### Backup Strategy

- [ ] Supabase backups enabled (automatic)
- [ ] Environment variables backed up securely
- [ ] Code in version control (GitHub)

---

## Quick Reference: Deployment Commands

### Local Testing Before Deploy

```powershell
# Verify everything works
cd C:\Users\safat\Desktop\Ragard
powershell -ExecutionPolicy Bypass -File scripts\verify.ps1

# Test backend
cd backend
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# Test frontend
cd frontend
npm run dev
```

### Production Deployment (Docker)

```bash
# Build
docker-compose -f docker-compose.prod.yml build

# Deploy
docker-compose -f docker-compose.prod.yml up -d

# View logs
docker-compose -f docker-compose.prod.yml logs -f

# Stop
docker-compose -f docker-compose.prod.yml down
```

---

## Common Issues & Solutions

### Backend won't start
- Check `ENVIRONMENT=production` is set
- Verify all required env vars are present
- Check logs: `docker-compose logs backend`

### CORS errors
- Verify `CORS_ORIGINS` includes your frontend domain
- Check that `ENVIRONMENT=production` is set
- Ensure frontend URL matches exactly (including https://)

### Frontend can't connect to backend
- Verify `NEXT_PUBLIC_API_BASE_URL` is correct
- Check backend is running and accessible
- Test backend URL directly in browser

### Extension connection fails
- Update extension options with production URLs
- Verify backend `/health` endpoint is accessible
- Check CORS allows extension origin

---

## Next Steps After Publishing

1. **Test thoroughly** - Use the site as a real user
2. **Monitor logs** - Watch for errors
3. **Set up alerts** - Get notified of issues
4. **Plan scaling** - If traffic grows, consider:
   - Load balancer
   - CDN for static assets
   - Database connection pooling
   - Caching layer (Redis)

---

## Need Help?

- Check `DEPLOYMENT.md` for detailed deployment guide
- Check `TROUBLESHOOTING.md` for common issues
- Review `PRODUCTION_READINESS_SUMMARY.md` for all changes made

