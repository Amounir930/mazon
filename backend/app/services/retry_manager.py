"""
Smart retry logic with LLM feedback
"""
import asyncio
from typing import Any, Callable, Awaitable
from loguru import logger

class RetryManager:
    """Smart retry logic with LLM feedback"""

    def __init__(self, max_retries: int = 2, base_delay: float = 1.0):
        self.max_retries = max_retries
        self.base_delay = base_delay

    async def execute_with_retry(self, operation: Callable[..., Awaitable[Any]], *args,
                               validation_func: Callable[[Any], tuple[bool, str]] = None, **kwargs) -> Any:
        """
        Execute operation with retry on validation failure.
        operation: async callable that returns raw_result
        validation_func: callable(raw_result) -> (bool, feedback_str)
        """
        last_error = None
        feedback_history = []

        for attempt in range(self.max_retries + 1):
            try:
                result = await operation(*args, **kwargs)

                # Validate if validator provided
                if validation_func:
                    is_valid, feedback = validation_func(result)
                    if not is_valid and attempt < self.max_retries:
                        feedback_history.append(feedback)
                        # Add feedback to kwargs for next attempt
                        kwargs['learned_fields'] = feedback_history
                        logger.info(f"Retry {attempt + 1}/{self.max_retries}: {feedback}")
                        await asyncio.sleep(self.base_delay * (attempt + 1))
                        continue

                return result

            except Exception as e:
                last_error = e
                logger.warning(f"Attempt {attempt + 1} failed: {e}")
                if attempt == self.max_retries:
                    break
                await asyncio.sleep(self.base_delay * (attempt + 1))

        raise last_error or ValueError("Operation failed after retries")