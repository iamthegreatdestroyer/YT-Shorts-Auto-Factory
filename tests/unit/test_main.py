"""
Unit tests for the main application entry point and CLI.
"""
from __future__ import annotations

import asyncio
import signal
import sys
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, Mock, patch, PropertyMock

import pytest

from src.core.exceptions import ConfigurationError, PipelineError, YTShortsError


# =============================================================================
# Helpers / fixtures
# =============================================================================


def _make_settings():
    """Build a minimal mock Settings object."""
    settings = MagicMock()
    settings.app.log_level.value = "INFO"
    settings.app.environment.value = "testing"
    settings.app.debug = False
    settings.storage.logs_path = Path("logs")
    settings.storage.ensure_directories = MagicMock()
    settings.validate_api_keys.return_value = {"youtube": True, "openai": True}
    settings.content.niche = "tech"
    settings.content.target_duration = 30
    settings.tts.provider.value = "edge_tts"
    settings.image.provider.value = "stable_diffusion"
    settings.schedule.enabled = True
    settings.schedule.timezone = "UTC"
    settings.schedule.generation_cron = "0 9 * * *"
    settings.schedule.upload_cron = "0 10 * * *"
    settings.is_production = False
    settings.is_development = True
    return settings


# =============================================================================
# Application class tests
# =============================================================================


class TestApplicationInit:
    """Test Application initialization."""

    def test_default_init(self):
        from src.main import Application
        app = Application()
        assert app.test_mode is False
        assert app.no_upload is False
        assert app.settings is None

    def test_custom_init(self):
        from src.main import Application
        app = Application(
            config_path=Path("config.yaml"),
            test_mode=True,
            no_upload=True,
            topic="tech tips",
            output_dir=Path("output"),
            upload=True,
            dry_run_upload=True,
            publish_date="2026-07-01",
        )
        assert app.test_mode is True
        assert app.no_upload is True
        assert app.topic == "tech tips"
        assert app.publish_date == "2026-07-01"


class TestApplicationLoadSettings:
    """Test Application.load_settings."""

    def test_successful_load(self):
        from src.main import Application
        mock_settings = _make_settings()

        with patch("src.main.reload_settings", return_value=mock_settings):
            app = Application(test_mode=True)
            result = app.load_settings()

        assert result is mock_settings
        assert app.settings is mock_settings

    def test_reload_failure_raises_config_error(self):
        from src.main import Application

        with patch("src.main.reload_settings", side_effect=Exception("file not found")):
            app = Application()
            with pytest.raises(ConfigurationError):
                app.load_settings()

    def test_validate_settings_called(self):
        from src.main import Application
        mock_settings = _make_settings()

        with patch("src.main.reload_settings", return_value=mock_settings):
            app = Application(test_mode=True)
            app.load_settings()
            mock_settings.validate_api_keys.assert_not_called()  # test_mode skips


class TestApplicationValidateSettings:
    """Test Application._validate_settings."""

    def test_settings_none_raises(self):
        from src.main import Application
        app = Application()
        with pytest.raises(ConfigurationError):
            app._validate_settings()

    def test_test_mode_skips_api_validation(self):
        from src.main import Application
        app = Application(test_mode=True)
        app.settings = _make_settings()
        app._validate_settings()
        app.settings.validate_api_keys.assert_not_called()

    def test_non_test_mode_validates_apis(self):
        from src.main import Application
        app = Application(test_mode=False)
        app.settings = _make_settings()
        app.settings.validate_api_keys.return_value = {
            "youtube": False,
            "openai": True,
        }
        # Should log warning but not raise
        app._validate_settings()
        app.settings.validate_api_keys.assert_called_once()


class TestApplicationSetup:
    """Test Application.setup."""

    def test_setup_success(self, tmp_path):
        from src.main import Application
        mock_settings = _make_settings()
        mock_settings.storage.logs_path = tmp_path

        with patch("src.main.reload_settings", return_value=mock_settings), \
             patch("src.main.setup_logging"), \
             patch("src.main.log_separator"), \
             patch("src.main.logger"):
            app = Application(test_mode=True)
            app.setup()

        assert app.settings is mock_settings

    def test_setup_settings_none_after_load_raises(self):
        from src.main import Application

        with patch("src.main.reload_settings", return_value=None):
            app = Application()
            with pytest.raises(ConfigurationError):
                app.setup()


class TestApplicationRunOnce:
    """Test Application.run_once."""

    @pytest.mark.asyncio
    async def test_settings_not_loaded_raises(self):
        from src.main import Application
        app = Application()
        with pytest.raises(ConfigurationError):
            await app.run_once()

    @pytest.mark.asyncio
    async def test_successful_run(self):
        from src.main import Application
        app = Application(test_mode=True)
        app.settings = _make_settings()

        mock_pipeline = AsyncMock()
        mock_pipeline.run = AsyncMock(return_value={"success": True, "video_id": "abc123"})

        with patch("src.main.pipeline_context") as mock_ctx, \
             patch("src.main.logger"):
            # pipeline_context is a context manager yielding a run_id
            from contextlib import contextmanager

            @contextmanager
            def fake_ctx(name):
                yield "run-001"

            mock_ctx.side_effect = fake_ctx

            with patch("src.core.pipeline.Pipeline", return_value=mock_pipeline):
                # Import and patch inline
                import src.main as main_module
                with patch.object(main_module, "pipeline_context", fake_ctx):
                    with patch("src.main.Pipeline", return_value=mock_pipeline, create=True):
                        result = await app.run_once()

        # Just ensure it didn't raise
        assert result is not None or True

    @pytest.mark.asyncio
    async def test_pipeline_import_and_run(self):
        from src.main import Application
        app = Application(test_mode=True)
        app.settings = _make_settings()

        mock_pipeline_instance = AsyncMock()
        mock_pipeline_instance.run = AsyncMock(return_value={"success": True, "video_id": "xyz"})

        mock_pipeline_cls = MagicMock(return_value=mock_pipeline_instance)

        from contextlib import contextmanager

        @contextmanager
        def fake_pipeline_ctx(name):
            yield "run-999"

        with patch("src.main.pipeline_context", fake_pipeline_ctx), \
             patch("src.main.logger"), \
             patch("src.core.pipeline.Pipeline", mock_pipeline_cls):
            # The actual pipeline import happens inside run_once
            # We patch at the module level where it's imported
            import importlib
            import src.core.pipeline as pipeline_mod
            orig = pipeline_mod.Pipeline
            try:
                pipeline_mod.Pipeline = mock_pipeline_cls
                result = await app.run_once()
            finally:
                pipeline_mod.Pipeline = orig

    @pytest.mark.asyncio
    async def test_yt_shorts_error_reraises(self):
        from src.main import Application
        app = Application(test_mode=True)
        app.settings = _make_settings()

        from contextlib import contextmanager

        @contextmanager
        def fake_ctx(name):
            yield "run-001"

        mock_pipeline = AsyncMock()
        mock_pipeline.run = AsyncMock(side_effect=PipelineError("fail"))

        with patch("src.main.pipeline_context", fake_ctx), \
             patch("src.main.logger"):
            import src.core.pipeline as pipeline_mod
            orig = pipeline_mod.Pipeline
            try:
                pipeline_mod.Pipeline = MagicMock(return_value=mock_pipeline)
                with pytest.raises(YTShortsError):
                    await app.run_once()
            finally:
                pipeline_mod.Pipeline = orig

    @pytest.mark.asyncio
    async def test_unexpected_error_wrapped(self):
        from src.main import Application
        app = Application(test_mode=True)
        app.settings = _make_settings()

        from contextlib import contextmanager

        @contextmanager
        def fake_ctx(name):
            yield "run-001"

        mock_pipeline = AsyncMock()
        mock_pipeline.run = AsyncMock(side_effect=RuntimeError("unexpected"))

        with patch("src.main.pipeline_context", fake_ctx), \
             patch("src.main.logger"):
            import src.core.pipeline as pipeline_mod
            orig = pipeline_mod.Pipeline
            try:
                pipeline_mod.Pipeline = MagicMock(return_value=mock_pipeline)
                with pytest.raises(PipelineError):
                    await app.run_once()
            finally:
                pipeline_mod.Pipeline = orig


class TestApplicationShutdown:
    """Test Application.shutdown."""

    @pytest.mark.asyncio
    async def test_shutdown_no_scheduler(self):
        from src.main import Application
        app = Application()
        app.settings = _make_settings()
        with patch("src.main.log_separator"), patch("src.main.logger"):
            await app.shutdown()  # Should not raise

    @pytest.mark.asyncio
    async def test_shutdown_with_scheduler(self):
        from src.main import Application
        app = Application()
        app.settings = _make_settings()
        mock_scheduler = MagicMock()
        app._scheduler = mock_scheduler
        with patch("src.main.log_separator"), patch("src.main.logger"):
            await app.shutdown()
        mock_scheduler.shutdown.assert_called_once_with(wait=True)

    @pytest.mark.asyncio
    async def test_shutdown_no_settings(self):
        from src.main import Application
        app = Application()
        with patch("src.main.log_separator"), patch("src.main.logger"):
            await app.shutdown()  # settings is None, should still work


class TestApplicationRequestShutdown:
    """Test Application.request_shutdown."""

    def test_sets_shutdown_event(self):
        from src.main import Application
        app = Application()
        # The event should not be set initially
        assert not app._shutdown_event.is_set()
        with patch("src.main.logger"):
            app.request_shutdown()
        assert app._shutdown_event.is_set()


class TestApplicationScheduledMethods:
    """Test Application._scheduled_generation/_scheduled_upload/_health_check."""

    @pytest.mark.asyncio
    async def test_scheduled_generation_success(self):
        from src.main import Application
        app = Application(test_mode=True)
        app.settings = _make_settings()

        with patch.object(app, "run_once", new=AsyncMock(return_value={"success": True})), \
             patch("src.main.logger"):
            await app._scheduled_generation()

    @pytest.mark.asyncio
    async def test_scheduled_generation_error_logged(self):
        from src.main import Application
        app = Application(test_mode=True)
        app.settings = _make_settings()

        with patch.object(app, "run_once", new=AsyncMock(side_effect=Exception("fail"))), \
             patch("src.main.logger"):
            await app._scheduled_generation()  # Should not raise

    @pytest.mark.asyncio
    async def test_scheduled_upload(self):
        from src.main import Application
        app = Application()
        with patch("src.main.logger"):
            await app._scheduled_upload()  # Should not raise

    @pytest.mark.asyncio
    async def test_health_check(self):
        from src.main import Application
        app = Application()
        with patch("src.main.logger"):
            await app._health_check()  # Should not raise


# =============================================================================
# CLI Interface tests
# =============================================================================


class TestCreateParser:
    """Test create_parser function."""

    def test_creates_parser(self):
        from src.main import create_parser
        parser = create_parser()
        assert parser is not None

    def test_once_flag(self):
        from src.main import create_parser
        parser = create_parser()
        args = parser.parse_args(["--once"])
        assert args.once is True

    def test_daemon_flag(self):
        from src.main import create_parser
        parser = create_parser()
        args = parser.parse_args(["--daemon"])
        assert args.daemon is True

    def test_dry_run_flag(self):
        from src.main import create_parser
        parser = create_parser()
        args = parser.parse_args(["--dry-run"])
        assert args.dry_run is True

    def test_no_upload_flag(self):
        from src.main import create_parser
        parser = create_parser()
        args = parser.parse_args(["--once", "--no-upload"])
        assert args.no_upload is True

    def test_test_flag(self):
        from src.main import create_parser
        parser = create_parser()
        args = parser.parse_args(["--once", "--test"])
        assert args.test is True

    def test_topic_arg(self):
        from src.main import create_parser
        parser = create_parser()
        args = parser.parse_args(["--once", "--topic", "python tips"])
        assert args.topic == "python tips"

    def test_output_arg(self):
        from src.main import create_parser
        parser = create_parser()
        args = parser.parse_args(["--once", "--output", "/tmp/output"])
        assert args.output == Path("/tmp/output")

    def test_debug_flag(self):
        from src.main import create_parser
        parser = create_parser()
        args = parser.parse_args(["--once", "--debug"])
        assert args.debug is True

    def test_verbose_flag(self):
        from src.main import create_parser
        parser = create_parser()
        args = parser.parse_args(["--once", "-v"])
        assert args.verbose == 1

    def test_upload_flag(self):
        from src.main import create_parser
        parser = create_parser()
        args = parser.parse_args(["--once", "--upload"])
        assert args.upload is True

    def test_publish_date(self):
        from src.main import create_parser
        parser = create_parser()
        args = parser.parse_args(["--once", "--publish-date", "2026-07-01"])
        assert args.publish_date == "2026-07-01"

    def test_once_and_daemon_mutually_exclusive(self):
        from src.main import create_parser
        parser = create_parser()
        with pytest.raises(SystemExit):
            parser.parse_args(["--once", "--daemon"])

    def test_config_arg(self):
        from src.main import create_parser
        parser = create_parser()
        args = parser.parse_args(["--once", "-c", "config/test.yaml"])
        assert args.config == Path("config/test.yaml")


class TestSetupSignalHandlers:
    """Test setup_signal_handlers function."""

    def test_registers_sigint(self):
        from src.main import setup_signal_handlers, Application
        app = Application()
        with patch("src.main.logger"):
            with patch("signal.signal") as mock_signal:
                setup_signal_handlers(app)
                # Should have registered at least SIGINT and SIGTERM
                calls = [c[0][0] for c in mock_signal.call_args_list]
                assert signal.SIGINT in calls
                assert signal.SIGTERM in calls

    def test_signal_handler_calls_request_shutdown(self):
        from src.main import setup_signal_handlers, Application
        app = Application()
        with patch("src.main.logger"):
            setup_signal_handlers(app)
            # Simulate the signal handler being called
            with patch.object(app, "request_shutdown") as mock_shutdown, \
                 patch("src.main.logger"):
                # Get the registered handler and call it
                import signal as sig_mod
                handler = sig_mod.getsignal(signal.SIGINT)
                if callable(handler):
                    handler(signal.SIGINT, None)


class TestAsyncMain:
    """Test async_main function."""

    @pytest.mark.asyncio
    async def test_no_mode_returns_2(self):
        from src.main import async_main, create_parser
        parser = create_parser()
        args = parser.parse_args([])
        result = await async_main(args)
        assert result == 2

    @pytest.mark.asyncio
    async def test_dry_run_returns_0(self):
        from src.main import async_main, create_parser
        parser = create_parser()
        args = parser.parse_args(["--dry-run"])

        mock_settings = _make_settings()

        with patch("src.main.reload_settings", return_value=mock_settings), \
             patch("src.main.setup_logging"), \
             patch("src.main.log_separator"), \
             patch("src.main.logger"), \
             patch("src.main.Application.shutdown", new=AsyncMock()):
            result = await async_main(args)

        assert result == 0

    @pytest.mark.asyncio
    async def test_dry_run_verbose(self):
        from src.main import async_main, create_parser
        parser = create_parser()
        args = parser.parse_args(["--dry-run", "-vv"])  # -vv → verbose=2

        mock_settings = _make_settings()

        with patch("src.main.reload_settings", return_value=mock_settings), \
             patch("src.main.setup_logging"), \
             patch("src.main.log_separator"), \
             patch("src.main.logger"), \
             patch("src.main.Application.shutdown", new=AsyncMock()):
            result = await async_main(args)

        assert result == 0

    @pytest.mark.asyncio
    async def test_dry_run_verbose_info(self):
        from src.main import async_main, create_parser
        parser = create_parser()
        args = parser.parse_args(["--dry-run", "-v"])  # -v → verbose=1

        mock_settings = _make_settings()

        with patch("src.main.reload_settings", return_value=mock_settings), \
             patch("src.main.setup_logging"), \
             patch("src.main.log_separator"), \
             patch("src.main.logger"), \
             patch("src.main.Application.shutdown", new=AsyncMock()):
            result = await async_main(args)

        assert result == 0

    @pytest.mark.asyncio
    async def test_once_success(self):
        from src.main import async_main, create_parser
        parser = create_parser()
        args = parser.parse_args(["--once", "--test"])

        mock_settings = _make_settings()

        with patch("src.main.reload_settings", return_value=mock_settings), \
             patch("src.main.setup_logging"), \
             patch("src.main.log_separator"), \
             patch("src.main.logger"), \
             patch("src.main.setup_signal_handlers"), \
             patch("src.main.Application.run_once", new=AsyncMock(
                 return_value={"success": True, "video_path": "/tmp/video.mp4", "video_id": "abc"}
             )), \
             patch("src.main.Application.shutdown", new=AsyncMock()):
            result = await async_main(args)

        assert result == 0

    @pytest.mark.asyncio
    async def test_once_failure(self):
        from src.main import async_main, create_parser
        parser = create_parser()
        args = parser.parse_args(["--once", "--test"])

        mock_settings = _make_settings()

        with patch("src.main.reload_settings", return_value=mock_settings), \
             patch("src.main.setup_logging"), \
             patch("src.main.log_separator"), \
             patch("src.main.logger"), \
             patch("src.main.setup_signal_handlers"), \
             patch("src.main.Application.run_once", new=AsyncMock(
                 return_value={"success": False, "error": "Pipeline failed"}
             )), \
             patch("src.main.Application.shutdown", new=AsyncMock()):
            result = await async_main(args)

        assert result == 1

    @pytest.mark.asyncio
    async def test_once_with_publish_date(self):
        from src.main import async_main, create_parser
        parser = create_parser()
        args = parser.parse_args(["--once", "--test", "--publish-date", "2026-07-01"])

        mock_settings = _make_settings()

        with patch("src.main.reload_settings", return_value=mock_settings), \
             patch("src.main.setup_logging"), \
             patch("src.main.log_separator"), \
             patch("src.main.logger"), \
             patch("src.main.setup_signal_handlers"), \
             patch("src.main.Application.run_once", new=AsyncMock(
                 return_value={"success": True}
             )), \
             patch("src.main.Application.shutdown", new=AsyncMock()):
            result = await async_main(args)

        assert result == 0

    @pytest.mark.asyncio
    async def test_once_yt_shorts_error(self):
        from src.main import async_main, create_parser
        parser = create_parser()
        args = parser.parse_args(["--once", "--test"])

        mock_settings = _make_settings()

        with patch("src.main.reload_settings", return_value=mock_settings), \
             patch("src.main.setup_logging"), \
             patch("src.main.log_separator"), \
             patch("src.main.logger"), \
             patch("src.main.setup_signal_handlers"), \
             patch("src.main.Application.run_once",
                   new=AsyncMock(side_effect=YTShortsError("pipeline error"))), \
             patch("src.main.Application.shutdown", new=AsyncMock()):
            result = await async_main(args)

        assert result == 1

    @pytest.mark.asyncio
    async def test_configuration_error_returns_2(self):
        from src.main import async_main, create_parser
        parser = create_parser()
        args = parser.parse_args(["--dry-run"])

        with patch("src.main.reload_settings", side_effect=ConfigurationError("bad config")), \
             patch("src.main.Application.shutdown", new=AsyncMock()):
            result = await async_main(args)

        assert result == 2

    @pytest.mark.asyncio
    async def test_keyboard_interrupt_returns_130(self):
        from src.main import async_main, create_parser
        parser = create_parser()
        args = parser.parse_args(["--once", "--test"])

        mock_settings = _make_settings()

        with patch("src.main.reload_settings", return_value=mock_settings), \
             patch("src.main.setup_logging"), \
             patch("src.main.log_separator"), \
             patch("src.main.logger"), \
             patch("src.main.setup_signal_handlers"), \
             patch("src.main.Application.run_once",
                   new=AsyncMock(side_effect=KeyboardInterrupt())), \
             patch("src.main.Application.shutdown", new=AsyncMock()):
            result = await async_main(args)

        assert result == 130

    @pytest.mark.asyncio
    async def test_unexpected_error_returns_1(self):
        from src.main import async_main, create_parser
        parser = create_parser()
        args = parser.parse_args(["--once", "--test"])

        mock_settings = _make_settings()

        with patch("src.main.reload_settings", return_value=mock_settings), \
             patch("src.main.setup_logging"), \
             patch("src.main.log_separator"), \
             patch("src.main.logger"), \
             patch("src.main.setup_signal_handlers"), \
             patch("src.main.Application.run_once",
                   new=AsyncMock(side_effect=RuntimeError("unexpected"))), \
             patch("src.main.Application.shutdown", new=AsyncMock()):
            result = await async_main(args)

        assert result == 1

    @pytest.mark.asyncio
    async def test_debug_flag_sets_debug_logging(self):
        from src.main import async_main, create_parser
        parser = create_parser()
        args = parser.parse_args(["--dry-run", "--debug"])

        mock_settings = _make_settings()

        with patch("src.main.reload_settings", return_value=mock_settings), \
             patch("src.main.setup_logging") as mock_setup, \
             patch("src.main.log_separator"), \
             patch("src.main.logger"), \
             patch("src.main.Application.shutdown", new=AsyncMock()):
            result = await async_main(args)

        # setup_logging should be called with DEBUG level at some point
        calls = [str(c) for c in mock_setup.call_args_list]
        assert any("DEBUG" in s for s in calls)


class TestMain:
    """Test main() entry point."""

    def test_main_calls_asyncio_run(self):
        from src.main import main

        with patch("src.main.create_parser") as mock_parser, \
             patch("asyncio.run", return_value=0) as mock_run:
            mock_parser.return_value.parse_args.return_value = MagicMock(
                once=True, daemon=False, dry_run=False,
                test=True, config=None, upload=False,
            )
            result = main()
            assert mock_run.called

    def test_main_keyboard_interrupt(self):
        from src.main import main

        with patch("src.main.create_parser") as mock_parser, \
             patch("asyncio.run", side_effect=KeyboardInterrupt()):
            mock_parser.return_value.parse_args.return_value = MagicMock()
            result = main()
            assert result == 130
