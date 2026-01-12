"""
Structured logging system using Loguru.

This module provides a production-ready logging infrastructure with:
- Colored console output
- Rotating file logs with compression
- JSON structured logging for log aggregation
- Error tracking with full tracebacks
- Performance decorators
- Request context tracking

Example:
    >>> from src.monitoring.logger import logger, setup_logging
    >>> setup_logging()
    >>> logger.info("Application started")
    >>> logger.error("Something went wrong", exc_info=True)
"""

from __future__ import annotations

import sys
import uuid
from contextlib import contextmanager
from datetime import datetime
from functools import wraps
from pathlib import Path
from time import perf_counter
from typing import Any, Callable, Generator, Optional, ParamSpec, TypeVar

from loguru import logger as _loguru_logger

from src.core.constants import LogConstants


# Type variables for decorators
P = ParamSpec("P")
R = TypeVar("R")


# =============================================================================
# Logger Configuration
# =============================================================================


def setup_logging(
    log_level: str = "INFO",
    log_dir: Path | str = "logs",
    log_file: str = "yt_shorts_factory.log",
    error_file: str = "errors.log",
    json_logging: bool = False,
    console_enabled: bool = True,
    rotation: str = LogConstants.LOG_ROTATION,
    retention: str = LogConstants.LOG_RETENTION,
    compression: str = LogConstants.LOG_COMPRESSION,
) -> None:
    """
    Configure the logging system with console and file handlers.

    Args:
        log_level: Minimum log level for console output.
        log_dir: Directory for log files.
        log_file: Main log file name.
        error_file: Error-only log file name.
        json_logging: Enable JSON structured logging.
        console_enabled: Enable console output.
        rotation: Log rotation configuration (e.g., "10 MB", "1 day").
        retention: Log retention period (e.g., "30 days").
        compression: Compression format for rotated logs.

    Example:
        >>> setup_logging(log_level="DEBUG", log_dir="logs")
        >>> logger.info("Logging configured!")
    """
    # Remove default handler
    _loguru_logger.remove()

    # Ensure log directory exists
    log_path = Path(log_dir)
    log_path.mkdir(parents=True, exist_ok=True)

    # Console handler with colors
    if console_enabled:
        console_format = (
            "<green>{time:HH:mm:ss}</green> | "
            "<level>{level: <8}</level> | "
            "<cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> | "
            "<level>{message}</level>"
        )

        _loguru_logger.add(
            sys.stderr,
            format=console_format,
            level=log_level.upper(),
            colorize=True,
            backtrace=False,
            diagnose=False,
        )

    # Main file handler (all levels)
    file_format = LogConstants.LOG_FORMAT_DETAILED

    _loguru_logger.add(
        log_path / log_file,
        format=file_format,
        level="DEBUG",  # Always capture DEBUG to file
        rotation=rotation,
        retention=retention,
        compression=compression,
        encoding="utf-8",
        enqueue=True,  # Thread-safe
        backtrace=True,
        diagnose=True,
    )

    # Error-only file handler
    _loguru_logger.add(
        log_path / error_file,
        format=file_format,
        level="ERROR",
        rotation=rotation,
        retention=retention,
        compression=compression,
        encoding="utf-8",
        enqueue=True,
        backtrace=True,
        diagnose=True,
    )

    # JSON handler for log aggregation (optional)
    if json_logging:
        _loguru_logger.add(
            log_path / "structured.json",
            format="{message}",
            level="DEBUG",
            rotation=rotation,
            retention=retention,
            compression=compression,
            encoding="utf-8",
            serialize=True,  # JSON format
            enqueue=True,
        )

    # Log startup message
    _loguru_logger.info(
        f"Logging initialized | level={log_level} | dir={log_path}"
    )


def configure_from_settings(settings: Any) -> None:
    """
    Configure logging from application settings.

    Args:
        settings: Application settings object with monitoring configuration.
    """
    from src.core.config import Settings

    if isinstance(settings, Settings):
        setup_logging(
            log_level=settings.app.log_level.value,
            log_dir=settings.storage.logs_path,
            json_logging=settings.is_production,
            console_enabled=settings.is_development,
        )


# =============================================================================
# Context Managers
# =============================================================================


@contextmanager
def log_context(**context: Any) -> Generator[None, None, None]:
    """
    Add contextual information to all log messages within the block.

    Args:
        **context: Key-value pairs to add to log context.

    Example:
        >>> with log_context(request_id="abc123", user_id="user1"):
        ...     logger.info("Processing request")
        ...     # All logs will include request_id and user_id
    """
    with _loguru_logger.contextualize(**context):
        yield


@contextmanager
def request_context(
    request_id: Optional[str] = None,
) -> Generator[str, None, None]:
    """
    Add request tracking context to logs.

    Args:
        request_id: Optional request ID. Generated if not provided.

    Yields:
        The request ID being used.

    Example:
        >>> with request_context() as req_id:
        ...     logger.info("Handling request")
        ...     # All logs will include the request_id
    """
    req_id = request_id or str(uuid.uuid4())[:8]
    with log_context(request_id=req_id):
        yield req_id


@contextmanager
def pipeline_context(
    pipeline_name: str,
    run_id: Optional[str] = None,
) -> Generator[str, None, None]:
    """
    Add pipeline execution context to logs.

    Args:
        pipeline_name: Name of the pipeline.
        run_id: Optional run ID. Generated if not provided.

    Yields:
        The run ID being used.

    Example:
        >>> with pipeline_context("video_generation") as run_id:
        ...     logger.info("Starting pipeline")
    """
    r_id = run_id or str(uuid.uuid4())[:8]
    with log_context(pipeline=pipeline_name, run_id=r_id):
        _loguru_logger.info(f"Pipeline '{pipeline_name}' started | run_id={r_id}")
        start_time = perf_counter()
        try:
            yield r_id
            duration = perf_counter() - start_time
            _loguru_logger.info(
                f"Pipeline '{pipeline_name}' completed | "
                f"duration={duration:.2f}s | run_id={r_id}"
            )
        except Exception as e:
            duration = perf_counter() - start_time
            _loguru_logger.exception(
                f"Pipeline '{pipeline_name}' failed | "
                f"duration={duration:.2f}s | run_id={r_id} | error={e}"
            )
            raise


# =============================================================================
# Decorators
# =============================================================================


def log_execution_time(
    func: Optional[Callable[P, R]] = None,
    *,
    level: str = "DEBUG",
    message: Optional[str] = None,
) -> Callable[P, R] | Callable[[Callable[P, R]], Callable[P, R]]:
    """
    Decorator to log function execution time.

    Args:
        func: The function to decorate.
        level: Log level for the timing message.
        message: Custom message format.

    Returns:
        Decorated function.

    Example:
        >>> @log_execution_time
        ... def slow_function():
        ...     time.sleep(1)
        ...
        >>> @log_execution_time(level="INFO")
        ... def another_function():
        ...     pass
    """
    def decorator(fn: Callable[P, R]) -> Callable[P, R]:
        @wraps(fn)
        def wrapper(*args: P.args, **kwargs: P.kwargs) -> R:
            start = perf_counter()
            try:
                result = fn(*args, **kwargs)
                duration = perf_counter() - start
                msg = message or f"{fn.__name__} completed in {duration:.4f}s"
                getattr(_loguru_logger, level.lower())(msg)
                return result
            except Exception:
                duration = perf_counter() - start
                _loguru_logger.error(f"{fn.__name__} failed after {duration:.4f}s")
                raise

        return wrapper

    if func is not None:
        return decorator(func)
    return decorator


def log_execution_time_async(
    func: Optional[Callable[P, R]] = None,
    *,
    level: str = "DEBUG",
    message: Optional[str] = None,
) -> Callable[P, R] | Callable[[Callable[P, R]], Callable[P, R]]:
    """
    Async version of log_execution_time decorator.

    Example:
        >>> @log_execution_time_async
        ... async def async_operation():
        ...     await asyncio.sleep(1)
    """
    def decorator(fn: Callable[P, R]) -> Callable[P, R]:
        @wraps(fn)
        async def wrapper(*args: P.args, **kwargs: P.kwargs) -> R:
            start = perf_counter()
            try:
                result = await fn(*args, **kwargs)
                duration = perf_counter() - start
                msg = message or f"{fn.__name__} completed in {duration:.4f}s"
                getattr(_loguru_logger, level.lower())(msg)
                return result
            except Exception:
                duration = perf_counter() - start
                _loguru_logger.error(f"{fn.__name__} failed after {duration:.4f}s")
                raise

        return wrapper

    if func is not None:
        return decorator(func)
    return decorator


def log_errors(
    func: Optional[Callable[P, R]] = None,
    *,
    level: str = "ERROR",
    reraise: bool = True,
    default_return: Any = None,
) -> Callable[P, R] | Callable[[Callable[P, R]], Callable[P, R]]:
    """
    Decorator to catch and log exceptions.

    Args:
        func: The function to decorate.
        level: Log level for error messages.
        reraise: Whether to re-raise the exception.
        default_return: Value to return on error if not re-raising.

    Returns:
        Decorated function.

    Example:
        >>> @log_errors(reraise=False, default_return=None)
        ... def risky_operation():
        ...     raise ValueError("Something went wrong")
    """
    def decorator(fn: Callable[P, R]) -> Callable[P, R]:
        @wraps(fn)
        def wrapper(*args: P.args, **kwargs: P.kwargs) -> R:
            try:
                return fn(*args, **kwargs)
            except Exception as e:
                _loguru_logger.opt(exception=True).log(
                    level.upper(),
                    f"Error in {fn.__name__}: {e}"
                )
                if reraise:
                    raise
                return default_return

        return wrapper

    if func is not None:
        return decorator(func)
    return decorator


def log_errors_async(
    func: Optional[Callable[P, R]] = None,
    *,
    level: str = "ERROR",
    reraise: bool = True,
    default_return: Any = None,
) -> Callable[P, R] | Callable[[Callable[P, R]], Callable[P, R]]:
    """
    Async version of log_errors decorator.

    Example:
        >>> @log_errors_async
        ... async def async_risky_operation():
        ...     raise ValueError("Async error")
    """
    def decorator(fn: Callable[P, R]) -> Callable[P, R]:
        @wraps(fn)
        async def wrapper(*args: P.args, **kwargs: P.kwargs) -> R:
            try:
                return await fn(*args, **kwargs)
            except Exception as e:
                _loguru_logger.opt(exception=True).log(
                    level.upper(),
                    f"Error in {fn.__name__}: {e}"
                )
                if reraise:
                    raise
                return default_return

        return wrapper

    if func is not None:
        return decorator(func)
    return decorator


def log_call(
    func: Optional[Callable[P, R]] = None,
    *,
    level: str = "DEBUG",
    log_args: bool = True,
    log_result: bool = False,
    max_arg_length: int = 100,
) -> Callable[P, R] | Callable[[Callable[P, R]], Callable[P, R]]:
    """
    Decorator to log function calls with arguments and results.

    Args:
        func: The function to decorate.
        level: Log level for call messages.
        log_args: Whether to log function arguments.
        log_result: Whether to log the return value.
        max_arg_length: Maximum length for logged argument strings.

    Returns:
        Decorated function.

    Example:
        >>> @log_call(log_result=True)
        ... def process_data(data: list) -> int:
        ...     return len(data)
    """
    def decorator(fn: Callable[P, R]) -> Callable[P, R]:
        @wraps(fn)
        def wrapper(*args: P.args, **kwargs: P.kwargs) -> R:
            # Build call information
            func_name = fn.__name__

            if log_args:
                # Format arguments
                args_str = ", ".join(
                    _truncate_str(repr(a), max_arg_length) for a in args
                )
                kwargs_str = ", ".join(
                    f"{k}={_truncate_str(repr(v), max_arg_length)}"
                    for k, v in kwargs.items()
                )
                all_args = ", ".join(filter(None, [args_str, kwargs_str]))
                getattr(_loguru_logger, level.lower())(
                    f"Calling {func_name}({all_args})"
                )
            else:
                getattr(_loguru_logger, level.lower())(f"Calling {func_name}()")

            result = fn(*args, **kwargs)

            if log_result:
                result_str = _truncate_str(repr(result), max_arg_length)
                getattr(_loguru_logger, level.lower())(
                    f"{func_name} returned: {result_str}"
                )

            return result

        return wrapper

    if func is not None:
        return decorator(func)
    return decorator


# =============================================================================
# Utility Functions
# =============================================================================


def _truncate_str(s: str, max_length: int) -> str:
    """Truncate string to max length with ellipsis."""
    if len(s) <= max_length:
        return s
    return s[: max_length - 3] + "..."


def log_separator(
    title: str = "",
    char: str = "=",
    length: int = 60,
    level: str = "INFO",
) -> None:
    """
    Log a visual separator line.

    Args:
        title: Optional title to include in the separator.
        char: Character to use for the separator.
        length: Total length of the separator.
        level: Log level.

    Example:
        >>> log_separator("Starting Process")
        # Logs: ==================== Starting Process ====================
    """
    if title:
        padding = (length - len(title) - 2) // 2
        line = f"{char * padding} {title} {char * padding}"
        # Adjust for odd lengths
        if len(line) < length:
            line += char
    else:
        line = char * length

    getattr(_loguru_logger, level.lower())(line)


def log_dict(
    data: dict[str, Any],
    title: Optional[str] = None,
    level: str = "DEBUG",
) -> None:
    """
    Log a dictionary in a formatted way.

    Args:
        data: Dictionary to log.
        title: Optional title for the log entry.
        level: Log level.

    Example:
        >>> log_dict({"key": "value", "count": 42}, title="Config")
    """
    log_func = getattr(_loguru_logger, level.lower())

    if title:
        log_func(f"{title}:")

    for key, value in data.items():
        log_func(f"  {key}: {value}")


def log_exception(
    error: Exception,
    context: Optional[dict[str, Any]] = None,
) -> None:
    """
    Log an exception with optional context.

    Args:
        error: The exception to log.
        context: Optional context information.

    Example:
        >>> try:
        ...     risky_operation()
        ... except Exception as e:
        ...     log_exception(e, context={"user_id": "123"})
    """
    if context:
        context_str = " | ".join(f"{k}={v}" for k, v in context.items())
        _loguru_logger.opt(exception=True).error(
            f"Exception occurred | {context_str} | {error}"
        )
    else:
        _loguru_logger.opt(exception=True).error(f"Exception occurred: {error}")


def get_child_logger(name: str) -> Any:
    """
    Get a child logger with a specific name.

    Args:
        name: Name for the child logger.

    Returns:
        Logger instance bound with the name.

    Example:
        >>> uploader_logger = get_child_logger("uploader")
        >>> uploader_logger.info("Upload started")
    """
    return _loguru_logger.bind(module=name)


# =============================================================================
# Structured Logging Helpers
# =============================================================================


def log_event(
    event_type: str,
    data: Optional[dict[str, Any]] = None,
    level: str = "INFO",
) -> None:
    """
    Log a structured event.

    Args:
        event_type: Type/name of the event.
        data: Event data as key-value pairs.
        level: Log level.

    Example:
        >>> log_event("video_uploaded", {"video_id": "abc123", "duration": 45})
    """
    event_data = {
        "event": event_type,
        "timestamp": datetime.utcnow().isoformat(),
        **(data or {}),
    }
    getattr(_loguru_logger, level.lower())(f"EVENT: {event_type} | {event_data}")


def log_metric(
    metric_name: str,
    value: float | int,
    unit: Optional[str] = None,
    tags: Optional[dict[str, str]] = None,
) -> None:
    """
    Log a metric value.

    Args:
        metric_name: Name of the metric.
        value: Metric value.
        unit: Optional unit of measurement.
        tags: Optional tags for the metric.

    Example:
        >>> log_metric("video_render_time", 15.5, unit="seconds")
        >>> log_metric("api_requests", 100, tags={"endpoint": "/upload"})
    """
    metric_data = {
        "metric": metric_name,
        "value": value,
        "timestamp": datetime.utcnow().isoformat(),
    }
    if unit:
        metric_data["unit"] = unit
    if tags:
        metric_data["tags"] = tags

    _loguru_logger.debug(f"METRIC: {metric_name}={value} | {metric_data}")


# =============================================================================
# Export Logger
# =============================================================================


# Re-export the configured logger
logger = _loguru_logger


__all__ = [
    # Main logger
    "logger",
    # Setup functions
    "setup_logging",
    "configure_from_settings",
    # Context managers
    "log_context",
    "request_context",
    "pipeline_context",
    # Decorators
    "log_execution_time",
    "log_execution_time_async",
    "log_errors",
    "log_errors_async",
    "log_call",
    # Utility functions
    "log_separator",
    "log_dict",
    "log_exception",
    "get_child_logger",
    # Structured logging
    "log_event",
    "log_metric",
]
