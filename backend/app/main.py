"""FastAPI application entry point."""
import logging
from datetime import datetime
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from contextlib import asynccontextmanager
from slowapi.errors import RateLimitExceeded
from slowapi import _rate_limit_exceeded_handler
from app.core.config import settings, validate_required_env_vars
from app.core.database import init_db, close_db, get_db
from app.core.logging_config import setup_logging
from app.api import trending, tickers, narratives, stocks, extension, reddit, regard_history, auth, watchlists, saved_analyses, user_regard

# Validate required environment variables on startup (fail fast)
validate_required_env_vars()

# Setup structured logging
setup_logging()
logger = logging.getLogger(__name__)

# Initialize Sentry error tracking (if configured)
if settings.SENTRY_DSN:
    try:
        import sentry_sdk
        from sentry_sdk.integrations.fastapi import FastApiIntegration
        from sentry_sdk.integrations.logging import LoggingIntegration
        
        sentry_sdk.init(
            dsn=settings.SENTRY_DSN,
            environment=settings.SENTRY_ENVIRONMENT,
            integrations=[
                FastApiIntegration(),
                LoggingIntegration(level=logging.INFO, event_level=logging.ERROR),
            ],
            traces_sample_rate=0.1 if settings.ENVIRONMENT == "production" else 1.0,
            profiles_sample_rate=0.1 if settings.ENVIRONMENT == "production" else 1.0,
        )
        logger.info("Sentry error tracking initialized")
    except ImportError:
        logger.warning("Sentry SDK not installed. Error tracking disabled.")
    except Exception as e:
        logger.warning(f"Failed to initialize Sentry: {e}")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan context manager for startup and shutdown."""
    # Startup: Initialize database
    await init_db()
    yield
    # Shutdown: Cancel background tasks first, then close database
    import asyncio
    
    try:
        from app.core.background_tasks import cancel_all_background_tasks
        await cancel_all_background_tasks()
    except asyncio.CancelledError:
        # Expected during shutdown - suppress it
        logger.debug("Background task cancellation interrupted during shutdown")
    except Exception as e:
        logger.warning(f"Error during background task cancellation: {e}")
    
    try:
        await close_db()
    except asyncio.CancelledError:
        # Expected during shutdown - suppress it
        logger.debug("Database close interrupted during shutdown")
    except Exception as e:
        logger.warning(f"Error closing database: {e}")

app = FastAPI(
    title="Ragard API",
    description="Meme/small-cap stock analysis API",
    version="0.1.0",
    lifespan=lifespan,
)

# Rate limiting
# Configure rate limiter - shared instance for all routers
try:
    from app.core.rate_limiter import limiter
    from slowapi.errors import RateLimitExceeded
    from slowapi import _rate_limit_exceeded_handler
    
    app.state.limiter = limiter
    app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
except ImportError:
    logger.warning("slowapi not installed. Rate limiting disabled. Install with: pip install slowapi")
    # Create a dummy limiter to prevent errors
    class DummyLimiter:
        def limit(self, *args, **kwargs):
            def decorator(func):
                return func
            return decorator
    app.state.limiter = DummyLimiter()

# Configure CORS
# Environment-aware CORS configuration
# Development: Allow all origins for Chrome extension compatibility
# Production: Restrict to specific origins
if settings.ENVIRONMENT == "production":
    # Production: Use configured origins (must be set in environment)
    # Chrome extensions use chrome-extension:// protocol which requires special handling
    # For production, you should explicitly list allowed origins including your frontend domain
    # Get CORS_ORIGINS as a list (parsed from comma-separated string)
    cors_origins = settings.get_cors_origins_list()
    
    if not cors_origins:
        import logging
        logger = logging.getLogger(__name__)
        logger.warning("CORS_ORIGINS not set in production! API may be inaccessible.")
    app.add_middleware(
        CORSMiddleware,
        allow_origins=cors_origins,
        allow_credentials=True,
        allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
        allow_headers=["*"],
    )
else:
    # Development: Allow all origins for Chrome extension compatibility
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],  # Allow all origins for Chrome extension compatibility
        allow_credentials=False,  # Must be False when allow_origins=["*"]
        allow_methods=["*"],
        allow_headers=["*"],
    )

# Include routers
app.include_router(trending.router)
app.include_router(tickers.router)
app.include_router(narratives.router)
app.include_router(stocks.router)
app.include_router(extension.router)
app.include_router(reddit.router)
app.include_router(regard_history.router)
app.include_router(auth.router)
app.include_router(watchlists.router)
app.include_router(saved_analyses.router)
app.include_router(user_regard.router)


@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "message": "Ragard API",
        "version": "0.1.0",
    }


@app.get("/health")
async def health():
    """
    Health check endpoint with dependency checks.
    Returns 200 if all systems are operational, 503 if any dependency is down.
    """
    health_status = {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "checks": {}
    }
    
    all_healthy = True
    
    # Check database connection
    try:
        db = await get_db()
        await db.execute("SELECT 1")
        health_status["checks"]["database"] = "healthy"
    except Exception as e:
        logger.warning(f"Database health check failed: {e}")
        health_status["checks"]["database"] = "unhealthy"
        all_healthy = False
    
    # Check Supabase connection (if configured)
    if settings.SUPABASE_URL:
        try:
            from app.core.supabase_client import get_supabase_auth
            supabase = get_supabase_auth()
            # Simple check - just verify client is initialized
            if supabase:
                health_status["checks"]["supabase"] = "healthy"
            else:
                health_status["checks"]["supabase"] = "unhealthy"
                all_healthy = False
        except Exception as e:
            logger.warning(f"Supabase health check failed: {e}")
            health_status["checks"]["supabase"] = "unhealthy"
            all_healthy = False
    else:
        health_status["checks"]["supabase"] = "not_configured"
    
    if not all_healthy:
        health_status["status"] = "degraded"
        return JSONResponse(
            status_code=503,
            content=health_status
        )
    
    return health_status


