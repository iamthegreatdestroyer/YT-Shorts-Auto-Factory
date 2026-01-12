"""
Utility decorators for the YouTube Shorts Factory.

This module provides decorators for:
- Retry with exponential backoff
- Timeout handling
- Result caching
- Execution timing
- Error handling

Example:
    >>> from src.utils.decorators import retry, timeout, cache_result
    >>>
    >>> @retry(max_attempts=3, delay=1.0)
    ... def flaky_operation():
    ...     pass
    >>>
    >>> @timeout(seconds=30)
    ... async def slow_operation():
    ...     pass
"""

from __future__ import annotations

import asyncio
import functools
import hashlib
import time
from collections import OrderedDict
from datetime import datetime, timedelta
from threading import Lock
from typing import Any, Callable, Optional, ParamSpec, TypeVar

from loguru import logger


P = ParamSpec("P")
R = TypeVar("R")


# =============================================================================
# Retry Decorator
# =============================================================================


def retry(
    max_attempts: int = 3,
    delay: float = 1.0,
    backoff: float = 2.0,
    exceptions: tuple[type[Exception], ...] = (Exception,),
    on_retry: Optional[Callable[[Exception, int], None]] = None,
):
    """
    Retry function on exception with exponential backoff.

    Works with both sync and async functions.

    Args:
        max_attempts: Maximum number of attempts (default 3).
        delay: Initial delay between retries in seconds.
        backoff: Multiplier for delay after each retry.
        exceptions: Tuple of exception types to catch.
        on_retry: Optional callback(exception, attempt) called on each retry.

    Returns:
        Decorated function.

    Example:
        >>> @retry(max_attempts=3, delay=1.0, backoff=2.0)
        ... def fetch_data():
        ...     # May fail, will be retried
        ...     pass
    """

    def decorator(func: Callable[P, R]) -> Callable[P, R]:
        @functools.wraps(func)
        async def async_wrapper(*args: P.args, **kwargs: P.kwargs) -> R:
            last_exception = None
            current_delay = delay

            for attempt in range(1, max_attempts + 1):
                try:
                    return await func(*args, **kwargs)
                except exceptions as e:
                    last_exception = e
                    if attempt < max_attempts:
                        logger.warning(
                            f"Retry {attempt}/{max_attempts} for {func.__name__}: {e}"
                        )
                        if on_retry:
                            on_retry(e, attempt)
                        await asyncio.sleep(current_delay)
                        current_delay *= backoff
                    else:
                        logger.error(
                            f"All {max_attempts} attempts failed for {func.__name__}"
                        )

            raise last_exception

        @functools.wraps(func)
        def sync_wrapper(*args: P.args, **kwargs: P.kwargs) -> R:
            last_exception = None
            current_delay = delay

            for attempt in range(1, max_attempts + 1):
                try:
                    return func(*args, **kwargs)
                except exceptions as e:
                    last_exception = e
                    if attempt < max_attempts:
                        logger.warning(
                            f"Retry {attempt}/{max_attempts} for {func.__name__}: {e}"
                        )
                        if on_retry:
                            on_retry(e, attempt)
                        time.sleep(current_delay)
                        current_delay *= backoff
                    else:
                        logger.error(
                            f"All {max_attempts} attempts failed for {func.__name__}"
                        )

            raise last_exception

        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        return sync_wrapper

    return decorator


# =============================================================================
# Timeout Decorator
# =============================================================================


def timeout(seconds: int):
    """
    Timeout function execution.

    Works only with async functions. For sync functions,
    consider using concurrent.futures with timeout.

    Args:
        seconds: Maximum execution time in seconds.

    Returns:
        Decorated function.

    Raises:
        asyncio.TimeoutError: If execution exceeds timeout.

    Example:
        >>> @timeout(30)
        ... async def slow_download():
        ...     await fetch_large_file()
    """

    def decorator(func: Callable[P, R]) -> Callable[P, R]:
        if not asyncio.iscoroutinefunction(func):
            raise TypeError("@timeout only works with async functions")

        @functools.wraps(func)
        async def wrapper(*args: P.args, **kwargs: P.kwargs) -> R:
            try:
                return await asyncio.wait_for(
                    func(*args, **kwargs),
                    timeout=seconds,
                )
            except asyncio.TimeoutError:
                logger.error(f"Timeout ({seconds}s) exceeded for {func.__name__}")
                raise

        return wrapper

    return decorator


# =============================================================================
# Cache Decorator
# =============================================================================


class LRUCache:
    """Thread-safe LRU cache with TTL support."""

    def __init__(self, maxsize: int = 128, ttl_seconds: int = 3600):
        self.maxsize = maxsize
        self.ttl_seconds = ttl_seconds
        self.cache: OrderedDict[str, tuple[Any, datetime]] = OrderedDict()
        self.lock = Lock()

    def _make_key(self, args: tuple, kwargs: dict) -> str:
        """Create hashable key from function arguments."""
        key_data = str((args, sorted(kwargs.items())))
        return hashlib.md5(key_data.encode()).hexdigest()

    def get(self, key: str) -> tuple[bool, Any]:
        """Get value from cache. Returns (found, value)."""
        with self.lock:
            if key not in self.cache:
                return False, None

            value, timestamp = self.cache[key]

            # Check TTL
            if datetime.now() - timestamp > timedelta(seconds=self.ttl_seconds):
                del self.cache[key]
                return False, None

            # Move to end (most recently used)
            self.cache.move_to_end(key)
            return True, value

    def set(self, key: str, value: Any) -> None:
        """Set value in cache."""
        with self.lock:
            if key in self.cache:
                self.cache.move_to_end(key)
            self.cache[key] = (value, datetime.now())

            # Evict oldest if over size
            while len(self.cache) > self.maxsize:
                self.cache.popitem(last=False)

    def clear(self) -> None:
        """Clear all cached values."""
        with self.lock:
            self.cache.clear()


def cache_result(
    ttl_seconds: int = 3600,
    maxsize: int = 128,
):
    """
    Cache function result in memory.

    Uses function arguments as cache key.
    Thread-safe with LRU eviction.

    Args:
        ttl_seconds: Time-to-live for cached results.
        maxsize: Maximum number of cached results.

    Returns:
        Decorated function.

    Example:
        >>> @cache_result(ttl_seconds=300)
        ... def expensive_computation(x, y):
        ...     return x * y
    """
    cache = LRUCache(maxsize=maxsize, ttl_seconds=ttl_seconds)

    def decorator(func: Callable[P, R]) -> Callable[P, R]:
        @functools.wraps(func)
        async def async_wrapper(*args: P.args, **kwargs: P.kwargs) -> R:
            key = cache._make_key(args, kwargs)
            found, value = cache.get(key)

            if found:
                logger.debug(f"Cache hit for {func.__name__}")
                return value

            result = await func(*args, **kwargs)
            cache.set(key, result)
            return result

        @functools.wraps(func)
        def sync_wrapper(*args: P.args, **kwargs: P.kwargs) -> R:
            key = cache._make_key(args, kwargs)
            found, value = cache.get(key)

            if found:
                logger.debug(f"Cache hit for {func.__name__}")
                return value

            result = func(*args, **kwargs)
            cache.set(key, result)
            return result

        # Add cache control methods
        wrapper = async_wrapper if asyncio.iscoroutinefunction(func) else sync_wrapper
        wrapper.cache_clear = cache.clear
        wrapper.cache = cache
        return wrapper

    return decorator


# =============================================================================
# Timing Decorator
# =============================================================================


def measure_time(
    log_result: bool = True,
    threshold_ms: Optional[float] = None,
):
    """
    Measure function execution time.

    Args:
        log_result: If True, log execution time.
        threshold_ms: Only log if execution time exceeds threshold.

    Returns:
        Decorated function.

    Example:
        >>> @measure_time(log_result=True)
        ... def process_video():
        ...     pass
    """

    def decorator(func: Callable[P, R]) -> Callable[P, R]:
        @functools.wraps(func)
        async def async_wrapper(*args: P.args, **kwargs: P.kwargs) -> R:
            start = time.perf_counter()
            try:
                result = await func(*args, **kwargs)
                return result
            finally:
                elapsed_ms = (time.perf_counter() - start) * 1000
                if log_result:
                    if threshold_ms is None or elapsed_ms >= threshold_ms:
                        logger.debug(
                            f"{func.__name__} executed in {elapsed_ms:.2f}ms"
                        )

        @functools.wraps(func)
        def sync_wrapper(*args: P.args, **kwargs: P.kwargs) -> R:
            start = time.perf_counter()
            try:
                result = func(*args, **kwargs)
                return result
            finally:
                elapsed_ms = (time.perf_counter() - start) * 1000
                if log_result:
                    if threshold_ms is None or elapsed_ms >= threshold_ms:
                        logger.debug(
                            f"{func.__name__} executed in {elapsed_ms:.2f}ms"
                        )

        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        return sync_wrapper

    return decorator


# =============================================================================
# Error Handling Decorator
# =============================================================================


def handle_errors(
    default_return: Any = None,
    exceptions: tuple[type[Exception], ...] = (Exception,),
    log_level: str = "error",
    reraise: bool = False,
):
    """
    Catch exceptions and optionally return default value.

    Args:
        default_return: Value to return on error.
        exceptions: Tuple of exception types to catch.
        log_level: Logging level for caught exceptions.
        reraise: If True, re-raise after logging.

    Returns:
        Decorated function.

    Example:
        >>> @handle_errors(default_return=[])
        ... def get_items():
        ...     # If this fails, returns []
        ...     pass
    """

    def decorator(func: Callable[P, R]) -> Callable[P, R]:
        @functools.wraps(func)
        async def async_wrapper(*args: P.args, **kwargs: P.kwargs) -> R:
            try:
                return await func(*args, **kwargs)
            except exceptions as e:
                log_func = getattr(logger, log_level, logger.error)
                log_func(
                    f"Error in {func.__name__}: {e}",
                    exc_info=True,
                )
                if reraise:
                    raise
                return default_return

        @functools.wraps(func)
        def sync_wrapper(*args: P.args, **kwargs: P.kwargs) -> R:
            try:
                return func(*args, **kwargs)
            except exceptions as e:
                log_func = getattr(logger, log_level, logger.error)
                log_func(
                    f"Error in {func.__name__}: {e}",
                    exc_info=True,
                )
                if reraise:
                    raise
                return default_return

        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        return sync_wrapper

    return decorator


# =============================================================================
# Deprecated Decorator
# =============================================================================


def deprecated(
    reason: str = "",
    version: str = "",
    alternative: str = "",
):
    """
    Mark function as deprecated.

    Logs a warning when the decorated function is called.

    Args:
        reason: Why the function is deprecated.
        version: Version when it will be removed.
        alternative: Suggested alternative function.

    Returns:
        Decorated function.

    Example:
        >>> @deprecated(reason="Use new_function instead", version="2.0")
        ... def old_function():
        ...     pass
    """

    def decorator(func: Callable[P, R]) -> Callable[P, R]:
        @functools.wraps(func)
        def wrapper(*args: P.args, **kwargs: P.kwargs) -> R:
            message = f"{func.__name__} is deprecated"
            if reason:
                message += f": {reason}"
            if version:
                message += f" (will be removed in {version})"
            if alternative:
                message += f". Use {alternative} instead"

            logger.warning(message)
            return func(*args, **kwargs)

        return wrapper

    return decorator


# =============================================================================
# Rate Limiting Decorator
# =============================================================================


def rate_limit(
    calls: int,
    period: float,
):
    """
    Limit function calls to a maximum rate.

    Thread-safe rate limiting using token bucket algorithm.

    Args:
        calls: Maximum number of calls allowed.
        period: Time period in seconds.

    Returns:
        Decorated function.

    Example:
        >>> @rate_limit(calls=10, period=60.0)
        ... def api_call():
        ...     # Max 10 calls per minute
        ...     pass
    """
    min_interval = period / calls
    last_call = [0.0]  # Mutable container for closure
    lock = Lock()

    def decorator(func: Callable[P, R]) -> Callable[P, R]:
        @functools.wraps(func)
        async def async_wrapper(*args: P.args, **kwargs: P.kwargs) -> R:
            with lock:
                elapsed = time.time() - last_call[0]
                wait_time = min_interval - elapsed

                if wait_time > 0:
                    await asyncio.sleep(wait_time)

                last_call[0] = time.time()

            return await func(*args, **kwargs)

        @functools.wraps(func)
        def sync_wrapper(*args: P.args, **kwargs: P.kwargs) -> R:
            with lock:
                elapsed = time.time() - last_call[0]
                wait_time = min_interval - elapsed

                if wait_time > 0:
                    time.sleep(wait_time)

                last_call[0] = time.time()

            return func(*args, **kwargs)

        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        return sync_wrapper

    return decorator


# =============================================================================
# Singleton Decorator
# =============================================================================


def singleton(cls):
    """
    Make a class a singleton.

    Only one instance of the class will be created.
    Thread-safe.

    Args:
        cls: Class to make singleton.

    Returns:
        Singleton wrapper.

    Example:
        >>> @singleton
        ... class DatabaseConnection:
        ...     pass
    """
    instances = {}
    lock = Lock()

    @functools.wraps(cls)
    def get_instance(*args, **kwargs):
        if cls not in instances:
            with lock:
                if cls not in instances:
                    instances[cls] = cls(*args, **kwargs)
        return instances[cls]

    return get_instance
