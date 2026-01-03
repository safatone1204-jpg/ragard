# Production Deployment Guide

This guide covers deploying Ragard to production.

## Prerequisites

- Docker and Docker Compose installed
- Domain name configured
- SSL certificate (Let's Encrypt recommended)
- Supabase project set up
- Environment variables configured

## Environment Variables

### Backend (.env)

```bash
# Required
ENVIRONMENT=production
SUPABASE_URL=your_supabase_url
SUPABASE_ANON_KEY=your_anon_key
SUPABASE_SERVICE_ROLE_KEY=your_service_role_key

# CORS - Set your production frontend URL
CORS_ORIGINS=https://yourdomain.com,https://www.yourdomain.com

# Optional but recommended
REDDIT_CLIENT_ID=your_reddit_client_id
REDDIT_CLIENT_SECRET=your_reddit_secret
OPENAI_API_KEY=your_openai_key
```

### Frontend (.env.local)

```bash
NEXT_PUBLIC_API_BASE_URL=https://api.yourdomain.com
NEXT_PUBLIC_SUPABASE_URL=your_supabase_url
NEXT_PUBLIC_SUPABASE_ANON_KEY=your_anon_key
```

## Docker Deployment

### Build and Run

```bash
# Build images
docker-compose -f docker-compose.prod.yml build

# Run in detached mode
docker-compose -f docker-compose.prod.yml up -d

# View logs
docker-compose -f docker-compose.prod.yml logs -f
```

## Reverse Proxy Setup (Nginx)

Example Nginx configuration:

```nginx
# Backend API
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

# Frontend
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

## SSL Certificate (Let's Encrypt)

```bash
# Install certbot
sudo apt-get install certbot python3-certbot-nginx

# Obtain certificate
sudo certbot --nginx -d yourdomain.com -d www.yourdomain.com -d api.yourdomain.com
```

## Database Migrations

Run Supabase migrations in the Supabase SQL Editor:

1. `supabase_schema_user_regard.sql`
2. `supabase_schema_watchlists_saved_analyses.sql`
3. `CREATE_USER_REGARD_TABLES.sql`
4. Any migration files in `migrations/`

## Monitoring

### Health Checks

- Backend: `https://api.yourdomain.com/health`
- Frontend: `https://yourdomain.com`

### Logs

```bash
# Backend logs
docker-compose logs -f backend

# Frontend logs
docker-compose logs -f frontend
```

## Security Checklist

- [ ] CORS origins configured correctly
- [ ] Environment variables set
- [ ] SSL certificates installed
- [ ] Rate limiting enabled
- [ ] Database credentials secured
- [ ] API keys not exposed in code
- [ ] Error tracking configured (optional but recommended)

## Scaling

For higher traffic:

1. Use a load balancer (e.g., AWS ALB, Cloudflare)
2. Scale backend containers: `docker-compose up -d --scale backend=3`
3. Use a managed database (PostgreSQL) instead of SQLite
4. Add Redis for caching
5. Use CDN for static assets

## Backup Strategy

1. **Database**: Regular Supabase backups (automatic)
2. **SQLite**: Backup `ragard.db` regularly if using SQLite
3. **Environment**: Store `.env` files securely (use secrets management)

## Troubleshooting

### Backend won't start
- Check environment variables
- Verify database connection
- Check logs: `docker-compose logs backend`

### Frontend build fails
- Verify `NEXT_PUBLIC_API_BASE_URL` is set
- Check Node.js version (18+)
- Clear `.next` directory and rebuild

### CORS errors
- Verify `CORS_ORIGINS` includes your frontend domain
- Check that `ENVIRONMENT=production` is set

