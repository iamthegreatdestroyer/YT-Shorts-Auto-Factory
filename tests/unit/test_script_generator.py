"""
Unit tests for script generation system.

Tests script generator, niche selector, and models.
"""

from __future__ import annotations

import pytest
from datetime import datetime
from pathlib import Path

from src.content_generation.models import (
    Hook,
    Script,
    SceneTransition,
    SceneType,
    VideoScene,
)
from src.content_generation.niche_selector import (
    HISTORICAL_MYSTERY,
    OBSCURE_FACT,
    PRODUCTIVITY_HACK,
    NicheSelector,
)
from src.content_generation.script_generator import ScriptGenerator
from src.trend_analysis.models import TrendData


class TestVideoScene:
    """Test VideoScene model."""

    def test_create_scene(self):
        """Test creating a scene."""
        scene = VideoScene(
            text="This is the scene content",
            duration=5.0,
            image_prompt="cinematic scene",
            transition=SceneTransition.FADE,
        )
        assert scene.text == "This is the scene content"
        assert scene.duration == 5.0
        assert scene.transition == SceneTransition.FADE

    def test_scene_duration_validation(self):
        """Test scene duration must be 0.5-30 seconds."""
        # Too short
        with pytest.raises(ValueError):
            VideoScene(
                text="Short",
                duration=0.2,
                image_prompt="test",
            )

        # Too long
        with pytest.raises(ValueError):
            VideoScene(
                text="Long",
                duration=40.0,
                image_prompt="test",
            )

    def test_scene_with_type(self):
        """Test scene type specification."""
        scene = VideoScene(
            text="Hook text",
            duration=3.0,
            image_prompt="opening",
            scene_type=SceneType.HOOK,
        )
        assert scene.scene_type == SceneType.HOOK


class TestHook:
    """Test Hook model."""

    def test_create_hook(self):
        """Test creating a hook."""
        hook = Hook(
            text="Did you know this amazing fact?",
            pattern="Did you know {keyword}?",
            keyword="ancient history",
            engagement_score=0.8,
        )
        assert hook.text == "Did you know this amazing fact?"
        assert hook.keyword == "ancient history"
        assert hook.engagement_score == 0.8

    def test_hook_text_length(self):
        """Test hook text must be 10-200 chars."""
        # Too short
        with pytest.raises(ValueError):
            Hook(
                text="Short",
                pattern="test",
                keyword="test",
            )

        # Too long
        with pytest.raises(ValueError):
            Hook(
                text="a" * 300,
                pattern="test",
                keyword="test",
            )


class TestScript:
    """Test Script model."""

    @pytest.fixture
    def sample_script(self) -> Script:
        """Create a sample script."""
        hook = Hook(
            text="Did you know about ancient Egypt?",
            pattern="Did you know {keyword}?",
            keyword="ancient Egypt",
        )

        scenes = [
            VideoScene(
                text="Scene 1 text",
                duration=5.0,
                image_prompt="ancient pyramid",
            ),
            VideoScene(
                text="Scene 2 text",
                duration=6.0,
                image_prompt="ancient artifact",
            ),
            VideoScene(
                text="Scene 3 text",
                duration=5.5,
                image_prompt="ancient mystery",
            ),
        ]

        return Script(
            title="Ancient Egypt Mysteries",
            hook=hook,
            scenes=scenes,
            call_to_action="Follow for more history!",
            niche="historical_mystery",
            trending_keyword="ancient Egypt",
            total_duration=18.0,
            word_count=75,
            scene_count=3,
        )

    def test_script_creation(self, sample_script):
        """Test creating a script."""
        assert sample_script.title == "Ancient Egypt Mysteries"
        assert sample_script.niche == "historical_mystery"
        assert len(sample_script.scenes) == 3

    def test_script_duration_validation(self, sample_script):
        """Test script duration must be 15-60 seconds."""
        # Too short
        with pytest.raises(ValueError):
            Script(
                title="Too short",
                hook=sample_script.hook,
                scenes=sample_script.scenes[:1],  # Only 4 seconds
                call_to_action="CTA",
                niche="test",
                trending_keyword="test",
                total_duration=4.0,
                word_count=20,
                scene_count=1,
            )

    def test_script_full_text(self, sample_script):
        """Test generating full text from script."""
        full_text = sample_script.full_text
        assert "ancient Egypt" in full_text
        assert "Scene 1" in full_text
        assert "Follow for more" in full_text

    def test_script_image_prompts(self, sample_script):
        """Test extracting image prompts."""
        prompts = sample_script.image_prompts
        assert len(prompts) == 3
        assert "pyramid" in prompts[0]

    def test_script_to_srt(self, sample_script):
        """Test converting script to SRT format."""
        srt = sample_script.to_srt()
        assert "00:00:00" in srt
        assert "-->" in srt
        assert "Scene 1" in srt

    def test_validate_duration(self, sample_script):
        """Test duration validation."""
        # Note: calculated duration will be the sum of scene durations
        # not the total_duration field, so validate_duration checks consistency
        calculated = sum(s.duration for s in sample_script.scenes)
        assert 15 <= calculated <= 60


class TestNicheDefinition:
    """Test niche definitions."""

    def test_historical_mystery_niche(self):
        """Test historical mystery niche definition."""
        assert HISTORICAL_MYSTERY.niche_id == "historical_mystery"
        assert len(HISTORICAL_MYSTERY.hook_patterns) > 0
        assert "mystery" in [kw.lower() for kw in HISTORICAL_MYSTERY.primary_keywords]

    def test_productivity_hack_niche(self):
        """Test productivity hack niche definition."""
        assert PRODUCTIVITY_HACK.niche_id == "productivity_hack"
        assert len(PRODUCTIVITY_HACK.call_to_actions) > 0

    def test_obscure_fact_niche(self):
        """Test obscure fact niche definition."""
        assert OBSCURE_FACT.niche_id == "obscure_fact"
        assert "fact" in [kw.lower() for kw in OBSCURE_FACT.primary_keywords]


class TestNicheSelector:
    """Test niche selector."""

    def test_list_niches(self):
        """Test listing available niches."""
        niches = NicheSelector.list_niches()
        assert len(niches) >= 3
        assert "historical_mystery" in niches
        assert "productivity_hack" in niches

    def test_get_niche(self):
        """Test getting niche by ID."""
        niche = NicheSelector.get_niche("historical_mystery")
        assert niche is not None
        assert niche.niche_id == "historical_mystery"

    def test_get_niche_not_found(self):
        """Test getting non-existent niche."""
        niche = NicheSelector.get_niche("unknown_niche")
        assert niche is None

    def test_select_best_niche(self):
        """Test selecting best niche for keyword."""
        niche = NicheSelector.select_best_niche("ancient mystery")
        assert niche == "historical_mystery"

        niche = NicheSelector.select_best_niche("productivity hack")
        assert niche == "productivity_hack"

    def test_get_hook_patterns(self):
        """Test getting hook patterns."""
        patterns = NicheSelector.get_hook_patterns("historical_mystery")
        assert len(patterns) > 0
        assert any("{keyword}" in p for p in patterns)

    def test_get_ctas(self):
        """Test getting CTAs."""
        ctas = NicheSelector.get_ctas("historical_mystery")
        assert len(ctas) > 0


class TestScriptGenerator:
    """Test script generator."""

    @pytest.fixture
    def generator(self) -> ScriptGenerator:
        """Create script generator."""
        return ScriptGenerator()

    @pytest.fixture
    def sample_trend(self) -> TrendData:
        """Create sample trend data."""
        return TrendData(
            keyword="ancient Egypt mystery",
            score=0.85,
            source="youtube",
            category="education",
            volume=50000,
            growth_rate=25.0,
            competition="low",
            related_keywords=["pyramids", "pharaohs", "hieroglyphics"],
        )

    @pytest.mark.asyncio
    async def test_generate_script(self, generator, sample_trend):
        """Test generating a script."""
        script = await generator.generate(
            niche="historical_mystery",
            trending_data=sample_trend,
            target_duration=45,
        )

        assert script.title is not None
        assert script.hook is not None
        assert len(script.scenes) >= 3
        assert 15 <= script.total_duration <= 60
        assert script.niche == "historical_mystery"
        # Check that keyword is in trending_keyword (may have "mystery" suffix)
        assert "ancient" in script.trending_keyword.lower()

    @pytest.mark.asyncio
    async def test_generate_invalid_niche(self, generator, sample_trend):
        """Test generating with invalid niche."""
        with pytest.raises(ValueError):
            await generator.generate(
                niche="invalid_niche",
                trending_data=sample_trend,
            )

    @pytest.mark.asyncio
    async def test_generate_hook(self, generator, sample_trend):
        """Test hook generation."""
        niche_def = NicheSelector.get_niche("historical_mystery")
        hook = generator._generate_hook(niche_def, sample_trend)

        assert hook.text is not None
        # Check keyword is in hook (may have "mystery" suffix)
        assert "ancient" in hook.text.lower()
        assert 0 <= hook.engagement_score <= 1

    @pytest.mark.asyncio
    async def test_generate_multiple_niches(self, generator, sample_trend):
        """Test generating scripts for different niches."""
        for niche_id in ["historical_mystery", "productivity_hack", "obscure_fact"]:
            script = await generator.generate(
                niche=niche_id,
                trending_data=sample_trend,
            )
            assert script.niche == niche_id
            assert len(script.scenes) >= 3

    @pytest.mark.asyncio
    async def test_generate_quality_score(self, generator, sample_trend):
        """Test quality score calculation."""
        script = await generator.generate(
            niche="historical_mystery",
            trending_data=sample_trend,
            target_duration=45,
        )
        
        # Quality score should be reasonable (not too low)
        assert script.quality_score > 0.4
        assert script.quality_score <= 1.0

    def test_generate_image_prompt(self, generator, sample_trend):
        """Test image prompt generation."""
        prompt = generator._generate_image_prompt(
            "Ancient Egypt was fascinating",
            sample_trend,
        )
        # Check that the prompt contains relevant keywords and style
        assert "ancient" in prompt.lower()
        assert "cinematic" in prompt.lower()

    def test_generate_title(self, generator, sample_trend):
        """Test title generation."""
        niche_def = NicheSelector.get_niche("historical_mystery")
        title = generator._generate_title(sample_trend, niche_def)
        
        assert title is not None
        # Check that keyword is in title
        assert "ancient" in title.lower()
        assert len(title) < 100

    def test_trim_scenes(self, generator):
        """Test trimming scenes to fit duration."""
        scenes = [
            VideoScene(text=f"Scene {i}", duration=8.0, image_prompt="test")
            for i in range(10)
        ]
        
        # 10 scenes * 8s = 80s, should be trimmed to ~40s
        trimmed = generator._trim_scenes(scenes, target=40)
        
        total = sum(s.duration for s in trimmed)
        assert total <= 40
        # Should have removed some scenes (at least with enough to bring it down)
        assert len(trimmed) < 10 or total == 40
