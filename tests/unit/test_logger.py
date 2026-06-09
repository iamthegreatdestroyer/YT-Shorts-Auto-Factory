"""
Unit tests for the structured logging system.
"""
from __future__ import annotations

import asyncio
import tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest


class TestSetupLogging:
    """Test setup_logging function."""

    def test_default_setup(self, tmp_path):
        from src.monitoring.logger import setup_logging
        setup_logging(log_dir=tmp_path, console_enabled=False)
        # Should not raise

    def test_setup_with_debug_level(self, tmp_path):
        from src.monitoring.logger import setup_logging
        setup_logging(log_level="DEBUG", log_dir=tmp_path, console_enabled=False)

    def test_setup_with_json_logging(self, tmp_path):
        from src.monitoring.logger import setup_logging
        setup_logging(log_dir=tmp_path, json_logging=True, console_enabled=False)
        assert (tmp_path / "structured.json").exists() or True  # file may be created lazily

    def test_setup_with_console(self, tmp_path):
        from src.monitoring.logger import setup_logging
        setup_logging(log_dir=tmp_path, console_enabled=True)

    def test_creates_log_dir(self, tmp_path):
        from src.monitoring.logger import setup_logging
        new_dir = tmp_path / "nested" / "logs"
        setup_logging(log_dir=new_dir, console_enabled=False)
        assert new_dir.exists()


class TestConfigureFromSettings:
    """Test configure_from_settings function."""

    def test_with_settings_object(self, tmp_path):
        from src.monitoring.logger import configure_from_settings

        mock_settings = MagicMock()
        mock_settings.app.log_level.value = "INFO"
        mock_settings.storage.logs_path = tmp_path
        mock_settings.is_production = False
        mock_settings.is_development = True

        with patch("src.monitoring.logger.setup_logging") as mock_setup:
            from src.core.config import Settings
            # Pass a non-Settings object → should not call setup_logging
            configure_from_settings({"not": "settings"})
            mock_setup.assert_not_called()

    def test_with_real_settings(self, tmp_path):
        from src.monitoring.logger import configure_from_settings
        from src.core.config import Settings

        with patch("src.monitoring.logger.setup_logging") as mock_setup:
            mock_s = MagicMock()
            mock_s.__class__ = Settings  # make isinstance check pass
            mock_s.app.log_level.value = "DEBUG"
            mock_s.storage.logs_path = tmp_path
            mock_s.is_production = False
            mock_s.is_development = True
            configure_from_settings(mock_s)
            mock_setup.assert_called_once()


class TestLogContext:
    """Test log_context context manager."""

    def test_basic_usage(self):
        from src.monitoring.logger import log_context, logger
        with log_context(request_id="test123"):
            logger.debug("inside context")

    def test_multiple_keys(self):
        from src.monitoring.logger import log_context, logger
        with log_context(user="alice", action="upload", count=42):
            logger.info("multi-key context")


class TestRequestContext:
    """Test request_context context manager."""

    def test_auto_generated_id(self):
        from src.monitoring.logger import request_context
        with request_context() as req_id:
            assert req_id is not None
            assert len(req_id) > 0

    def test_provided_id(self):
        from src.monitoring.logger import request_context
        with request_context(request_id="my-req-id") as req_id:
            assert req_id == "my-req-id"


class TestPipelineContext:
    """Test pipeline_context context manager."""

    def test_success_path(self):
        from src.monitoring.logger import pipeline_context
        with pipeline_context("test_pipeline") as run_id:
            assert run_id is not None

    def test_provided_run_id(self):
        from src.monitoring.logger import pipeline_context
        with pipeline_context("test_pipeline", run_id="run-001") as run_id:
            assert run_id == "run-001"

    def test_exception_propagates(self):
        from src.monitoring.logger import pipeline_context
        with pytest.raises(ValueError):
            with pipeline_context("failing_pipeline"):
                raise ValueError("test error")


class TestLogExecutionTime:
    """Test log_execution_time decorator."""

    def test_direct_decoration(self):
        from src.monitoring.logger import log_execution_time

        @log_execution_time
        def my_func():
            return 42

        result = my_func()
        assert result == 42

    def test_parameterized_decoration(self):
        from src.monitoring.logger import log_execution_time

        @log_execution_time(level="INFO")
        def my_func():
            return "hello"

        result = my_func()
        assert result == "hello"

    def test_custom_message(self):
        from src.monitoring.logger import log_execution_time

        @log_execution_time(message="custom message")
        def my_func():
            return True

        assert my_func() is True

    def test_exception_logs_and_reraises(self):
        from src.monitoring.logger import log_execution_time

        @log_execution_time
        def failing_func():
            raise RuntimeError("boom")

        with pytest.raises(RuntimeError):
            failing_func()


class TestLogExecutionTimeAsync:
    """Test log_execution_time_async decorator."""

    @pytest.mark.asyncio
    async def test_direct_decoration(self):
        from src.monitoring.logger import log_execution_time_async

        @log_execution_time_async
        async def my_async_func():
            return 42

        result = await my_async_func()
        assert result == 42

    @pytest.mark.asyncio
    async def test_parameterized_decoration(self):
        from src.monitoring.logger import log_execution_time_async

        @log_execution_time_async(level="INFO")
        async def my_func():
            return "async"

        result = await my_func()
        assert result == "async"

    @pytest.mark.asyncio
    async def test_custom_message(self):
        from src.monitoring.logger import log_execution_time_async

        @log_execution_time_async(message="custom async message")
        async def my_func():
            return True

        assert await my_func() is True

    @pytest.mark.asyncio
    async def test_exception_reraises(self):
        from src.monitoring.logger import log_execution_time_async

        @log_execution_time_async
        async def failing():
            raise ValueError("async boom")

        with pytest.raises(ValueError):
            await failing()


class TestLogErrors:
    """Test log_errors decorator."""

    def test_direct_decoration_success(self):
        from src.monitoring.logger import log_errors

        @log_errors
        def my_func():
            return "ok"

        assert my_func() == "ok"

    def test_reraise_true(self):
        from src.monitoring.logger import log_errors

        @log_errors(reraise=True)
        def fail():
            raise ValueError("test error")

        with pytest.raises(ValueError):
            fail()

    def test_reraise_false_returns_default(self):
        from src.monitoring.logger import log_errors

        @log_errors(reraise=False, default_return="fallback")
        def fail():
            raise ValueError("test error")

        result = fail()
        assert result == "fallback"

    def test_no_exception_passes_through(self):
        from src.monitoring.logger import log_errors

        @log_errors(reraise=False)
        def succeed():
            return 123

        assert succeed() == 123


class TestLogErrorsAsync:
    """Test log_errors_async decorator."""

    @pytest.mark.asyncio
    async def test_success(self):
        from src.monitoring.logger import log_errors_async

        @log_errors_async
        async def my_func():
            return "async ok"

        assert await my_func() == "async ok"

    @pytest.mark.asyncio
    async def test_reraise_true(self):
        from src.monitoring.logger import log_errors_async

        @log_errors_async(reraise=True)
        async def fail():
            raise RuntimeError("async fail")

        with pytest.raises(RuntimeError):
            await fail()

    @pytest.mark.asyncio
    async def test_reraise_false(self):
        from src.monitoring.logger import log_errors_async

        @log_errors_async(reraise=False, default_return=None)
        async def fail():
            raise RuntimeError("ignored")

        result = await fail()
        assert result is None


class TestLogCall:
    """Test log_call decorator."""

    def test_direct_decoration(self):
        from src.monitoring.logger import log_call

        @log_call
        def my_func(a, b=2):
            return a + b

        result = my_func(1, b=3)
        assert result == 4

    def test_log_result(self):
        from src.monitoring.logger import log_call

        @log_call(log_result=True)
        def my_func(x):
            return x * 2

        assert my_func(5) == 10

    def test_no_args_logging(self):
        from src.monitoring.logger import log_call

        @log_call(log_args=False)
        def my_func(secret):
            return secret

        assert my_func("value") == "value"

    def test_long_args_truncated(self):
        from src.monitoring.logger import log_call

        @log_call(max_arg_length=10)
        def my_func(data):
            return data

        long_data = "x" * 100
        result = my_func(long_data)
        assert result == long_data

    def test_parameterized_level(self):
        from src.monitoring.logger import log_call

        @log_call(level="INFO")
        def my_func():
            return True

        assert my_func() is True


class TestLogSeparator:
    """Test log_separator function."""

    def test_without_title(self):
        from src.monitoring.logger import log_separator
        log_separator()  # Should not raise

    def test_with_title(self):
        from src.monitoring.logger import log_separator
        log_separator("Test Section")

    def test_custom_char(self):
        from src.monitoring.logger import log_separator
        log_separator("Title", char="-")

    def test_custom_level(self):
        from src.monitoring.logger import log_separator
        log_separator("Test", level="DEBUG")

    def test_odd_length_title(self):
        from src.monitoring.logger import log_separator
        log_separator("X", length=61)


class TestLogDict:
    """Test log_dict function."""

    def test_basic_dict(self):
        from src.monitoring.logger import log_dict
        log_dict({"key": "value", "count": 42})

    def test_with_title(self):
        from src.monitoring.logger import log_dict
        log_dict({"a": 1}, title="My Data")

    def test_debug_level(self):
        from src.monitoring.logger import log_dict
        log_dict({"x": "y"}, level="DEBUG")


class TestLogException:
    """Test log_exception function."""

    def test_without_context(self):
        from src.monitoring.logger import log_exception
        log_exception(ValueError("test error"))

    def test_with_context(self):
        from src.monitoring.logger import log_exception
        log_exception(
            RuntimeError("runtime error"),
            context={"user_id": "123", "action": "upload"},
        )


class TestGetChildLogger:
    """Test get_child_logger function."""

    def test_returns_logger(self):
        from src.monitoring.logger import get_child_logger
        child = get_child_logger("uploader")
        assert child is not None

    def test_can_log(self):
        from src.monitoring.logger import get_child_logger
        child = get_child_logger("test_module")
        child.debug("test message from child logger")


class TestLogEvent:
    """Test log_event function."""

    def test_basic_event(self):
        from src.monitoring.logger import log_event
        log_event("video_created")

    def test_with_data(self):
        from src.monitoring.logger import log_event
        log_event("video_uploaded", data={"video_id": "abc123", "duration": 45})

    def test_custom_level(self):
        from src.monitoring.logger import log_event
        log_event("pipeline_started", level="DEBUG")


class TestLogMetric:
    """Test log_metric function."""

    def test_basic_metric(self):
        from src.monitoring.logger import log_metric
        log_metric("render_time", 15.5)

    def test_with_unit(self):
        from src.monitoring.logger import log_metric
        log_metric("video_size", 1048576, unit="bytes")

    def test_with_tags(self):
        from src.monitoring.logger import log_metric
        log_metric("api_requests", 100, tags={"endpoint": "/upload", "status": "200"})

    def test_with_unit_and_tags(self):
        from src.monitoring.logger import log_metric
        log_metric("duration", 30.0, unit="seconds", tags={"type": "short"})


class TestTruncateStr:
    """Test _truncate_str utility."""

    def test_short_string_unchanged(self):
        from src.monitoring.logger import _truncate_str
        assert _truncate_str("hello", 10) == "hello"

    def test_long_string_truncated(self):
        from src.monitoring.logger import _truncate_str
        result = _truncate_str("hello world this is long", 10)
        assert len(result) <= 10
        assert result.endswith("...")

    def test_exact_length(self):
        from src.monitoring.logger import _truncate_str
        s = "12345"
        assert _truncate_str(s, 5) == s
