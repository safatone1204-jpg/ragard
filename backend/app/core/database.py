"""Database configuration and connection management."""
import aiosqlite
import asyncio
import logging
from pathlib import Path
from typing import Optional
from app.core.config import settings

logger = logging.getLogger(__name__)

# Database file path (in backend directory)
# SQLite is only used in development - production should use Supabase/Postgres
BACKEND_DIR = Path(__file__).parent.parent.parent
DB_PATH = BACKEND_DIR / "ragard.db"

# Global database connection (lazy initialization)
_db_connection: Optional[aiosqlite.Connection] = None


async def get_db() -> aiosqlite.Connection:
    """Get or create database connection."""
    global _db_connection
    
    # In production, SQLite should not be used - use Supabase/Postgres instead
    if settings.ENVIRONMENT == "production":
        raise RuntimeError(
            "SQLite database is not available in production. "
            "Please use Supabase/Postgres for production deployments. "
            "Set ENVIRONMENT=development to use SQLite for local development."
        )
    
    if _db_connection is None:
        _db_connection = await aiosqlite.connect(
            str(DB_PATH),
            timeout=30.0,  # Wait up to 30 seconds for locks
            check_same_thread=False  # Allow use from different async contexts
        )
        # Enable WAL mode for better concurrency (allows concurrent reads)
        await _db_connection.execute("PRAGMA journal_mode = WAL")
        # Set busy timeout to prevent locking issues
        await _db_connection.execute("PRAGMA busy_timeout = 30000")  # 30 seconds
        # Enable foreign keys
        await _db_connection.execute("PRAGMA foreign_keys = ON")
        # Set row factory for dict-like access
        _db_connection.row_factory = aiosqlite.Row
        logger.info(f"Connected to database: {DB_PATH}")
    
    # Lightweight health check: verify connection is still valid
    try:
        await asyncio.wait_for(
            _db_connection.execute("SELECT 1"),
            timeout=1.0
        )
    except (asyncio.TimeoutError, Exception) as e:
        # Connection is unhealthy, recreate it
        logger.warning(f"Database connection unhealthy, recreating: {e}")
        try:
            await _db_connection.close()
        except Exception:
            pass
        _db_connection = None
        # Recreate connection
        _db_connection = await aiosqlite.connect(
            str(DB_PATH),
            timeout=30.0,
            check_same_thread=False
        )
        await _db_connection.execute("PRAGMA journal_mode = WAL")
        await _db_connection.execute("PRAGMA busy_timeout = 30000")
        await _db_connection.execute("PRAGMA foreign_keys = ON")
        _db_connection.row_factory = aiosqlite.Row
        logger.info("Database connection recreated after health check failure")
    
    return _db_connection


async def close_db():
    """Close database connection."""
    global _db_connection
    
    if _db_connection is not None:
        try:
            # Wait a moment for any pending operations to complete
            try:
                await asyncio.wait_for(asyncio.sleep(0.1), timeout=0.2)
            except (asyncio.TimeoutError, asyncio.CancelledError):
                # If we're being cancelled, just proceed to close
                pass
            
            await _db_connection.close()
            _db_connection = None
            logger.info("Database connection closed")
        except asyncio.CancelledError:
            # Expected during shutdown - try to close anyway
            logger.debug("Database close was interrupted, attempting immediate close")
            try:
                if _db_connection:
                    await _db_connection.close()
            except Exception:
                pass
            _db_connection = None
        except Exception as e:
            logger.warning(f"Error closing database connection: {e}")
            _db_connection = None


async def init_db():
    """Initialize database tables."""
    db = await get_db()
    
    # Create regard_history table
    await db.execute("""
        CREATE TABLE IF NOT EXISTS regard_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            ticker TEXT NOT NULL,
            timestamp_utc TEXT NOT NULL,
            timestamp_local TEXT NOT NULL,
            window_label TEXT NOT NULL DEFAULT 'current',
            score_raw REAL,
            score_rounded INTEGER,
            scoring_mode TEXT NOT NULL,
            ai_success BOOLEAN NOT NULL,
            total_posts INTEGER DEFAULT 0,
            posts_reddit INTEGER DEFAULT 0,
            posts_twitter INTEGER DEFAULT 0,
            posts_discord INTEGER DEFAULT 0,
            posts_news INTEGER DEFAULT 0,
            low_sample_size BOOLEAN NOT NULL DEFAULT 0,
            is_weekend BOOLEAN NOT NULL DEFAULT 0,
            is_holiday BOOLEAN NOT NULL DEFAULT 0,
            has_data_gap BOOLEAN NOT NULL DEFAULT 0,
            price_at_snapshot REAL,
            change_24h_pct REAL,
            volume_24h REAL,
            market_cap REAL,
            model_version TEXT,
            scoring_version TEXT NOT NULL,
            config_snapshot TEXT,
            forward_return_24h REAL,
            forward_return_3d REAL,
            forward_return_7d REAL,
            created_at TEXT NOT NULL DEFAULT (datetime('now'))
        )
    """)
    
    # Create indexes
    await db.execute("""
        CREATE INDEX IF NOT EXISTS idx_regard_history_ticker_timestamp 
        ON regard_history(ticker, timestamp_utc)
    """)
    
    await db.execute("""
        CREATE INDEX IF NOT EXISTS idx_regard_history_timestamp 
        ON regard_history(timestamp_utc)
    """)
    
    await db.commit()
    logger.info("Database tables initialized")
