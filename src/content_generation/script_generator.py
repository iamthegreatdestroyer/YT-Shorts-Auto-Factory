"""
Main script generator using Jinja2 templates.

Generates video scripts for different niches using template-based approach.
Can be extended with LLM integration in the future.
"""

from __future__ import annotations

import random
import time
from datetime import datetime
from pathlib import Path
from typing import Optional

from jinja2 import Environment, FileSystemLoader, TemplateNotFound
from loguru import logger

from src.content_generation.models import Hook, Script, SceneTransition, VideoScene
from src.content_generation.niche_selector import NicheSelector
from src.trend_analysis.models import TrendData


class ScriptGenerator:
    """
    Generates video scripts using Jinja2 templates.
    
    Supports multiple niches with customizable templates.
    Can be extended to use LLM for dynamic generation.
    """

    def __init__(self, template_dir: Optional[Path] = None):
        """
        Initialize script generator.
        
        Args:
            template_dir: Path to templates directory
        """
        if template_dir is None:
            # Default to src/content_generation/templates
            template_dir = Path(__file__).parent / "templates"
        
        self.template_dir = template_dir
        self.env = Environment(
            loader=FileSystemLoader(template_dir),
            trim_blocks=True,
            lstrip_blocks=True,
            autoescape=False,
        )
        
        logger.info(f"ScriptGenerator initialized with templates from {template_dir}")

    async def generate(
        self,
        niche: str,
        trending_data: TrendData,
        target_duration: float = 45,
        style: Optional[str] = None,
    ) -> Script:
        """
        Generate a complete video script.
        
        Args:
            niche: Content niche (e.g., 'historical_mystery')
            trending_data: TrendData with keyword and metadata
            target_duration: Target video length (15-60 seconds)
            style: Optional style override
            
        Returns:
            Complete Script object
            
        Raises:
            ValueError: If niche not found or generation fails
        """
        start_time = time.time()
        
        niche_def = NicheSelector.get_niche(niche)
        if not niche_def:
            raise ValueError(f"Unknown niche: {niche}")
        
        logger.info(f"Generating script for {niche}: {trending_data.keyword}")
        
        # Generate hook
        hook = self._generate_hook(niche_def, trending_data)
        
        # Generate body scenes
        scenes = await self._generate_scenes(
            niche, niche_def, trending_data, target_duration, hook
        )
        
        # Generate call-to-action
        cta = self._select_cta(niche_def)
        
        # Calculate metrics
        total_duration = sum(s.duration for s in scenes)
        full_text = hook.text + " " + " ".join(s.text for s in scenes) + " " + cta
        word_count = len(full_text.split())
        
        # Trim if exceeds duration
        if total_duration > 60:
            scenes = self._trim_scenes(scenes, target=58)
            total_duration = sum(s.duration for s in scenes)
        
        generation_time_ms = (time.time() - start_time) * 1000
        
        script = Script(
            title=self._generate_title(trending_data, niche_def),
            hook=hook,
            scenes=scenes,
            call_to_action=cta,
            niche=niche,
            trending_keyword=trending_data.keyword,
            related_keywords=trending_data.related_keywords[:5],
            total_duration=total_duration,
            word_count=word_count,
            scene_count=len(scenes),
            created_at=datetime.utcnow(),
            generated_by="template_engine",
            quality_score=self._calculate_quality_score(script=None, niche_def=niche_def),
        )
        
        logger.info(
            f"Generated script: {total_duration:.1f}s, {len(scenes)} scenes, "
            f"{word_count} words ({generation_time_ms:.0f}ms)"
        )
        
        return script

    def _generate_hook(self, niche_def, trending_data: TrendData) -> Hook:
        """Generate attention-grabbing hook."""
        patterns = niche_def.hook_patterns
        pattern = random.choice(patterns)
        text = pattern.replace("{keyword}", trending_data.keyword)
        
        # Calculate engagement score based on keyword strength
        engagement = min(trending_data.score + random.uniform(-0.2, 0.2), 1.0)
        
        return Hook(
            text=text,
            pattern=pattern,
            keyword=trending_data.keyword,
            engagement_score=max(0, engagement),
        )

    async def _generate_scenes(
        self,
        niche: str,
        niche_def,
        trending_data: TrendData,
        target_duration: float,
        hook: Hook,
    ) -> list[VideoScene]:
        """Generate scene sequence."""
        scenes = []
        
        # Estimate scenes needed (avg 5 seconds per scene)
        num_scenes = min(int(target_duration / 5), niche_def.max_scenes)
        num_scenes = max(num_scenes, niche_def.min_scenes)
        
        # Try to load template
        template_name = f"{niche}.jinja2"
        try:
            template = self.env.get_template(template_name)
            rendered = template.render(
                keyword=trending_data.keyword,
                fact1="Key insight about the topic",
                fact2="Another interesting angle",
                fact3="Surprising additional fact",
                theory="Leading scientific explanation",
                context1="The discovery context",
                implication1="What this means",
                reason1="Primary reason",
                reason2="Secondary reason",
                tip1="The main tip or hack",
                time_required="5 minutes",
                benefit="improved productivity",
            )
        except TemplateNotFound:
            logger.warning(f"Template not found: {template_name}, using fallback")
            rendered = self._generate_fallback_content(niche, trending_data)
        
        # Split content into scenes
        content_lines = [line.strip() for line in rendered.split("\n") if line.strip()]
        
        lines_per_scene = max(1, len(content_lines) // num_scenes)
        
        for i in range(num_scenes):
            start_idx = i * lines_per_scene
            end_idx = (i + 1) * lines_per_scene if i < num_scenes - 1 else len(content_lines)
            
            scene_text = " ".join(content_lines[start_idx:end_idx])
            
            if not scene_text:
                continue
            
            # Estimate duration from word count (reading speed ~2.5 words/sec)
            word_count = len(scene_text.split())
            duration = (word_count / 2.5) + 0.5  # +0.5s for visual processing
            duration = min(max(duration, 2.0), 12.0)  # Clamp 2-12 seconds
            
            scene = VideoScene(
                text=scene_text,
                duration=duration,
                image_prompt=self._generate_image_prompt(scene_text, trending_data),
                transition=SceneTransition.FADE if i > 0 else SceneTransition.NONE,
                visual_style=niche_def.visual_style,
            )
            scenes.append(scene)
        
        return scenes

    def _generate_image_prompt(self, scene_text: str, trending_data: TrendData) -> str:
        """Generate Stable Diffusion prompt for scene."""
        # Simple approach: use keywords + base style
        base_style = "cinematic lighting, highly detailed, 4k, dramatic"
        
        # Extract first few words as scene descriptor
        words = scene_text.split()[:5]
        descriptor = " ".join(words) if words else trending_data.keyword
        
        return f"{descriptor}, related to {trending_data.keyword}, {base_style}"

    def _generate_title(self, trending_data: TrendData, niche_def) -> str:
        """Generate SEO-optimized title."""
        templates = [
            f"The Truth About {trending_data.keyword}",
            f"{trending_data.keyword}: What Nobody Tells You",
            f"Why {trending_data.keyword} Is Trending Right Now",
            f"This {trending_data.keyword} Secret Will Shock You",
        ]
        return random.choice(templates)

    def _select_cta(self, niche_def) -> str:
        """Select call-to-action."""
        cta = random.choice(niche_def.call_to_actions)
        return cta

    def _generate_fallback_content(self, niche: str, trending_data: TrendData) -> str:
        """Generate fallback content if template not found."""
        fallback = f"""
        Let me tell you about {trending_data.keyword}.
        
        This is one of the most important topics in {niche}.
        
        Here's what you need to know:
        
        First, {trending_data.keyword} is complex.
        
        But the key insight is straightforward.
        
        Many people misunderstand {trending_data.keyword}.
        
        That's because it requires context.
        
        When you understand the background, everything makes sense.
        
        The implications are significant.
        
        This affects your daily life more than you think.
        
        Now you're equipped with the real knowledge.
        """
        return fallback

    def _trim_scenes(self, scenes: list[VideoScene], target: float) -> list[VideoScene]:
        """Trim scenes to fit target duration."""
        current_duration = sum(s.duration for s in scenes)
        
        if current_duration <= target:
            return scenes
        
        # Remove scenes from end until within target
        num_removed = 0
        while current_duration > target and len(scenes) > 3:
            removed = scenes.pop()
            current_duration -= removed.duration
            num_removed += 1
        
        if num_removed > 0:
            logger.debug(f"Trimmed {num_removed} scenes to reach {current_duration:.1f}s target")
        return scenes

    def _calculate_quality_score(self, script: Optional[Script] = None, niche_def=None) -> float:
        """Calculate script quality score."""
        if script is None:
            return 0.7  # Default score for new scripts
        
        score = 0.5
        
        # Check duration (50-60s is ideal)
        if 45 <= script.total_duration <= 60:
            score += 0.2
        
        # Check scene count (5-8 scenes optimal)
        if 5 <= script.scene_count <= 8:
            score += 0.15
        
        # Check word count (reasonable for Shorts)
        if 100 <= script.word_count <= 300:
            score += 0.15
        
        return min(score, 1.0)
