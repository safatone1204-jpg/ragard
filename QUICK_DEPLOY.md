# Quick Deploy - Get ragardai.com Live Fast

This is the **fastest way** to get your site live. We'll use:
- **Frontend**: Vercel (free, automatic SSL, 5 minutes)
- **Backend**: Railway or Render (free tier, 10 minutes)

---

## Step 1: Prepare Your Code (5 minutes)

### 1.1 Update Environment Variables

**Backend (`backend/.env`):**
```bash
ENVIRONMENT=production
CORS_ORIGINS=https://ragardai.com,https://www.ragardai.com,https://api.ragardai.com
# ... keep your existing Supabase keys
```

**Frontend (`frontend/.env.local`):**
```bash
NEXT_PUBLIC_API_BASE_URL=https://api.ragardai.com
# ... keep your existing Supabase keys
```

### 1.2 Push to GitHub

Make sure your code is on GitHub:
```bash
git add .
git commit -m "Prepare for production deployment"
git push origin main
```

**Action Items:**
- [ ] Environment variables updated
- [ ] Code pushed to GitHub

---

## Step 2: Deploy Frontend to Vercel (5 minutes)

### 2.1 Sign Up / Login

1. Go to [vercel.com](https://vercel.com)
2. Sign up or log in with GitHub

### 2.2 Import Project

1. Click **"Add New..."** → **"Project"**
2. Click **"Import Git Repository"**
3. Select your Ragard repository
4. Click **"Import"**

### 2.3 Configure Project

**Important Settings:**

1. **Root Directory**: Click "Edit" → Set to `frontend`
   - This tells Vercel where your Next.js app is

2. **Framework Preset**: Should auto-detect "Next.js"

3. **Build Command**: Leave as default (`npm run build`)

4. **Output Directory**: Leave as default (`.next`)

5. **Install Command**: Leave as default (`npm install`)

### 2.4 Add Environment Variables

Click **"Environment Variables"** and add:

```
NEXT_PUBLIC_API_BASE_URL = https://api.ragardai.com
NEXT_PUBLIC_SUPABASE_URL = https://gyaqeaehpehbrrlrdsvz.supabase.co
NEXT_PUBLIC_SUPABASE_ANON_KEY = (your anon key)
```

**Important**: 
- Add these for **Production**, **Preview**, and **Development**
- Use the same values for all environments

### 2.5 Deploy

1. Click **"Deploy"**
2. Wait 2-3 minutes for build
3. You'll get a URL like: `ragard-xyz123.vercel.app`

### 2.6 Add Custom Domain

1. In your project, go to **"Settings"** → **"Domains"**
2. Click **"Add Domain"**
3. Enter: `ragardai.com`
4. Click **"Add"**
5. Enter: `www.ragardai.com`
6. Click **"Add"**

Vercel will show you DNS records to add. **Don't add them yet** - we'll do DNS after backend is ready.

**Action Items:**
- [ ] Frontend deployed to Vercel
- [ ] Custom domains added (but not configured yet)

---

## Step 3: Deploy Backend to Railway (10 minutes)

### 3.1 Sign Up / Login

1. Go to [railway.app](https://railway.app)
2. Sign up or log in with GitHub

### 3.2 Create New Project

1. Click **"New Project"**
2. Select **"Deploy from GitHub repo"**
3. Select your Ragard repository
4. Click **"Deploy Now"**

### 3.3 Configure Service

1. Railway will detect it's a Python project
2. Click on the service to configure it

### 3.4 Set Root Directory

1. Click **"Settings"**
2. Scroll to **"Root Directory"**
3. Set to: `backend`
4. Click **"Save"**

### 3.5 Add Environment Variables

1. Go to **"Variables"** tab
2. Click **"New Variable"**
3. Add each of these:

```
ENVIRONMENT = production
SUPABASE_URL = https://gyaqeaehpehbrrlrdsvz.supabase.co
SUPABASE_ANON_KEY = (your anon key)
SUPABASE_SERVICE_ROLE_KEY = (your service role key)
CORS_ORIGINS = https://ragardai.com,https://www.ragardai.com,https://api.ragardai.com
OPENAI_API_KEY = (your openai key - if you have it)
REDDIT_CLIENT_ID = (your reddit client id - if you have it)
REDDIT_CLIENT_SECRET = (your reddit secret - if you have it)
```

### 3.6 Set Start Command

1. Go to **"Settings"**
2. Find **"Start Command"**
3. Set to: `uvicorn app.main:app --host 0.0.0.0 --port $PORT`
4. Click **"Save"**

### 3.7 Deploy

1. Railway will automatically deploy
2. Wait 2-3 minutes
3. You'll get a URL like: `ragard-production.up.railway.app`

### 3.8 Add Custom Domain

1. Go to **"Settings"** → **"Networking"**
2. Click **"Generate Domain"** (this gives you a Railway domain)
3. Click **"Custom Domain"**
4. Enter: `api.ragardai.com`
5. Railway will show you DNS records to add

**Action Items:**
- [ ] Backend deployed to Railway
- [ ] Custom domain `api.ragardai.com` added

---

## Step 4: Configure DNS (5 minutes)

Now you need to add DNS records in your domain registrar (where you bought ragardai.com).

### 4.1 Get DNS Records

**From Vercel:**
1. Go to your Vercel project → **Settings** → **Domains**
2. Click on `ragardai.com`
3. You'll see DNS records like:
   - Type: `A`, Name: `@`, Value: `76.76.21.21`
   - Type: `CNAME`, Name: `www`, Value: `cname.vercel-dns.com`

**From Railway:**
1. Go to Railway project → **Settings** → **Networking**
2. Click on `api.ragardai.com`
3. You'll see a DNS record like:
   - Type: `CNAME`, Name: `api`, Value: `something.railway.app`

### 4.2 Add DNS Records

Go to your domain registrar (GoDaddy, Namecheap, Cloudflare, etc.):

1. Find **DNS Management** or **DNS Settings**
2. Add the records Vercel and Railway provided:

**For ragardai.com (Vercel):**
```
Type: A
Name: @
Value: (IP from Vercel)

Type: CNAME
Name: www
Value: (CNAME from Vercel)
```

**For api.ragardai.com (Railway):**
```
Type: CNAME
Name: api
Value: (CNAME from Railway)
```

### 4.3 Wait for DNS Propagation

- Usually takes 5-30 minutes
- Can take up to 48 hours (rare)
- Check with: `nslookup ragardai.com`

**Action Items:**
- [ ] DNS records added in registrar
- [ ] Wait for propagation (check every 10 minutes)

---

## Step 5: Verify Everything Works

### 5.1 Test Backend

```bash
# In browser or terminal
curl https://api.ragardai.com/health

# Should return: {"status":"healthy",...}
```

Or visit: `https://api.ragardai.com/health` in browser

### 5.2 Test Frontend

Visit: `https://ragardai.com`

**Check:**
- [ ] Homepage loads
- [ ] No console errors
- [ ] API calls work (check Network tab)

### 5.3 Test www

Visit: `https://www.ragardai.com`

**Check:**
- [ ] Loads correctly (should redirect or load same as ragardai.com)

---

## Step 6: Update Chrome Extension

1. Open Chrome: `chrome://extensions/`
2. Find Ragard extension → Click **"Options"**
3. Set **API Base URL**: `https://api.ragardai.com`
4. Set **Web App Base URL**: `https://ragardai.com`
5. Click **"Test Connection"**
6. Click **"Save Settings"**

---

## Troubleshooting

### DNS Not Working

**Wait longer**: DNS can take up to 48 hours (usually 5-30 minutes)

**Check DNS:**
```bash
# Windows
nslookup ragardai.com
nslookup api.ragardai.com

# Should show your server IPs
```

### Frontend Shows Error

**Check:**
- Environment variables are set in Vercel
- `NEXT_PUBLIC_API_BASE_URL` is correct
- Browser console for errors

### Backend Not Responding

**Check:**
- Railway deployment is running (green status)
- Environment variables are set
- Check Railway logs for errors

### CORS Errors

**Fix:**
- Verify `CORS_ORIGINS` includes `https://ragardai.com` and `https://www.ragardai.com`
- Check `ENVIRONMENT=production` is set

---

## Alternative: Render Instead of Railway

If Railway doesn't work, use Render:

1. Go to [render.com](https://render.com)
2. Sign up with GitHub
3. Click **"New"** → **"Web Service"**
4. Connect your GitHub repo
5. **Root Directory**: `backend`
6. **Build Command**: `pip install -r requirements.txt`
7. **Start Command**: `uvicorn app.main:app --host 0.0.0.0 --port $PORT`
8. Add environment variables (same as Railway)
9. Add custom domain: `api.ragardai.com`

---

## Summary

**Total Time**: ~30 minutes

1. ✅ Update env vars (5 min)
2. ✅ Deploy frontend to Vercel (5 min)
3. ✅ Deploy backend to Railway (10 min)
4. ✅ Configure DNS (5 min)
5. ✅ Wait for DNS (5-30 min)
6. ✅ Test and verify (5 min)

**Your URLs:**
- Frontend: https://ragardai.com
- Backend: https://api.ragardai.com

---

## Need Help?

- **Vercel Docs**: https://vercel.com/docs
- **Railway Docs**: https://docs.railway.app
- **DNS Issues**: Check your domain registrar's DNS documentation

