"""
Content Generation module - Creates scripts and content from trends.

This module handles:
- AI-powered script generation
- Template-based content creation
- Content optimization for engagement
- Multi-format output generation
"""

from src.content_generation.models import (
    Hook,
    Script,
    SceneTransition,
    SceneType,
    ScriptGenerationRequest,
    ScriptGenerationResult,
    VideoScene,
)
from src.content_generation.niche_selector import (
    HISTORICAL_MYSTERY,
    OBSCURE_FACT,
    PRODUCTIVITY_HACK,
    NicheDefinition,
    NicheSelector,
)
from src.content_generation.script_generator import ScriptGenerator

__all__ = [
    # Models
    "Hook",
    "Script",
    "VideoScene",
    "SceneTransition",
    "SceneType",
    "ScriptGenerationRequest",
    "ScriptGenerationResult",
    # Niches
    "NicheDefinition",
    "NicheSelector",
    "HISTORICAL_MYSTERY",
    "PRODUCTIVITY_HACK",
    "OBSCURE_FACT",
    # Generator
    "ScriptGenerator",
]
