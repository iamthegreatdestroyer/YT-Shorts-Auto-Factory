"""
Main entry point for the YouTube Shorts Automation Factory.

This module provides the CLI interface and application lifecycle management
for running the video generation pipeline.

Usage:
    # Run once and exit
    python -m src.main --once

    # Run as daemon with scheduling
    python -m src.main --daemon

    # Run in test mode (no upload)
    python -m src.main --once --no-upload

    # Dry run (validate config only)
    python -m src.main --dry-run
"""

from __future__ import annotations

import argparse
import asyncio
import signal
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Optional

from src import __version__
from src.core.config import Settings, get_settings, reload_settings
from src.core.exceptions import (
    ConfigurationError,
    PipelineError,
    YTShortsError,
)
from src.monitoring.logger import (
    logger,
    log_separator,
    pipeline_context,
    setup_logging,
)


# =============================================================================
# Application Class
# =============================================================================


class Application:
    """
    Main application class that manages the video generation lifecycle.

    Handles:
    - Configuration loading and validation
    - Logging setup
    - Pipeline execution (one-time or scheduled)
    - Graceful shutdown
    """

    def __init__(
        self,
        config_path: Optional[Path] = None,
        test_mode: bool = False,
        no_upload: bool = False,
    ) -> None:
        """
        Initialize the application.

        Args:
            config_path: Optional path to configuration file.
            test_mode: If True, run in test mode with mock services.
            no_upload: If True, generate video but skip upload.
        """
        self.config_path = config_path
        self.test_mode = test_mode
        self.no_upload = no_upload
        self.settings: Optional[Settings] = None
        self._shutdown_event = asyncio.Event()
        self._scheduler: Optional[Any] = None

    def load_settings(self) -> Settings:
        """
        Load and validate application settings.

        Returns:
            Validated settings instance.

        Raises:
            ConfigurationError: If settings are invalid.
        """
        try:
            # Reload settings to pick up any changes
            self.settings = reload_settings()

            # Validate critical settings
            self._validate_settings()

            return self.settings

        except Exception as e:
            raise ConfigurationError(
                f"Failed to load settings: {e}",
                original_error=e,
            ) from e

    def _validate_settings(self) -> None:
        """Validate that required settings are configured."""
        if self.settings is None:
            raise ConfigurationError("Settings not loaded")

        # Check API keys if not in test mode
        if not self.test_mode:
            api_status = self.settings.validate_api_keys()
            missing_apis = [name for name, configured in api_status.items() if not configured]

            # Log warnings for missing optional APIs
            for api_name in missing_apis:
                logger.warning(f"API not configured: {api_name}")

    def setup(self) -> None:
        """Set up the application (logging, directories, etc.)."""
        # Load settings first
        self.load_settings()

        if self.settings is None:
            raise ConfigurationError("Settings not loaded")

        # Set up logging
        setup_logging(
            log_level=self.settings.app.log_level.value,
            log_dir=self.settings.storage.logs_path,
            console_enabled=True,
        )

        # Ensure directories exist
        self.settings.storage.ensure_directories()

        # Log startup information
        log_separator("YouTube Shorts Factory Starting", char="=")
        logger.info(f"Version: {__version__}")
        logger.info(f"Environment: {self.settings.app.environment.value}")
        logger.info(f"Debug Mode: {self.settings.app.debug}")
        logger.info(f"Test Mode: {self.test_mode}")
        logger.info(f"No Upload: {self.no_upload}")
        log_separator()

    async def run_once(self) -> dict[str, Any]:
        """
        Run the video generation pipeline once.

        Returns:
            Dictionary with pipeline result information.
        """
        if self.settings is None:
            raise ConfigurationError("Application not set up. Call setup() first.")

        with pipeline_context("video_generation") as run_id:
            logger.info(f"Starting single pipeline run | run_id={run_id}")

            try:
                # Import pipeline here to avoid circular imports
                from src.core.pipeline import Pipeline

                # Initialize pipeline
                pipeline = Pipeline(
                    settings=self.settings,
                    test_mode=self.test_mode,
                    no_upload=self.no_upload,
                )

                # Execute pipeline
                result = await pipeline.run()

                logger.info(
                    f"Pipeline completed successfully | "
                    f"run_id={run_id} | "
                    f"video_id={result.get('video_id', 'N/A')}"
                )

                return result

            except YTShortsError as e:
                logger.error(f"Pipeline failed | run_id={run_id} | error={e}")
                raise

            except Exception as e:
                logger.exception(f"Unexpected error in pipeline | run_id={run_id}")
                raise PipelineError(
                    f"Pipeline failed unexpectedly: {e}",
                    pipeline_name="video_generation",
                    run_id=run_id,
                    original_error=e,
                ) from e

    async def run_daemon(self) -> None:
        """
        Run the application as a daemon with scheduled execution.

        This method runs indefinitely until interrupted.
        """
        if self.settings is None:
            raise ConfigurationError("Application not set up. Call setup() first.")

        logger.info("Starting daemon mode...")

        try:
            # Import scheduler
            from apscheduler.schedulers.asyncio import AsyncIOScheduler
            from apscheduler.triggers.cron import CronTrigger

            # Create scheduler
            self._scheduler = AsyncIOScheduler(
                timezone=self.settings.schedule.timezone,
            )

            # Parse cron expressions and add jobs
            if self.settings.schedule.enabled:
                # Video generation job
                gen_trigger = CronTrigger.from_crontab(
                    self.settings.schedule.generation_cron
                )
                self._scheduler.add_job(
                    self._scheduled_generation,
                    trigger=gen_trigger,
                    id="video_generation",
                    name="Video Generation",
                    replace_existing=True,
                )
                logger.info(
                    f"Scheduled video generation: {self.settings.schedule.generation_cron}"
                )

                # Upload job (if different from generation)
                if self.settings.schedule.upload_cron != self.settings.schedule.generation_cron:
                    upload_trigger = CronTrigger.from_crontab(
                        self.settings.schedule.upload_cron
                    )
                    self._scheduler.add_job(
                        self._scheduled_upload,
                        trigger=upload_trigger,
                        id="video_upload",
                        name="Video Upload",
                        replace_existing=True,
                    )
                    logger.info(
                        f"Scheduled video upload: {self.settings.schedule.upload_cron}"
                    )

            # Health check job (every 5 minutes)
            self._scheduler.add_job(
                self._health_check,
                trigger="interval",
                minutes=5,
                id="health_check",
                name="Health Check",
                replace_existing=True,
            )

            # Start scheduler
            self._scheduler.start()
            logger.info("Scheduler started. Waiting for scheduled jobs...")

            # Print next run times
            for job in self._scheduler.get_jobs():
                logger.info(
                    f"Job '{job.name}' next run: {job.next_run_time}"
                )

            # Wait for shutdown signal
            await self._shutdown_event.wait()

        except KeyboardInterrupt:
            logger.info("Keyboard interrupt received. Shutting down...")
        finally:
            await self.shutdown()

    async def _scheduled_generation(self) -> None:
        """Execute scheduled video generation."""
        logger.info("Scheduled video generation triggered")
        try:
            await self.run_once()
        except Exception as e:
            logger.error(f"Scheduled generation failed: {e}")

    async def _scheduled_upload(self) -> None:
        """Execute scheduled video upload."""
        logger.info("Scheduled upload triggered")
        # TODO: Implement upload queue processing
        logger.warning("Scheduled upload not yet implemented")

    async def _health_check(self) -> None:
        """Perform periodic health check."""
        logger.debug("Health check: OK")
        # TODO: Add actual health checks
        # - Check disk space
        # - Check API connectivity
        # - Check database connection

    async def shutdown(self) -> None:
        """Gracefully shut down the application."""
        log_separator("Shutting Down", char="-")

        # Stop scheduler if running
        if self._scheduler is not None:
            logger.info("Stopping scheduler...")
            self._scheduler.shutdown(wait=True)

        # Cleanup temp files
        if self.settings is not None:
            logger.info("Cleaning up temporary files...")
            # TODO: Implement cleanup

        logger.info("Shutdown complete")

    def request_shutdown(self) -> None:
        """Request application shutdown (from signal handler)."""
        logger.info("Shutdown requested")
        self._shutdown_event.set()


# =============================================================================
# CLI Interface
# =============================================================================


def create_parser() -> argparse.ArgumentParser:
    """
    Create the command-line argument parser.

    Returns:
        Configured ArgumentParser instance.
    """
    parser = argparse.ArgumentParser(
        prog="yt-shorts-factory",
        description="YouTube Shorts Automation Factory - Generate and upload viral short-form content",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s --once                 Generate one video and exit
  %(prog)s --daemon               Run as daemon with scheduling
  %(prog)s --once --no-upload     Generate without uploading
  %(prog)s --dry-run              Validate configuration only
  %(prog)s --version              Show version and exit

For more information, visit: https://github.com/YTShortsFactory
        """,
    )

    # Version
    parser.add_argument(
        "-V", "--version",
        action="version",
        version=f"%(prog)s {__version__}",
    )

    # Execution modes (mutually exclusive)
    mode_group = parser.add_mutually_exclusive_group(required=True)

    mode_group.add_argument(
        "--once",
        action="store_true",
        help="Run the pipeline once and exit",
    )

    mode_group.add_argument(
        "--daemon",
        action="store_true",
        help="Run as daemon with scheduled execution",
    )

    mode_group.add_argument(
        "--dry-run",
        action="store_true",
        help="Validate configuration and exit",
    )

    # Optional arguments
    parser.add_argument(
        "-c", "--config",
        type=Path,
        metavar="PATH",
        help="Path to configuration file (default: config/config.yaml)",
    )

    parser.add_argument(
        "--test",
        action="store_true",
        help="Run in test mode with mock services",
    )

    parser.add_argument(
        "--no-upload",
        action="store_true",
        help="Generate video but skip YouTube upload",
    )

    parser.add_argument(
        "--debug",
        action="store_true",
        help="Enable debug logging",
    )

    parser.add_argument(
        "-v", "--verbose",
        action="count",
        default=0,
        help="Increase verbosity (-v for INFO, -vv for DEBUG)",
    )

    return parser


def setup_signal_handlers(app: Application) -> None:
    """
    Set up signal handlers for graceful shutdown.

    Args:
        app: Application instance to handle shutdown.
    """
    def signal_handler(signum: int, frame: Any) -> None:
        signal_name = signal.Signals(signum).name
        logger.info(f"Received signal {signal_name}")
        app.request_shutdown()

    # Register signal handlers
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    # On Windows, also handle CTRL+C and CTRL+BREAK
    if sys.platform == "win32":
        signal.signal(signal.SIGBREAK, signal_handler)


async def async_main(args: argparse.Namespace) -> int:
    """
    Async main function.

    Args:
        args: Parsed command-line arguments.

    Returns:
        Exit code (0 for success, non-zero for failure).
    """
    # Create application
    app = Application(
        config_path=args.config,
        test_mode=args.test,
        no_upload=args.no_upload,
    )

    try:
        # Set up the application
        app.setup()

        # Override log level based on verbosity
        if args.debug or args.verbose >= 2:
            setup_logging(log_level="DEBUG")
        elif args.verbose == 1:
            setup_logging(log_level="INFO")

        # Execute based on mode
        if args.dry_run:
            logger.info("Dry run - configuration is valid")
            print("\n✅ Configuration validated successfully!")
            print(f"\nSettings summary:")
            print(f"  Environment: {app.settings.app.environment.value}")
            print(f"  Niche: {app.settings.content.niche}")
            print(f"  Target Duration: {app.settings.content.target_duration}s")
            print(f"  TTS Provider: {app.settings.tts.provider.value}")
            print(f"  Image Provider: {app.settings.image.provider.value}")
            return 0

        # Set up signal handlers
        setup_signal_handlers(app)

        if args.once:
            # Run once
            result = await app.run_once()
            if result.get("success", False):
                print(f"\n✅ Video generated successfully!")
                if result.get("video_path"):
                    print(f"   Video: {result['video_path']}")
                if result.get("video_id"):
                    print(f"   YouTube ID: {result['video_id']}")
                return 0
            else:
                print(f"\n❌ Video generation failed: {result.get('error', 'Unknown error')}")
                return 1

        elif args.daemon:
            # Run as daemon
            await app.run_daemon()
            return 0

    except ConfigurationError as e:
        logger.error(f"Configuration error: {e}")
        print(f"\n❌ Configuration error: {e}")
        return 2

    except YTShortsError as e:
        logger.error(f"Application error: {e}")
        print(f"\n❌ Error: {e}")
        return 1

    except KeyboardInterrupt:
        logger.info("Interrupted by user")
        print("\n⚠️  Interrupted by user")
        return 130

    except Exception as e:
        logger.exception("Unexpected error")
        print(f"\n❌ Unexpected error: {e}")
        return 1

    finally:
        await app.shutdown()

    return 0


def main() -> int:
    """
    Main entry point.

    Returns:
        Exit code.
    """
    # Parse arguments
    parser = create_parser()
    args = parser.parse_args()

    # Run async main
    try:
        return asyncio.run(async_main(args))
    except KeyboardInterrupt:
        print("\n⚠️  Interrupted")
        return 130


# =============================================================================
# Script Entry Point
# =============================================================================


if __name__ == "__main__":
    sys.exit(main())
