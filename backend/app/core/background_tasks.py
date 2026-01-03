"""Background task management for fire-and-forget operations."""
import asyncio
import logging
from typing import Set

logger = logging.getLogger(__name__)

# Track all background tasks
_background_tasks: Set[asyncio.Task] = set()
_shutting_down = False


def create_background_task(coro):
    """
    Create a tracked background task that will be cancelled on shutdown.
    
    Args:
        coro: Coroutine to run in background
    
    Returns:
        asyncio.Task
    """
    global _shutting_down
    
    # Don't create new tasks if we're shutting down
    if _shutting_down:
        logger.debug("Skipping background task creation during shutdown")
        return None
    
    task = asyncio.create_task(coro)
    _background_tasks.add(task)
    
    # Remove task from set when it completes
    def remove_task(task):
        _background_tasks.discard(task)
        # Log if task failed
        try:
            if task.exception():
                logger.debug(f"Background task failed: {task.exception()}")
        except Exception:
            pass
    
    task.add_done_callback(remove_task)
    return task


async def cancel_all_background_tasks():
    """Cancel all tracked background tasks. Called during shutdown."""
    global _shutting_down
    
    _shutting_down = True
    
    if not _background_tasks:
        return
    
    logger.info(f"Cancelling {len(_background_tasks)} background tasks")
    
    # Create a copy to avoid modification during iteration
    tasks_to_cancel = list(_background_tasks)
    
    # Cancel all tasks
    for task in tasks_to_cancel:
        if not task.done():
            try:
                task.cancel()
            except Exception as e:
                logger.debug(f"Error cancelling task: {e}")
    
    # Wait for cancellation to complete (with timeout)
    if tasks_to_cancel:
        try:
            # Use gather with return_exceptions to handle cancellations gracefully
            results = await asyncio.wait_for(
                asyncio.gather(*tasks_to_cancel, return_exceptions=True),
                timeout=1.5  # Reduced timeout to avoid blocking shutdown
            )
            # Log any exceptions that occurred (but ignore CancelledError)
            for i, result in enumerate(results):
                if isinstance(result, Exception) and not isinstance(result, asyncio.CancelledError):
                    logger.debug(f"Background task {i} raised exception: {result}")
        except asyncio.TimeoutError:
            logger.debug("Some background tasks didn't cancel within timeout (continuing shutdown)")
        except asyncio.CancelledError:
            # We're being cancelled ourselves - this is expected during shutdown
            logger.debug("Background task cancellation was interrupted (continuing shutdown)")
            # Still try to cancel remaining tasks
            for task in tasks_to_cancel:
                if not task.done():
                    try:
                        task.cancel()
                    except Exception:
                        pass
        except Exception as e:
            logger.debug(f"Error cancelling background tasks: {e}")
    
    _background_tasks.clear()
    logger.debug("Background task cancellation complete")

