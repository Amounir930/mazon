"""
Background Task Manager
Replaces Celery with asyncio-based task queue
"""
import asyncio
import uuid
from typing import Dict, Any, Optional
from datetime import datetime
from loguru import logger


class TaskManager:
    """Manages background tasks using asyncio"""

    def __init__(self):
        self._tasks: Dict[str, asyncio.Task] = {}
        self._results: Dict[str, dict] = {}
        self._queue: asyncio.Queue = asyncio.Queue()
        self._running = False

    async def start(self):
        """Start the task worker"""
        self._running = True
        logger.info("Task manager started")
        asyncio.create_task(self._worker())

    async def _worker(self):
        """Background worker that processes tasks from queue"""
        while self._running:
            try:
                task_id, coro = await asyncio.wait_for(self._queue.get(), timeout=1.0)
                await self._execute_task(task_id, coro)
                self._queue.task_done()
            except asyncio.TimeoutError:
                continue
            except Exception as e:
                logger.error(f"Worker error: {str(e)}")

    async def _execute_task(self, task_id: str, coro):
        """Execute a single task"""
        try:
            self._results[task_id] = {
                "status": "running",
                "started_at": datetime.utcnow().isoformat(),
            }
            result = await coro
            self._results[task_id] = {
                "status": "completed",
                "result": result,
                "completed_at": datetime.utcnow().isoformat(),
            }
            logger.info(f"Task completed: {task_id}")
        except Exception as e:
            self._results[task_id] = {
                "status": "failed",
                "error": str(e),
                "completed_at": datetime.utcnow().isoformat(),
            }
            logger.error(f"Task failed: {task_id} — {str(e)}")

    async def submit(self, coro) -> str:
        """Submit a task to the queue"""
        task_id = str(uuid.uuid4())
        await self._queue.put((task_id, coro))
        logger.info(f"Task queued: {task_id}")
        return task_id

    def get_status(self, task_id: str) -> Optional[dict]:
        """Get task status"""
        return self._results.get(task_id)

    def list_all(self) -> Dict[str, dict]:
        """List all tasks"""
        return self._results.copy()

    def stop(self):
        """Stop the task worker"""
        self._running = False
        logger.info("Task manager stopped")


# Global instance
task_manager = TaskManager()
