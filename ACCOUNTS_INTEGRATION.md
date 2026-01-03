# Accounts Integration Summary

This document summarizes the Supabase authentication integration into the Ragard frontend.

## Frontend Supabase Client

**Location:** `frontend/lib/supabaseClient.ts`

- Exports a single `supabase` client instance
- Uses `NEXT_PUBLIC_SUPABASE_URL` and `NEXT_PUBLIC_SUPABASE_ANON_KEY` environment variables
- Falls back to hardcoded values if env vars are not set (for development)
- Safe to use on the client side (uses anon key, not service role key)

## Auth State Management

**Location:** `frontend/contexts/AuthContext.tsx`

- Uses React Context API for global auth state
- Provides `AuthProvider` component that wraps the app (in `app/layout.tsx`)
- Exports `useAuth()` hook for components to access auth state
- Auth state includes:
  - `isLoggedIn: boolean`
  - `user: { id: string; email: string | null } | null`
  - `loading: boolean` (initial auth check)
  - `setUser()` and `setIsLoggedIn()` for updating state

**Initial Auth Check:**
- On app startup, checks for stored token in localStorage
- If token exists, validates it by calling `/api/me`
- If valid, sets user state; if invalid, clears token

## Token Storage

**Location:** `frontend/lib/authStorage.ts`

- Uses `localStorage` for web app (Chrome extension would use `chrome.storage`)
- Functions:
  - `saveAccessToken(token)` - Stores Supabase access token
  - `getAccessToken()` - Retrieves stored token
  - `clearAccessToken()` - Removes token and user data
  - `saveUser(user)` / `getUser()` - Helper for user data

## Auth Helper Functions

**Location:** `frontend/lib/authClient.ts`

- `signUp(email, password)` - Creates new account via Supabase
- `signIn(email, password)` - Authenticates existing user
- `signOut()` - Logs out and clears local state
- All functions save/clear tokens automatically
- Returns `{ user, error }` response format

## API Wrapper

**Location:** `frontend/lib/api.ts`

- `callRagardAPI(path, options)` - Central API helper function
- Automatically includes `Authorization: Bearer <token>` header if token exists
- Handles 401 responses by clearing token and dispatching `auth:unauthorized` event
- All authenticated API calls should use this function

## Accounts Tab Behavior

**Location:** `frontend/app/account/page.tsx`

### Logged-Out Mode

- Shows toggle between "Log In" and "Sign Up" tabs
- Form with email and password inputs
- Submit button calls `signIn()` or `signUp()` based on mode
- Shows error messages for failed attempts
- Shows success message on successful login/signup
- After successful auth, fetches user info from `/api/me` and updates global state

### Logged-In Mode

- Displays user email and ID
- Shows message: "Your watchlists and saved analyses are now tied to this account."
- "Log Out" button that calls `signOut()` and clears auth state

## Homepage Watchlist Behavior

**Location:** `frontend/components/Watchlist.tsx`

### Logged-Out State

- Shows message: "Log in to use personalized watchlists."
- Subtext: "Watchlists are only available when you're signed in."
- Button: "Go to Account to log in" (navigates to `/account`)
- All watchlist functionality is disabled/hidden

### Logged-In State

- Fully functional watchlist UI
- On mount:
  - Calls `GET /api/watchlists` to fetch user's watchlists
  - If no watchlists exist, creates default "My Watchlist"
  - Uses first watchlist as the active one
- Add symbol form:
  - Validates symbol exists via `fetchStockProfile()`
  - Calls `POST /api/watchlists/:id/items` to add ticker
  - Updates local state with new item
- Remove functionality:
  - Calls `DELETE /api/watchlists/:id/items/:itemId`
  - Updates local state to remove item
- Displays watchlist items in a table with:
  - Symbol, Name, Price, Change, Regard Score
  - Remove button for each item

## Watchlist API Functions

**Location:** `frontend/lib/watchlistAPI.ts`

- `fetchWatchlists()` - Get all user's watchlists
- `createWatchlist(name)` - Create new watchlist
- `deleteWatchlist(id)` - Delete a watchlist
- `addWatchlistItem(watchlistId, ticker)` - Add ticker to watchlist
- `removeWatchlistItem(watchlistId, itemId)` - Remove ticker from watchlist
- All functions use `callRagardAPI()` which includes auth token automatically

## Environment Variables

Add to `.env.local` or set in deployment:

```
NEXT_PUBLIC_SUPABASE_URL=https://gyaqeaehpehbrrlrdsvz.supabase.co
NEXT_PUBLIC_SUPABASE_ANON_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

## Security Notes

- Access tokens are stored in localStorage (client-side)
- Tokens are automatically included in API requests via `callRagardAPI()`
- 401 responses trigger automatic logout
- Service role key is never used on the client (only anon key)

## Backend Endpoints Used

- `GET /api/me` - Get current user info
- `GET /api/watchlists` - List user's watchlists
- `POST /api/watchlists` - Create watchlist
- `DELETE /api/watchlists/:id` - Delete watchlist
- `GET /api/watchlists/:id/items` - Get items for a watchlist
- `POST /api/watchlists/:id/items` - Add ticker to watchlist
- `DELETE /api/watchlists/:id/items/:itemId` - Remove ticker from watchlist

## Known Limitations

- Currently uses first watchlist as default (no watchlist selection UI yet)
- Chrome extension would need to use `chrome.storage` instead of `localStorage` (not yet implemented)

