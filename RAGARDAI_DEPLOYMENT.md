# Ragard Deployment Guide for ragardai.com

This is your specific deployment guide for **ragardai.com**.

## Domain Setup

**Your Domain**: `ragardai.com`
**Backend API**: `api.ragardai.com` (recommended)
**Frontend**: `ragardai.com` and `www.ragardai.com`

---

## Step 1: DNS Configuration

### 1.1 Add DNS Records

In your domain registrar (where you bought ragardai.com), add these DNS records:

**Option A: Single Server (Backend + Frontend on same server)**
```
Type: A
Name: @
Value: YOUR_SERVER_IP
TTL: 3600

Type: A
Name: www
Value: YOUR_SERVER_IP
TTL: 3600

Type: A
Name: api
Value: YOUR_SERVER_IP
TTL: 3600
```

**Option B: Separate Servers**
```
Type: A
Name: @
Value: FRONTEND_SERVER_IP
TTL: 3600

Type: A
Name: www
Value: FRONTEND_SERVER_IP
TTL: 3600

Type: A
Name: api
Value: BACKEND_SERVER_IP
TTL: 3600
```

**Action Items:**
- [ ] DNS records added in domain registrar
- [ ] Wait for DNS propagation (can take up to 48 hours, usually 1-2 hours)
- [ ] Verify with: `nslookup ragardai.com` and `nslookup api.ragardai.com`

---

## Step 2: Update Environment Variables

### 2.1 Backend Environment (`backend/.env`)

Update your `backend/.env` file:

```bash
# REQUIRED - Set to production
ENVIRONMENT=production

# REQUIRED - Your Supabase credentials (already configured)
SUPABASE_URL=https://gyaqeaehpehbrrlrdsvz.supabase.co
SUPABASE_ANON_KEY=your_anon_key_here
SUPABASE_SERVICE_ROLE_KEY=your_service_role_key_here

# REQUIRED - Your production domains
CORS_ORIGINS=https://ragardai.com,https://www.ragardai.com,https://api.ragardai.com

# OPTIONAL but recommended
OPENAI_API_KEY=your_openai_key
REDDIT_CLIENT_ID=your_reddit_client_id
REDDIT_CLIENT_SECRET=your_reddit_secret
```

**Key Changes:**
- Change `ENVIRONMENT=development` → `ENVIRONMENT=production`
- Update `CORS_ORIGINS` to: `https://ragardai.com,https://www.ragardai.com,https://api.ragardai.com`

### 2.2 Frontend Environment (`frontend/.env.local`)

Update your `frontend/.env.local` file:

```bash
# REQUIRED - Your production API URL
NEXT_PUBLIC_API_BASE_URL=https://api.ragardai.com

# REQUIRED - Same as backend
NEXT_PUBLIC_SUPABASE_URL=https://gyaqeaehpehbrrlrdsvz.supabase.co
NEXT_PUBLIC_SUPABASE_ANON_KEY=your_anon_key_here
```

**Key Changes:**
- Change `NEXT_PUBLIC_API_BASE_URL` from `http://localhost:8000` to `https://api.ragardai.com`

---

## Step 3: Deploy Backend to api.ragardai.com

### Option A: Using Docker (Recommended)

```bash
# On your server
cd /path/to/ragard
docker-compose -f docker-compose.prod.yml build
docker-compose -f docker-compose.prod.yml up -d

# Check it's running
docker-compose -f docker-compose.prod.yml ps
docker-compose -f docker-compose.prod.yml logs -f backend
```

### Option B: Using Platform (Railway/Render/Fly.io)

1. **Railway**:
   - Connect GitHub repo
   - Add environment variables
   - Deploy
   - Get URL (e.g., `ragard-api.railway.app`)
   - Add custom domain: `api.ragardai.com`

2. **Render**:
   - Create new Web Service
   - Connect repo
   - Set environment variables
   - Add custom domain: `api.ragardai.com`

**Action Items:**
- [ ] Backend deployed
- [ ] Test: `https://api.ragardai.com/health` (should return JSON)
- [ ] Verify no errors in logs

---

## Step 4: Deploy Frontend to ragardai.com

### Option A: Using Vercel (Easiest for Next.js)

1. Go to [vercel.com](https://vercel.com)
2. Import your GitHub repo
3. **Root Directory**: Set to `frontend`
4. **Build Command**: `npm run build`
5. **Output Directory**: `.next`
6. **Environment Variables**:
   - `NEXT_PUBLIC_API_BASE_URL=https://api.ragardai.com`
   - `NEXT_PUBLIC_SUPABASE_URL=your_supabase_url`
   - `NEXT_PUBLIC_SUPABASE_ANON_KEY=your_anon_key`
7. Deploy
8. Add custom domain: `ragardai.com` and `www.ragardai.com`

### Option B: Using Docker

```bash
# On your server
cd /path/to/ragard
docker-compose -f docker-compose.prod.yml up -d frontend
```

### Option C: Using Netlify

1. Connect GitHub repo
2. **Base directory**: `frontend`
3. **Build command**: `npm run build`
4. **Publish directory**: `frontend/.next`
5. Add environment variables
6. Add custom domain: `ragardai.com`

**Action Items:**
- [ ] Frontend deployed
- [ ] Test: `https://ragardai.com` (should load homepage)
- [ ] Verify API calls work (check browser console)

---

## Step 5: SSL Certificates

### If Using Vercel/Netlify:
- SSL is automatic! ✅
- They handle certificates automatically

### If Using Your Own Server:

```bash
# Install certbot
sudo apt-get update
sudo apt-get install certbot python3-certbot-nginx

# Get certificates for all domains
sudo certbot --nginx -d ragardai.com -d www.ragardai.com -d api.ragardai.com

# Certbot will automatically configure Nginx
```

**Action Items:**
- [ ] SSL certificates installed
- [ ] Test: `https://ragardai.com` (should show lock icon)
- [ ] Test: `https://api.ragardai.com` (should show lock icon)

---

## Step 6: Nginx Configuration (If Using Your Own Server)

### Backend API (`/etc/nginx/sites-available/api.ragardai.com`)

```nginx
server {
    listen 80;
    server_name api.ragardai.com;
    
    location / {
        proxy_pass http://localhost:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

### Frontend (`/etc/nginx/sites-available/ragardai.com`)

```nginx
server {
    listen 80;
    server_name ragardai.com www.ragardai.com;
    
    location / {
        proxy_pass http://localhost:3000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

**After creating configs:**
```bash
# Enable sites
sudo ln -s /etc/nginx/sites-available/api.ragardai.com /etc/nginx/sites-enabled/
sudo ln -s /etc/nginx/sites-available/ragardai.com /etc/nginx/sites-enabled/

# Test configuration
sudo nginx -t

# Reload Nginx
sudo systemctl reload nginx
```

---

## Step 7: Update Chrome Extension

1. Open Chrome Extensions: `chrome://extensions/`
2. Find Ragard extension → Click "Options"
3. Set **API Base URL**: `https://api.ragardai.com`
4. Set **Web App Base URL**: `https://ragardai.com`
5. Click "Test Connection" (should show success)
6. Click "Save Settings"

**Action Items:**
- [ ] Extension configured with production URLs
- [ ] Test connection successful
- [ ] Extension works with production backend

---

## Step 8: Verification Checklist

### Backend Verification

```bash
# Health check
curl https://api.ragardai.com/health

# Should return:
# {"status":"healthy","database":"connected","supabase":"connected"}
```

**Check:**
- [ ] `https://api.ragardai.com/health` returns healthy status
- [ ] `https://api.ragardai.com/docs` shows API documentation
- [ ] No SQLite errors in logs (should use Supabase)

### Frontend Verification

**Check:**
- [ ] `https://ragardai.com` loads homepage
- [ ] `https://www.ragardai.com` redirects or loads
- [ ] No console errors in browser
- [ ] API calls work (check Network tab)
- [ ] Authentication works (Supabase login)

### Extension Verification

**Check:**
- [ ] Extension connects to `https://api.ragardai.com`
- [ ] Analysis features work
- [ ] No CORS errors in console

### Security Verification

**Check:**
- [ ] HTTPS enforced (no HTTP access)
- [ ] SSL certificates valid (green lock icon)
- [ ] CORS configured correctly
- [ ] Environment variables not exposed in code

---

## Quick Commands Reference

### Check DNS Propagation

```bash
# Windows
nslookup ragardai.com
nslookup api.ragardai.com

# Linux/Mac
dig ragardai.com
dig api.ragardai.com
```

### Test Backend

```bash
# Health check
curl https://api.ragardai.com/health

# API docs
curl https://api.ragardai.com/docs
```

### View Logs (Docker)

```bash
# Backend logs
docker-compose -f docker-compose.prod.yml logs -f backend

# Frontend logs
docker-compose -f docker-compose.prod.yml logs -f frontend
```

---

## Troubleshooting

### DNS Not Working

**Problem**: Domain not resolving
**Solution**: 
- Wait for DNS propagation (up to 48 hours)
- Check DNS records are correct
- Use `nslookup` or `dig` to verify

### CORS Errors

**Problem**: Frontend can't connect to backend
**Solution**:
- Verify `CORS_ORIGINS` includes `https://ragardai.com` and `https://www.ragardai.com`
- Check `ENVIRONMENT=production` is set
- Ensure URLs match exactly (including `https://`)

### SSL Certificate Issues

**Problem**: Certificate not working
**Solution**:
- Verify DNS is pointing to server
- Check certbot logs: `sudo certbot certificates`
- Renew if needed: `sudo certbot renew`

### Backend Won't Start

**Problem**: Backend fails to start
**Solution**:
- Check `ENVIRONMENT=production` is set
- Verify all required env vars are present
- Check logs: `docker-compose logs backend`
- Verify Supabase connection

---

## Next Steps After Deployment

1. **Monitor**: Set up uptime monitoring (UptimeRobot, Pingdom)
2. **Analytics**: Add Google Analytics or similar
3. **Error Tracking**: Set up Sentry (optional)
4. **Backup**: Verify Supabase backups are enabled
5. **Documentation**: Update any public docs with your domain

---

## Your Specific URLs

- **Frontend**: https://ragardai.com
- **Backend API**: https://api.ragardai.com
- **API Docs**: https://api.ragardai.com/docs
- **Health Check**: https://api.ragardai.com/health

---

## Need Help?

- Check `DEPLOYMENT.md` for general deployment guide
- Check `PUBLISHING_CHECKLIST.md` for detailed checklist
- Check `TROUBLESHOOTING.md` for common issues

