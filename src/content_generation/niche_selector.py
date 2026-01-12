"""
Niche selector - matches content to niches and applies niche-specific rules.

Provides niche definitions, keyword matching, and style selection.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

from pydantic import BaseModel, Field


class NicheDefinition(BaseModel):
    """Definition of a content niche."""

    niche_id: str = Field(..., description="Unique niche identifier")
    name: str = Field(..., description="Human-readable niche name")
    description: str = Field(..., description="What this niche is about")
    
    # Keywords
    primary_keywords: list[str] = Field(
        ..., description="Primary keywords for this niche"
    )
    category_keywords: list[str] = Field(
        default_factory=list, description="Related category keywords"
    )
    
    # Hook patterns
    hook_patterns: list[str] = Field(
        ..., description="Hook template patterns for this niche"
    )
    
    # Scene structure
    min_scenes: int = Field(default=3, ge=1)
    max_scenes: int = Field(default=8, le=20)
    recommended_scene_duration: float = Field(default=5.0, ge=2, le=15)
    
    # Content style
    tone: str = Field(default="informative", description="Content tone/style")
    visual_style: str = Field(
        default="cinematic", description="Recommended visual style"
    )
    
    # CTAs specific to niche
    call_to_actions: list[str] = Field(
        default_factory=list, description="Niche-specific CTAs"
    )


# Built-in niches
HISTORICAL_MYSTERY = NicheDefinition(
    niche_id="historical_mystery",
    name="Historical Mystery",
    description="Mysterious historical events, unsolved cases, archaeological discoveries",
    primary_keywords=[
        "mystery",
        "history",
        "ancient",
        "unsolved",
        "archaeological",
        "discovery",
        "secret",
    ],
    category_keywords=["civilization", "artifact", "legend", "folklore", "conspiracy"],
    hook_patterns=[
        "This {keyword} mystery has baffled historians for centuries",
        "The truth about {keyword} will shock you",
        "What really happened with {keyword}?",
        "Historians are still confused about {keyword}",
        "This {keyword} secret was hidden for 1000+ years",
    ],
    tone="mysterious,intriguing,educational",
    visual_style="cinematic,dramatic,historical",
    call_to_actions=[
        "Like if you love history mysteries!",
        "Follow for more unsolved mysteries!",
        "Share this with a history buff!",
        "What do YOU think happened?",
    ],
)

PRODUCTIVITY_HACK = NicheDefinition(
    niche_id="productivity_hack",
    name="Productivity Hack",
    description="Life hacks, productivity tips, time management, efficiency tricks",
    primary_keywords=[
        "productivity",
        "hack",
        "efficiency",
        "time management",
        "life hack",
        "tip",
        "trick",
        "shortcut",
    ],
    category_keywords=["organization", "routine", "optimization", "workflow", "mindset"],
    hook_patterns=[
        "This {keyword} trick changed my life",
        "The ultimate {keyword} hack you need to know",
        "Stop wasting time with this {keyword} method",
        "This {keyword} will save you hours",
        "The {keyword} secret nobody talks about",
    ],
    tone="motivating,practical,helpful",
    visual_style="clean,modern,minimal",
    call_to_actions=[
        "Try this today and tell me if it works!",
        "Which hack will you try first?",
        "Follow for more life-changing tips!",
        "Save this for later!",
    ],
)

OBSCURE_FACT = NicheDefinition(
    niche_id="obscure_fact",
    name="Obscure Fact",
    description="Amazing facts, mind-blowing trivia, scientific discoveries, weird but true",
    primary_keywords=[
        "fact",
        "trivia",
        "science",
        "nature",
        "technology",
        "discovery",
        "unbelievable",
        "amazing",
    ],
    category_keywords=["biology", "physics", "space", "animal", "weird", "incredible"],
    hook_patterns=[
        "Did you know this about {keyword}?",
        "The surprising truth about {keyword}",
        "This {keyword} fact will blow your mind",
        "You won't believe this {keyword} is real",
        "Most people don't know this about {keyword}",
    ],
    tone="amazed,educational,entertaining",
    visual_style="vibrant,engaging,visual",
    call_to_actions=[
        "Did this blow your mind? Tell me!",
        "Follow for more mind-blowing facts!",
        "Tag someone who needs to see this!",
        "Share if you're amazed!",
    ],
)


class NicheSelector:
    """Selects and manages content niches."""

    AVAILABLE_NICHES = {
        "historical_mystery": HISTORICAL_MYSTERY,
        "productivity_hack": PRODUCTIVITY_HACK,
        "obscure_fact": OBSCURE_FACT,
    }

    @classmethod
    def get_niche(cls, niche_id: str) -> Optional[NicheDefinition]:
        """Get niche definition by ID."""
        return cls.AVAILABLE_NICHES.get(niche_id.lower())

    @classmethod
    def list_niches(cls) -> list[str]:
        """List all available niche IDs."""
        return list(cls.AVAILABLE_NICHES.keys())

    @classmethod
    def select_best_niche(
        cls, trending_keyword: str, available_niches: Optional[list[str]] = None
    ) -> Optional[str]:
        """
        Select best niche for a trending keyword.
        
        Matches keyword against niche definitions and returns best match.
        """
        if not available_niches:
            available_niches = cls.list_niches()

        best_match = None
        best_score = 0

        keyword_lower = trending_keyword.lower()

        for niche_id in available_niches:
            if niche_id not in cls.AVAILABLE_NICHES:
                continue

            niche = cls.AVAILABLE_NICHES[niche_id]

            # Score based on keyword matches
            score = 0

            # Primary keywords = 3 points
            for kw in niche.primary_keywords:
                if kw.lower() in keyword_lower:
                    score += 3

            # Category keywords = 1 point
            for kw in niche.category_keywords:
                if kw.lower() in keyword_lower:
                    score += 1

            if score > best_score:
                best_score = score
                best_match = niche_id

        return best_match if best_score > 0 else available_niches[0]

    @classmethod
    def get_hook_patterns(cls, niche_id: str) -> list[str]:
        """Get hook patterns for a niche."""
        niche = cls.get_niche(niche_id)
        return niche.hook_patterns if niche else []

    @classmethod
    def get_ctas(cls, niche_id: str) -> list[str]:
        """Get call-to-actions for a niche."""
        niche = cls.get_niche(niche_id)
        return niche.call_to_actions if niche else []
