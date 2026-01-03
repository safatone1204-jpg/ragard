# Monitoring and Observability Setup

This document outlines monitoring configurations for Ragard in production.

## Error Tracking (Sentry)

### Backend Setup

1. Create a Sentry account at https://sentry.io
2. Create a new project (Python/FastAPI)
3. Copy the DSN
4. Add to `backend/.env`:
   ```bash
   SENTRY_DSN=your_sentry_dsn_here
   SENTRY_ENVIRONMENT=production
   ```

### Frontend Setup

1. Create a new project in Sentry (JavaScript/Next.js)
2. Copy the DSN
3. Add to `frontend/.env.local`:
   ```bash
   NEXT_PUBLIC_SENTRY_DSN=your_sentry_dsn_here
   NEXT_PUBLIC_SENTRY_ENVIRONMENT=production
   ```

### Features

- Automatic error capture
- Performance monitoring (10% sample rate in production)
- Release tracking
- User context tracking
- Breadcrumb logging

## Application Performance Monitoring (APM)

### Recommended Services

1. **Sentry Performance** (included with Sentry)
   - Already configured
   - Tracks API response times
   - Identifies slow endpoints

2. **Datadog** (optional, for advanced monitoring)
   - Infrastructure monitoring
   - Custom metrics
   - Log aggregation

3. **New Relic** (alternative)
   - Full-stack observability
   - Real-time monitoring

## Health Checks

### Endpoints

- Backend: `https://api.yourdomain.com/health`
- Frontend: `https://yourdomain.com`

### Monitoring

Set up uptime monitoring with:
- **UptimeRobot** (free tier available)
- **Pingdom**
- **StatusCake**

Configure alerts for:
- HTTP status != 200
- Response time > 5 seconds
- SSL certificate expiration

## Log Aggregation

### Options

1. **Sentry** (errors and performance)
2. **Logtail** (structured logs)
3. **Datadog Logs**
4. **CloudWatch** (if using AWS)

### Log Levels

- **Production**: INFO and above
- **Development**: DEBUG and above

## Metrics to Monitor

### Application Metrics

- API response times (p50, p95, p99)
- Error rate
- Request rate
- Database query performance
- Cache hit rate (when implemented)

### Infrastructure Metrics

- CPU usage
- Memory usage
- Disk I/O
- Network traffic
- Container health

## Alerting

### Critical Alerts

- API down (health check fails)
- Error rate > 5%
- Response time p95 > 2 seconds
- Database connection failures

### Warning Alerts

- Error rate > 1%
- Response time p95 > 1 second
- High memory usage (>80%)
- Disk space < 20%

## Dashboard Setup

### Recommended Dashboards

1. **Error Dashboard**
   - Error count by type
   - Error rate over time
   - Top erroring endpoints

2. **Performance Dashboard**
   - Response time percentiles
   - Request rate
   - Slowest endpoints

3. **Infrastructure Dashboard**
   - Resource utilization
   - Container health
   - Network metrics

## Cost Considerations

- **Sentry**: Free tier (5K events/month)
- **UptimeRobot**: Free tier (50 monitors)
- **Datadog**: Paid (starts at $15/host/month)

For budget-conscious deployments:
- Use Sentry for errors (free tier)
- Use UptimeRobot for uptime monitoring (free)
- Use structured logging to files (free)
- Add paid services as you scale

