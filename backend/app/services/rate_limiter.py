"""
Rate Limiter for Amazon SP-API Listings Items API

Implements Exponential Backoff to handle 429 Too Many Requests errors.
This is REQUIRED by Amazon SP-API to avoid being throttled.

Reference: https://developer-docs.amazon.com/sp-api/docs/rate-limits
"""
import asyncio
import time
from typing import Callable, Any, Optional
from dataclasses import dataclass, field
from loguru import logger


@dataclass
class RateLimitConfig:
    """Configuration for rate limiting"""
    max_retries: int = 5              # Maximum retry attempts
    base_delay: float = 1.0           # Initial delay in seconds
    max_delay: float = 60.0           # Maximum delay in seconds
    multiplier: float = 2.0           # Exponential multiplier
    retry_on_status: list[int] = field(default_factory=lambda: [429, 500, 502, 503, 504])
    # Amazon's rate limits for Listings Items API (approximate):
    # - 20 requests per second
    # - 100 requests per 5 minutes per marketplace
    burst_limit: int = 15             # Max requests before adding delay
    burst_window: float = 1.0         # Time window for burst limit (seconds)


@dataclass
class RateLimitStats:
    """Statistics about rate limiting"""
    total_requests: int = 0
    successful_requests: int = 0
    throttled_requests: int = 0
    failed_requests: int = 0
    total_retries: int = 0
    total_wait_time: float = 0.0
    last_throttle_time: Optional[float] = None

    @property
    def throttle_rate(self) -> float:
        if self.total_requests == 0:
            return 0.0
        return (self.throttled_requests / self.total_requests) * 100

    @property
    def success_rate(self) -> float:
        if self.total_requests == 0:
            return 0.0
        return (self.successful_requests / self.total_requests) * 100


class ExponentialBackoff:
    """
    Exponential Backoff calculator.
    
    Calculates delays using the formula:
        delay = min(base_delay * (multiplier ^ attempt), max_delay)
    
    Example with base=1s, multiplier=2, max=60s:
        Attempt 0: 1s
        Attempt 1: 2s
        Attempt 2: 4s
        Attempt 3: 8s
        Attempt 4: 16s
        Attempt 5: 32s (capped at 60s)
    """

    @staticmethod
    def calculate_delay(attempt: int, config: RateLimitConfig) -> float:
        """Calculate delay for a given attempt number"""
        delay = config.base_delay * (config.multiplier ** attempt)
        return min(delay, config.max_delay)

    @staticmethod
    def add_jitter(delay: float) -> float:
        """
        Add randomized jitter to avoid thundering herd problem.
        Amazon recommends adding 0-1000ms of random jitter.
        """
        import random
        jitter = random.uniform(0, 1.0)  # 0-1 second jitter
        return delay + jitter


class RateLimitedClient:
    """
    HTTP client wrapper with built-in rate limiting and exponential backoff.
    
    Usage:
        client = RateLimitedClient()
        
        # Wrap any async function call with rate limiting
        result = await client.execute(
            lambda: api_client.put_listing(sku, payload),
            context=f"PUT listing {sku}"
        )
    """

    def __init__(self, config: Optional[RateLimitConfig] = None):
        self.config = config or RateLimitConfig()
        self.stats = RateLimitStats()
        self._request_timestamps: list[float] = []

    async def execute(
        self,
        func: Callable,
        context: str = "API call",
        *args,
        **kwargs
    ) -> Any:
        """
        Execute an async function with exponential backoff retry logic.
        
        Args:
            func: Async function to execute
            context: Description for logging (e.g., "PUT listing SKU-123")
            *args, **kwargs: Arguments to pass to func
        
        Returns:
            The result of func()
        
        Raises:
            Exception: After max retries exceeded
        """
        last_error = None
        
        for attempt in range(self.config.max_retries + 1):
            self.stats.total_requests += 1

            # Check burst rate limit before making request
            await self._check_burst_limit()

            try:
                # Execute the actual API call
                result = await func(*args, **kwargs)
                
                self.stats.successful_requests += 1
                if attempt > 0:
                    logger.info(f"{context} succeeded after {attempt} retries")
                return result

            except Exception as e:
                last_error = e
                status_code = getattr(e, 'status_code', None) or getattr(e, 'response', None)
                
                if hasattr(status_code, 'status_code'):
                    status_code = status_code.status_code
                elif status_code is None:
                    status_code = 0  # Unknown

                # Check if this is a retryable error
                if status_code in self.config.retry_on_status:
                    self.stats.throttled_requests += 1
                    self.stats.total_retries += 1
                    
                    if attempt < self.config.max_retries:
                        # Calculate delay with exponential backoff + jitter
                        delay = ExponentialBackoff.calculate_delay(attempt, self.config)
                        delay = ExponentialBackoff.add_jitter(delay)
                        
                        self.stats.total_wait_time += delay
                        self.stats.last_throttle_time = time.time()

                        logger.warning(
                            f"{context} throttled (attempt {attempt + 1}/{self.config.max_retries}) "
                            f"- waiting {delay:.1f}s before retry "
                            f"(HTTP {status_code})"
                        )
                        
                        await asyncio.sleep(delay)
                    else:
                        logger.error(
                            f"{context} failed after {self.config.max_retries} retries "
                            f"(HTTP {status_code})"
                        )
                        self.stats.failed_requests += 1
                        raise Exception(
                            f"{context} failed after {self.config.max_retries} retries: {e}"
                        ) from e
                else:
                    # Non-retryable error (400, 401, 403, etc.) - fail immediately
                    self.stats.failed_requests += 1
                    logger.error(f"{context} failed with non-retryable error (HTTP {status_code}): {e}")
                    raise

        # Should never reach here, but just in case
        self.stats.failed_requests += 1
        raise last_error

    async def execute_batch(
        self,
        items: list[Any],
        process_func: Callable,
        context: str = "batch",
        concurrency: int = 1,
        delay_between_items: float = 0.1,
    ) -> dict:
        """
        Process a batch of items with rate limiting.
        
        Args:
            items: List of items to process
            process_func: Async function to process each item (receives item as arg)
            context: Description for logging
            concurrency: Number of concurrent requests (keep low to avoid throttling)
            delay_between_items: Delay between each item (seconds)
        
        Returns:
            dict with "successful", "failed", "results" keys
        """
        results = []
        successful = 0
        failed = 0
        
        logger.info(f"Processing {len(items)} items in batch ({context})")
        
        for i, item in enumerate(items):
            try:
                result = await self.execute(
                    lambda item=item: process_func(item),
                    context=f"{context} item {i + 1}/{len(items)}"
                )
                results.append({"item": item, "result": result, "success": True})
                successful += 1
                
                # Add delay between items to avoid hitting rate limits
                if i < len(items) - 1:
                    await asyncio.sleep(delay_between_items)
                    
            except Exception as e:
                logger.error(f"Failed to process {context} item {i + 1}: {e}")
                results.append({"item": item, "error": str(e), "success": False})
                failed += 1
        
        summary = {
            "total": len(items),
            "successful": successful,
            "failed": failed,
            "results": results,
            "rate_limit_stats": {
                "throttle_rate": self.stats.throttle_rate,
                "success_rate": self.stats.success_rate,
                "total_retries": self.stats.total_retries,
                "total_wait_time": f"{self.stats.total_wait_time:.1f}s",
            }
        }
        
        logger.info(
            f"Batch {context} complete: {successful}/{len(items)} successful, "
            f"{failed} failed, {self.stats.total_retries} retries, "
            f"throttle rate: {self.stats.throttle_rate:.1f}%"
        )
        
        return summary

    async def _check_burst_limit(self):
        """
        Check if we're hitting the burst rate limit.
        If so, add an artificial delay to avoid 429 errors.
        """
        now = time.time()
        
        # Remove old timestamps outside the window
        self._request_timestamps = [
            ts for ts in self._request_timestamps
            if now - ts < self.config.burst_window
        ]
        
        # If we're at the burst limit, add delay
        if len(self._request_timestamps) >= self.config.burst_limit:
            delay = 1.0  # Wait 1 second before next request
            logger.debug(f"Burst rate limit reached, waiting {delay}s")
            await asyncio.sleep(delay)
            self._request_timestamps.clear()
        
        self._request_timestamps.append(now)

    def get_stats(self) -> dict:
        """Get current rate limiting statistics"""
        return {
            "total_requests": self.stats.total_requests,
            "successful_requests": self.stats.successful_requests,
            "throttled_requests": self.stats.throttled_requests,
            "failed_requests": self.stats.failed_requests,
            "total_retries": self.stats.total_retries,
            "total_wait_time_seconds": round(self.stats.total_wait_time, 2),
            "throttle_rate_percent": round(self.stats.throttle_rate, 2),
            "success_rate_percent": round(self.stats.success_rate, 2),
        }

    def reset_stats(self):
        """Reset statistics counters"""
        self.stats = RateLimitStats()
        self._request_timestamps.clear()


# Global rate limiter instance (singleton)
_global_rate_limiter: Optional[RateLimitedClient] = None


def get_rate_limiter(config: Optional[RateLimitConfig] = None) -> RateLimitedClient:
    """Get or create the global rate limiter instance"""
    global _global_rate_limiter
    if _global_rate_limiter is None:
        _global_rate_limiter = RateLimitedClient(config)
    return _global_rate_limiter
