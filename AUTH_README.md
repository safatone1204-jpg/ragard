# Supabase Authentication Integration

This document summarizes the Supabase authentication and user data features integrated into the Ragard backend.

## Environment Variables

The following environment variables must be set in your `.env` file (or environment):

- `SUPABASE_URL` - Your Supabase project URL
- `SUPABASE_ANON_KEY` - Your Supabase anonymous/public key
- `SUPABASE_SERVICE_ROLE_KEY` - Your Supabase service role key (server-side only)

**Important:** Never commit these values to version control. The service role key has full database access and should only be used server-side.

## Supabase Client Module

Location: `backend/app/core/supabase_client.py`

This module provides two Supabase clients:

- `get_supabase_admin()` - Admin client using the service role key (for server-side database operations)
- `get_supabase_auth()` - Auth client using the anon key (for validating user tokens)

Both clients are initialized lazily on first use and cached for subsequent requests.

## Authentication Middleware

Location: `backend/app/core/auth.py`

The `get_current_user()` function:

- Extracts the Bearer token from the `Authorization` header
- Validates the token with Supabase
- Returns an `AuthenticatedUser` object with `id` and `email`
- Raises `HTTPException` (401) if the token is missing or invalid

Usage in endpoints:
```python
from app.core.auth import get_current_user, AuthenticatedUser
from fastapi import Depends

@router.get("/protected")
async def protected_endpoint(
    current_user: AuthenticatedUser = Depends(get_current_user)
):
    # current_user.id and current_user.email are available
    ...
```

## API Endpoints

### Authentication

#### `GET /api/me`
Returns information about the currently authenticated user.

- **Auth:** Required
- **Response:** `{ id: string, email: string | null }`

### Watchlists

#### `GET /api/watchlists`
Get all watchlists for the current user.

- **Auth:** Required
- **Response:** Array of watchlists ordered by `created_at` ASC

#### `POST /api/watchlists`
Create a new watchlist.

- **Auth:** Required
- **Body:** `{ name: string }`
- **Response:** Created watchlist

#### `DELETE /api/watchlists/:id`
Delete a watchlist (and all its items via CASCADE).

- **Auth:** Required
- **Response:** `{ success: true }` or 404 if not found

#### `POST /api/watchlists/:id/items`
Add a ticker to a watchlist.

- **Auth:** Required
- **Body:** `{ ticker: string }`
- **Response:** Created watchlist item

#### `DELETE /api/watchlists/:id/items/:itemId`
Remove a ticker from a watchlist.

- **Auth:** Required
- **Response:** `{ success: true }` or 404 if not found

### Saved Analyses

#### `GET /api/saved-analyses`
Get all saved analyses for the current user.

- **Auth:** Required
- **Query Params:** `ticker` (optional) - Filter by ticker symbol
- **Response:** Array of saved analyses ordered by `created_at` DESC

#### `POST /api/saved-analyses`
Create a new saved analysis.

- **Auth:** Required
- **Body:** 
  ```json
  {
    "ticker": "SGBX",
    "snapshot": { ... },
    "tags": ["meme", "high-regard"],
    "note": "Optional note"
  }
  ```
- **Response:** Created saved analysis

#### `DELETE /api/saved-analyses/:id`
Delete a saved analysis.

- **Auth:** Required
- **Response:** `{ success: true }` or 404 if not found

## Database Schema

Location: `supabase_schema_watchlists_saved_analyses.sql`

This SQL file contains the schema for:
- `watchlists` table
- `watchlist_items` table
- `saved_analyses` table
- Row Level Security (RLS) policies
- Indexes for performance

**Important:** This SQL file must be run manually in the Supabase SQL Editor. Do NOT execute it from the backend code.

## Security Notes

- All endpoints (except `/api/me` which is just informational) require authentication
- The service role key is never exposed to clients
- Row Level Security (RLS) policies ensure users can only access their own data
- All database operations use the admin client server-side, bypassing RLS for efficiency while maintaining security through application-level checks

## Error Handling

- Missing or invalid tokens return HTTP 401
- Missing resources return HTTP 404
- Validation errors return HTTP 400
- Internal errors return HTTP 500 with generic messages (detailed errors are logged server-side only)

