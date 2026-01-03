"""Progress tracking for long-running tasks."""
import asyncio
import logging
from typing import Dict, Optional
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

# In-memory store for progress: {user_id: ProgressInfo}
_progress_store: Dict[str, 'ProgressInfo'] = {}

# Clean up old progress entries after 5 minutes
CLEANUP_INTERVAL_SECONDS = 300


class ProgressInfo:
    """Progress information for a task."""
    def __init__(self, user_id: str, total_steps: int = 0):
        self.user_id = user_id
        self.current_step: int = 0
        self.total_steps: int = total_steps
        self.percentage: float = 0.0
        self.status: str = "starting"  # starting, parsing, enriching, inserting, analyzing, complete, error
        self.message: str = ""
        self.created_at: datetime = datetime.utcnow()
        self.updated_at: datetime = datetime.utcnow()
        self.error: Optional[str] = None
    
    def update(self, step: int, status: str, message: str = "", error: Optional[str] = None):
        """Update progress."""
        self.current_step = step
        self.status = status
        self.message = message
        self.updated_at = datetime.utcnow()
        self.error = error
        
        if self.total_steps > 0:
            self.percentage = min(100.0, (step / self.total_steps) * 100.0)
        else:
            self.percentage = 0.0
    
    def to_dict(self) -> dict:
        """Convert to dictionary for JSON response."""
        return {
            "user_id": self.user_id,
            "current_step": self.current_step,
            "total_steps": self.total_steps,
            "percentage": round(self.percentage, 1),
            "status": self.status,
            "message": self.message,
            "error": self.error,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
        }


def create_progress(user_id: str, total_steps: int = 0) -> ProgressInfo:
    """Create a new progress tracker for a user."""
    progress = ProgressInfo(user_id, total_steps)
    _progress_store[user_id] = progress
    logger.debug(f"Created progress tracker for user {user_id}: {total_steps} steps")
    return progress


def get_progress(user_id: str) -> Optional[ProgressInfo]:
    """Get progress for a user."""
    return _progress_store.get(user_id)


def update_progress(user_id: str, step: int, status: str, message: str = "", error: Optional[str] = None):
    """Update progress for a user."""
    progress = _progress_store.get(user_id)
    if progress:
        progress.update(step, status, message, error)
        logger.debug(f"Progress for user {user_id}: {step}/{progress.total_steps} ({progress.percentage:.1f}%) - {status}")
    else:
        logger.warning(f"Attempted to update progress for user {user_id} but no progress tracker exists")


def complete_progress(user_id: str, message: str = "Complete"):
    """Mark progress as complete."""
    progress = _progress_store.get(user_id)
    if progress:
        progress.update(progress.total_steps, "complete", message)
        # Schedule cleanup after a delay
        # Use tracked background task for cleanup
        from app.core.background_tasks import create_background_task
        create_background_task(_cleanup_progress_after_delay(user_id))
    else:
        logger.warning(f"Attempted to complete progress for user {user_id} but no progress tracker exists")


def clear_progress(user_id: str):
    """Clear progress for a user."""
    if user_id in _progress_store:
        del _progress_store[user_id]
        logger.debug(f"Cleared progress for user {user_id}")


async def _cleanup_progress_after_delay(user_id: str, delay_seconds: int = 60):
    """Clean up progress entry after a delay."""
    await asyncio.sleep(delay_seconds)
    if user_id in _progress_store:
        del _progress_store[user_id]
        logger.debug(f"Cleaned up progress for user {user_id} after {delay_seconds} seconds")


async def cleanup_old_progress():
    """Periodically clean up old progress entries."""
    while True:
        try:
            now = datetime.utcnow()
            to_remove = []
            
            for user_id, progress in _progress_store.items():
                # Remove entries older than 5 minutes
                if (now - progress.updated_at) > timedelta(seconds=CLEANUP_INTERVAL_SECONDS):
                    to_remove.append(user_id)
            
            for user_id in to_remove:
                del _progress_store[user_id]
                logger.debug(f"Cleaned up old progress for user {user_id}")
            
            await asyncio.sleep(60)  # Check every minute
        except Exception as e:
            logger.error(f"Error in progress cleanup: {e}")
            await asyncio.sleep(60)

