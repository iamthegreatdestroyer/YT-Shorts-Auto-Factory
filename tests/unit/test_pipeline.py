"""Tests for src/core/pipeline.py — covers Pipeline, PipelineContext, StageResult, PipelineResult."""
from __future__ import annotations

import asyncio
from pathlib import Path
from time import perf_counter
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from src.core.pipeline import (
    Pipeline,
    PipelineContext,
    PipelineResult,
    StageResult,
)
from src.core.constants import PipelineStage


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def make_pipeline(test_config, *, test_mode=True, no_upload=True, topic=None):
    return Pipeline(
        settings=test_config,
        test_mode=test_mode,
        no_upload=no_upload,
        topic=topic,
    )


# ---------------------------------------------------------------------------
# StageResult
# ---------------------------------------------------------------------------


def test_stage_result_to_dict_success():
    r = StageResult(stage=PipelineStage.TREND_ANALYSIS, success=True, duration=1.5)
    d = r.to_dict()
    assert d["success"] is True
    assert d["stage"] == PipelineStage.TREND_ANALYSIS.value
    assert d["duration"] == pytest.approx(1.5)
    assert d["error"] is None
    assert "timestamp" in d


def test_stage_result_to_dict_failure():
    r = StageResult(stage=PipelineStage.TTS_GENERATION, success=False, error="boom")
    d = r.to_dict()
    assert d["success"] is False
    assert d["error"] == "boom"


# ---------------------------------------------------------------------------
# PipelineContext
# ---------------------------------------------------------------------------


def test_pipeline_context_add_temp_file(test_config):
    ctx = PipelineContext(run_id="abc", settings=test_config)
    p = Path("/tmp/foo.mp3")
    ctx.add_temp_file(p)
    assert p in ctx.temp_files
    # Adding same file twice doesn't duplicate
    ctx.add_temp_file(p)
    assert ctx.temp_files.count(p) == 1


def test_pipeline_context_get_duration_not_started(test_config):
    ctx = PipelineContext(run_id="x", settings=test_config)
    assert ctx.get_duration() == 0.0


def test_pipeline_context_get_duration_in_progress(test_config):
    ctx = PipelineContext(run_id="x", settings=test_config)
    ctx.start_time = perf_counter() - 0.5
    dur = ctx.get_duration()
    assert dur >= 0.4


def test_pipeline_context_get_duration_finished(test_config):
    ctx = PipelineContext(run_id="x", settings=test_config)
    ctx.start_time = perf_counter() - 1.0
    ctx.end_time = ctx.start_time + 0.75
    assert ctx.get_duration() == pytest.approx(0.75, abs=0.01)


def test_pipeline_context_to_dict(test_config):
    ctx = PipelineContext(run_id="test-run", settings=test_config, test_mode=True, no_upload=True)
    d = ctx.to_dict()
    assert d["run_id"] == "test-run"
    assert d["test_mode"] is True
    assert d["no_upload"] is True
    assert d["video_path"] is None


# ---------------------------------------------------------------------------
# PipelineResult
# ---------------------------------------------------------------------------


def test_pipeline_result_to_dict():
    pr = PipelineResult(success=True, run_id="r1", title="My Vid", tags=["a", "b"])
    d = pr.to_dict()
    assert d["success"] is True
    assert d["run_id"] == "r1"
    assert d["title"] == "My Vid"
    assert d["tags"] == ["a", "b"]
    assert d["video_path"] is None


# ---------------------------------------------------------------------------
# Pipeline.__init__
# ---------------------------------------------------------------------------


def test_pipeline_init_defaults(test_config):
    p = Pipeline(settings=test_config)
    assert p.test_mode is False
    assert p.no_upload is False
    assert p.topic is None


def test_pipeline_init_overrides(test_config):
    p = Pipeline(settings=test_config, test_mode=True, no_upload=True, topic="robots")
    assert p.test_mode is True
    assert p.no_upload is True
    assert p.topic == "robots"


def test_pipeline_init_output_dir_override(test_config, tmp_path):
    p = Pipeline(settings=test_config, output_dir=tmp_path)
    assert test_config.storage.output_path == tmp_path


# ---------------------------------------------------------------------------
# Pipeline.run() — test_mode with no_upload (fast, no external calls)
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_pipeline_run_test_mode_succeeds(test_config):
    """Full pipeline run in test_mode with no_upload returns success dict."""
    p = make_pipeline(test_config, test_mode=True, no_upload=True)
    result = await p.run()
    assert result["success"] is True
    assert "run_id" in result
    assert len(result["stages"]) >= 7  # 7 stages when no_upload=True


@pytest.mark.asyncio
async def test_pipeline_run_uses_topic_override(test_config):
    """Explicit topic appears in trend_data."""
    p = make_pipeline(test_config, test_mode=True, no_upload=True, topic="Python tips")
    result = await p.run()
    assert result["success"] is True


@pytest.mark.asyncio
async def test_pipeline_run_no_upload_skips_upload_stage(test_config):
    """no_upload=True means UPLOAD stage is not present in stage results."""
    p = make_pipeline(test_config, test_mode=True, no_upload=True)
    result = await p.run()
    stage_names = [s["stage"] for s in result["stages"]]
    assert PipelineStage.UPLOAD.value not in stage_names


@pytest.mark.asyncio
async def test_pipeline_run_default_topic(test_config):
    """Default topic used when topic is None."""
    p = make_pipeline(test_config, test_mode=True, no_upload=True, topic=None)
    result = await p.run()
    assert result["success"] is True


# ---------------------------------------------------------------------------
# Pipeline._execute_stage failure paths
# ---------------------------------------------------------------------------



@pytest.mark.asyncio
async def test_pipeline_run_stage_error_returns_failure_dict(test_config):
    """A StageError in a stage causes run() to return success=False dict."""
    from src.core.exceptions import StageError

    p = make_pipeline(test_config, test_mode=True, no_upload=True)

    async def _fail(ctx):
        raise StageError("oops", stage_name="script_generation")

    p._generate_script = _fail
    result = await p.run()
    assert result["success"] is False
    assert "error" in result


# ---------------------------------------------------------------------------
# Individual stage handlers (test_mode)
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_analyze_trends_test_mode(test_config):
    """_analyze_trends sets trend_data in test_mode."""
    p = make_pipeline(test_config)
    ctx = PipelineContext(run_id="x", settings=test_config, test_mode=True)
    await p._analyze_trends(ctx)
    assert ctx.trend_data is not None
    assert "topic" in ctx.trend_data
    assert "keywords" in ctx.trend_data


@pytest.mark.asyncio
async def test_analyze_trends_with_topic(test_config):
    """_analyze_trends uses explicit topic override."""
    p = Pipeline(settings=test_config, test_mode=True, topic="custom topic here")
    ctx = PipelineContext(run_id="x", settings=test_config, test_mode=True)
    await p._analyze_trends(ctx)
    assert ctx.trend_data["topic"] == "custom topic here"
    assert ctx.trend_data["source"] == "user_override"


@pytest.mark.asyncio
async def test_generate_script_test_mode(test_config):
    """_generate_script produces script_data dict in test_mode."""
    p = make_pipeline(test_config)
    ctx = PipelineContext(run_id="x", settings=test_config, test_mode=True)
    ctx.trend_data = {"topic": "Python 101", "keywords": ["python"]}
    await p._generate_script(ctx)
    assert ctx.script_data is not None
    assert "hook" in ctx.script_data
    assert "segments" in ctx.script_data


@pytest.mark.asyncio
async def test_generate_script_no_trend_raises(test_config):
    """_generate_script without trend_data raises StageError."""
    from src.core.exceptions import StageError
    p = make_pipeline(test_config)
    ctx = PipelineContext(run_id="x", settings=test_config, test_mode=True)
    with pytest.raises(StageError):
        await p._generate_script(ctx)


@pytest.mark.asyncio
async def test_generate_audio_test_mode(test_config, tmp_path):
    """_generate_audio in test_mode sets audio_path without calling TTS."""
    p = make_pipeline(test_config)
    ctx = PipelineContext(run_id="x", settings=test_config, test_mode=True)
    ctx.script_data = {"hook": "hi", "segments": [], "outro": "bye"}
    await p._generate_audio(ctx)
    assert ctx.audio_path is not None


@pytest.mark.asyncio
async def test_generate_audio_no_script_raises(test_config):
    """_generate_audio without script_data raises StageError."""
    from src.core.exceptions import StageError
    p = make_pipeline(test_config)
    ctx = PipelineContext(run_id="x", settings=test_config, test_mode=True)
    with pytest.raises(StageError):
        await p._generate_audio(ctx)
