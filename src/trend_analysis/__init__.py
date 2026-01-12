"""
Trend Analysis module - Monitors and analyzes trending content sources.

This module handles:
- Multi-source trend aggregation (Reddit, Twitter/X, YouTube, Google Trends)
- Trend scoring and prioritization
- Niche relevance filtering
- Trend data caching and persistence

Usage:
    from src.trend_analysis import TrendAnalyzer, TrendData
    
    analyzer = TrendAnalyzer(settings)
    trends = await analyzer.get_trending_topics()
    best_trend = analyzer.select_best_trend(trends)
"""

from src.trend_analysis.analyzer import TrendAnalyzer
from src.trend_analysis.cache import TrendCache
from src.trend_analysis.models import (
    CompetitionLevel,
    ScrapingResult,
    TrendBatch,
    TrendCategory,
    TrendData,
    TrendSource,
)

__all__ = [
    # Main analyzer
    "TrendAnalyzer",
    "TrendCache",
    # Models
    "TrendData",
    "TrendBatch",
    "TrendSource",
    "TrendCategory",
    "CompetitionLevel",
    "ScrapingResult",
]
