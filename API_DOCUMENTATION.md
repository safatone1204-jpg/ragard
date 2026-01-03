# Ragard API Documentation

## Base URL

- **Development**: `http://localhost:8000`
- **Production**: `https://api.yourdomain.com`

## Authentication

Most endpoints require authentication via Bearer token in the Authorization header:

```
Authorization: Bearer <your_supabase_access_token>
```

Get your access token from Supabase Auth after logging in through the frontend.

## Rate Limiting

- **Development**: 1000 requests per minute per IP
- **Production**: 100 requests per minute per IP

Rate limit headers are included in responses:
- `X-RateLimit-Limit`: Maximum requests allowed
- `X-RateLimit-Remaining`: Remaining requests in current window
- `X-RateLimit-Reset`: Time when limit resets

## Endpoints

### Public Endpoints (No Auth Required)

#### Health Check
```
GET /health
```

Returns system health status and dependency checks.

**Response:**
```json
{
  "status": "healthy",
  "timestamp": "2024-01-01T00:00:00Z",
  "checks": {
    "database": "healthy",
    "supabase": "healthy"
  }
}
```

#### Root
```
GET /
```

Returns API information.

**Response:**
```json
{
  "message": "Ragard API",
  "version": "0.1.0",
}
```

### Trending Endpoints

#### Get Trending Tickers
```
GET /api/trending?timeframe=24h
```

**Query Parameters:**
- `timeframe` (optional): `24h`, `7d`, or `30d` (default: `24h`)

**Response:**
```json
[
  {
    "symbol": "TSLA",
    "company_name": "Tesla Inc",
    "price": 250.00,
    "change_pct": 5.2,
    "market_cap": 800000000000,
    "ragard_score": 75,
    "risk_level": "medium"
  }
]
```

### Ticker Endpoints

#### Get Ticker Details
```
GET /api/tickers/{symbol}
```

**Path Parameters:**
- `symbol`: Stock ticker symbol (e.g., "TSLA")

**Response:**
```json
{
  "symbol": "TSLA",
  "company_name": "Tesla Inc",
  "price": 250.00,
  "change_pct": 5.2,
  "market_cap": 800000000000,
  "ragard_score": 75,
  "risk_level": "medium",
  "volume": 50000000,
  "float_shares": 3000000000,
  "exit_liquidity_rating": "high",
  "hype_vs_price_text": "Moderate hype",
  "ragard_label": "Bullish"
}
```

### Stock Profile Endpoints

#### Get Stock Profile
```
GET /api/stocks/{symbol}
```

**Path Parameters:**
- `symbol`: Stock ticker symbol

**Response:**
Comprehensive company profile including:
- Company overview
- Valuation metrics
- Financial health
- SEC filings
- Reddit stats
- Narratives
- Ragard score

### Narratives Endpoints

#### Get Narratives
```
GET /api/narratives?timeframe=24h
```

**Query Parameters:**
- `timeframe` (optional): `24h`, `7d`, or `30d`

### Authentication Endpoints

#### Get Current User
```
GET /api/me
```

**Auth:** Required

**Response:**
```json
{
  "id": "user-uuid",
  "email": "user@example.com",
  "firstName": "John",
  "lastName": "Doe",
  "createdAt": "2024-01-01T00:00:00Z"
}
```

#### Check Auth Status
```
GET /api/auth/status
```

**Auth:** Optional (returns `isAuthenticated: false` if not logged in)

**Response:**
```json
{
  "isAuthenticated": true,
  "userId": "user-uuid",
  "username": "John",
  "email": "user@example.com"
}
```

### Watchlist Endpoints

#### Get Watchlists
```
GET /api/watchlists
```

**Auth:** Required

#### Create Watchlist
```
POST /api/watchlists
```

**Auth:** Required

**Request Body:**
```json
{
  "name": "My Watchlist",
  "tickers": ["TSLA", "AAPL"]
}
```

#### Delete Watchlist
```
DELETE /api/watchlists/{watchlist_id}
```

**Auth:** Required

### Saved Analyses Endpoints

#### Get Saved Analyses
```
GET /api/saved-analyses?ticker=TSLA
```

**Auth:** Required

**Query Parameters:**
- `ticker` (optional): Filter by ticker symbol

#### Create Saved Analysis
```
POST /api/saved-analyses
```

**Auth:** Required

**Request Body:**
```json
{
  "ticker": "TSLA",
  "snapshot": {...},
  "tags": ["analysis", "bullish"],
  "note": "Strong momentum"
}
```

#### Delete Saved Analysis
```
DELETE /api/saved-analyses/{analysis_id}
```

**Auth:** Required

### User Regard Endpoints

#### Get User Regard Score
```
GET /api/user-regard
```

**Auth:** Required

**Response:**
```json
{
  "regardScore": 65,
  "wins": 10,
  "losses": 5,
  "winRate": 0.67,
  "sampleSize": 15,
  "lastUpdated": "2024-01-01T00:00:00Z"
}
```

#### Upload Trade History
```
POST /api/trade-history/upload
```

**Auth:** Required

**Request:** Multipart form data with CSV file

#### Get Upload Progress
```
GET /api/trade-history/progress
```

**Auth:** Required

#### Download User Report
```
GET /api/user-regard/report
```

**Auth:** Required

**Response:** PDF file

### Extension Endpoints

#### Analyze Reddit Post
```
POST /api/extension/analyze-reddit-post
```

**Request Body:**
```json
{
  "url": "https://reddit.com/r/wallstreetbets/...",
  "authorContext": {...}
}
```

#### Resolve Tickers
```
POST /api/extension/resolve-tickers
```

**Request Body:**
```json
{
  "text": "I'm buying $TSLA and $AAPL",
  "url": "https://..."
}
```

## Error Responses

All errors follow this format:

```json
{
  "detail": "Error message here"
}
```

**Status Codes:**
- `200`: Success
- `201`: Created
- `400`: Bad Request
- `401`: Unauthorized
- `404`: Not Found
- `429`: Too Many Requests (rate limited)
- `500`: Internal Server Error
- `503`: Service Unavailable (health check)

## OpenAPI Documentation

Interactive API documentation available at:
- **Swagger UI**: `/docs`
- **ReDoc**: `/redoc`

## Support

For API support, please contact [your support email/contact].

