"""
YouTube Trends Scraper.

Fetches trending topics from YouTube using the YouTube Data API v3
and/or web scraping of the YouTube Trending page.
"""

from __future__ import annotations

import asyncio
import re
from datetime import datetime
from typing import TYPE_CHECKING, Any, Optional
from urllib.parse import urljoin

import aiohttp
from bs4 import BeautifulSoup
from loguru import logger

from src.core.exceptions import ScrapingError
from src.trend_analysis.base import BaseScraper
from src.trend_analysis.models import (
    CompetitionLevel,
    ScrapingResult,
    TrendCategory,
    TrendData,
    TrendSource,
)

if TYPE_CHECKING:
    from src.core.config import Settings


class YouTubeTrendsScraper(BaseScraper):
    """
    Scraper for YouTube trending content.

    Uses multiple methods to gather trend data:
    1. YouTube Data API v3 (if API key is configured)
    2. Web scraping of YouTube Trending page (fallback)

    The scraper extracts:
    - Trending video titles and keywords
    - View counts and engagement metrics
    - Video categories and tags
    - Channel information
    """

    source = TrendSource.YOUTUBE

    # YouTube URLs
    YOUTUBE_TRENDING_URL = "https://www.youtube.com/feed/trending"
    YOUTUBE_API_BASE = "https://www.googleapis.com/youtube/v3"

    # HTTP headers to mimic browser
    HEADERS = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
            "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        ),
        "Accept-Language": "en-US,en;q=0.9",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    }

    def __init__(self, settings: "Settings") -> None:
        """Initialize YouTube scraper."""
        super().__init__(settings)
        self._api_key: Optional[str] = None
        self._session: Optional[aiohttp.ClientSession] = None

    @property
    def enabled(self) -> bool:
        """Check if YouTube trends is enabled."""
        return self.settings.trends.enable_youtube_trends

    @property
    def has_api_key(self) -> bool:
        """Check if YouTube API key is configured."""
        api_key = self.settings.youtube.api_key.get_secret_value()
        return bool(api_key and len(api_key) > 10)

    async def _get_session(self) -> aiohttp.ClientSession:
        """Get or create aiohttp session."""
        if self._session is None or self._session.closed:
            timeout = aiohttp.ClientTimeout(total=30)
            self._session = aiohttp.ClientSession(
                headers=self.HEADERS,
                timeout=timeout,
            )
        return self._session

    async def close(self) -> None:
        """Close the HTTP session."""
        if self._session and not self._session.closed:
            await self._session.close()

    async def validate_credentials(self) -> bool:
        """Validate YouTube API credentials."""
        if not self.has_api_key:
            logger.debug("No YouTube API key configured")
            return False

        try:
            # Test API with a simple request
            api_key = self.settings.youtube.api_key.get_secret_value()
            url = f"{self.YOUTUBE_API_BASE}/videos"
            params = {
                "part": "snippet",
                "chart": "mostPopular",
                "maxResults": 1,
                "key": api_key,
            }

            session = await self._get_session()
            async with session.get(url, params=params) as response:
                if response.status == 200:
                    logger.info("YouTube API credentials validated")
                    return True
                elif response.status == 403:
                    logger.warning("YouTube API key is invalid or quota exceeded")
                    return False
                else:
                    logger.warning(f"YouTube API validation failed: {response.status}")
                    return False

        except Exception as e:
            logger.error(f"YouTube API validation error: {e}")
            return False

    async def fetch_trends(
        self,
        query: Optional[str] = None,
        max_results: int = 10,
    ) -> ScrapingResult:
        """
        Fetch YouTube trending topics.

        Uses API if available, falls back to web scraping.

        Args:
            query: Optional category filter.
            max_results: Maximum trends to return.

        Returns:
            ScrapingResult with trends.
        """
        trends: list[TrendData] = []
        errors: list[str] = []

        # Try API first if key is available
        if self.has_api_key:
            try:
                api_trends = await self._fetch_via_api(max_results)
                trends.extend(api_trends)
            except Exception as e:
                logger.warning(f"YouTube API fetch failed, trying scraper: {e}")
                errors.append(f"API: {str(e)}")

        # Fallback or supplement with web scraping
        if len(trends) < max_results:
            try:
                scraped_trends = await self._fetch_via_scraping(
                    max_results - len(trends)
                )
                trends.extend(scraped_trends)
            except Exception as e:
                logger.error(f"YouTube scraping failed: {e}")
                errors.append(f"Scrape: {str(e)}")

        if not trends and errors:
            return ScrapingResult(
                success=False,
                source=self.source,
                error="; ".join(errors),
            )

        # Deduplicate by keyword
        seen_keywords: set[str] = set()
        unique_trends: list[TrendData] = []
        for trend in trends:
            keyword_lower = trend.keyword.lower()
            if keyword_lower not in seen_keywords:
                seen_keywords.add(keyword_lower)
                unique_trends.append(trend)

        return ScrapingResult(
            success=True,
            source=self.source,
            trends=unique_trends[:max_results],
        )

    async def _fetch_via_api(self, max_results: int) -> list[TrendData]:
        """
        Fetch trends using YouTube Data API v3.

        Args:
            max_results: Maximum results to fetch.

        Returns:
            List of TrendData from API.
        """
        api_key = self.settings.youtube.api_key.get_secret_value()
        url = f"{self.YOUTUBE_API_BASE}/videos"
        params = {
            "part": "snippet,statistics",
            "chart": "mostPopular",
            "regionCode": "US",
            "maxResults": min(max_results * 2, 50),  # Fetch extra for filtering
            "key": api_key,
        }

        session = await self._get_session()
        async with session.get(url, params=params) as response:
            if response.status != 200:
                text = await response.text()
                raise ScrapingError(
                    f"YouTube API error: {response.status}",
                    context={"response": text[:500]},
                )

            data = await response.json()

        trends: list[TrendData] = []

        for item in data.get("items", []):
            snippet = item.get("snippet", {})
            statistics = item.get("statistics", {})

            # Extract keywords from title
            title = snippet.get("title", "")
            keywords = self._extract_keywords_from_title(title)

            if not keywords:
                continue

            # Get primary keyword
            primary_keyword = keywords[0]

            # Calculate metrics
            view_count = int(statistics.get("viewCount", 0))
            like_count = int(statistics.get("likeCount", 0))
            comment_count = int(statistics.get("commentCount", 0))

            # Estimate volume and growth (simplified)
            volume = view_count
            engagement_rate = (
                (like_count + comment_count) / view_count * 100
                if view_count > 0
                else 0
            )

            # Map YouTube category
            category = self._map_youtube_category(snippet.get("categoryId", ""))

            trends.append(
                TrendData(
                    keyword=primary_keyword,
                    source=self.source,
                    volume=volume,
                    growth_rate=engagement_rate * 10,  # Scale engagement as proxy
                    competition=self._estimate_competition(volume, engagement_rate),
                    category=category,
                    related_keywords=keywords[1:5],
                    description=title,
                    url=f"https://youtube.com/watch?v={item['id']}",
                    raw_data={
                        "video_id": item["id"],
                        "channel": snippet.get("channelTitle"),
                        "published_at": snippet.get("publishedAt"),
                    },
                )
            )

        return trends

    async def _fetch_via_scraping(self, max_results: int) -> list[TrendData]:
        """
        Fetch trends by scraping YouTube trending page.

        Args:
            max_results: Maximum results to fetch.

        Returns:
            List of TrendData from scraping.
        """
        session = await self._get_session()

        try:
            async with session.get(self.YOUTUBE_TRENDING_URL) as response:
                if response.status != 200:
                    raise ScrapingError(
                        f"YouTube trending page returned {response.status}"
                    )
                html = await response.text()

        except aiohttp.ClientError as e:
            raise ScrapingError(f"Failed to fetch YouTube trending: {e}") from e

        trends = self._parse_trending_html(html, max_results)
        return trends

    def _parse_trending_html(self, html: str, max_results: int) -> list[TrendData]:
        """
        Parse YouTube trending page HTML.

        Note: YouTube uses dynamic JS rendering, so this extracts
        initial data from embedded JSON.

        Args:
            html: Raw HTML content.
            max_results: Maximum results to extract.

        Returns:
            List of TrendData.
        """
        trends: list[TrendData] = []

        # Try to find ytInitialData JSON
        pattern = r'var ytInitialData = ({.*?});'
        match = re.search(pattern, html)

        if match:
            try:
                import json

                data = json.loads(match.group(1))
                trends = self._extract_trends_from_initial_data(data, max_results)
            except (json.JSONDecodeError, KeyError) as e:
                logger.warning(f"Failed to parse ytInitialData: {e}")

        # Fallback: parse visible HTML elements
        if not trends:
            trends = self._extract_trends_from_html(html, max_results)

        return trends

    def _extract_trends_from_initial_data(
        self,
        data: dict[str, Any],
        max_results: int,
    ) -> list[TrendData]:
        """Extract trends from YouTube's initial data JSON."""
        trends: list[TrendData] = []

        try:
            # Navigate to trending content
            tabs = data.get("contents", {}).get(
                "twoColumnBrowseResultsRenderer", {}
            ).get("tabs", [])

            for tab in tabs:
                content = tab.get("tabRenderer", {}).get("content", {})
                section_list = content.get("sectionListRenderer", {})
                contents = section_list.get("contents", [])

                for section in contents:
                    items = (
                        section.get("itemSectionRenderer", {})
                        .get("contents", [{}])[0]
                        .get("shelfRenderer", {})
                        .get("content", {})
                        .get("expandedShelfContentsRenderer", {})
                        .get("items", [])
                    )

                    for item in items:
                        video = item.get("videoRenderer", {})
                        if not video:
                            continue

                        title = self._get_text(video.get("title", {}))
                        if not title:
                            continue

                        keywords = self._extract_keywords_from_title(title)
                        if not keywords:
                            continue

                        view_text = self._get_text(video.get("viewCountText", {}))
                        views = self._parse_view_count(view_text)

                        trends.append(
                            TrendData(
                                keyword=keywords[0],
                                source=self.source,
                                volume=views,
                                category=TrendCategory.GENERAL,
                                related_keywords=keywords[1:5],
                                description=title,
                                url=f"https://youtube.com/watch?v={video.get('videoId', '')}",
                            )
                        )

                        if len(trends) >= max_results:
                            return trends

        except Exception as e:
            logger.warning(f"Error extracting from initial data: {e}")

        return trends

    def _extract_trends_from_html(
        self,
        html: str,
        max_results: int,
    ) -> list[TrendData]:
        """Extract trends from HTML using BeautifulSoup."""
        soup = BeautifulSoup(html, "html.parser")
        trends: list[TrendData] = []

        # Look for video titles in various elements
        title_selectors = [
            "a#video-title",
            "h3.title-and-badge a",
            "span#video-title",
        ]

        for selector in title_selectors:
            elements = soup.select(selector)
            for elem in elements:
                title = elem.get_text(strip=True)
                if not title or len(title) < 5:
                    continue

                keywords = self._extract_keywords_from_title(title)
                if not keywords:
                    continue

                href = elem.get("href", "")
                url = urljoin("https://youtube.com", href) if href else None

                trends.append(
                    TrendData(
                        keyword=keywords[0],
                        source=self.source,
                        category=TrendCategory.GENERAL,
                        related_keywords=keywords[1:5],
                        description=title,
                        url=url,
                    )
                )

                if len(trends) >= max_results:
                    break

            if len(trends) >= max_results:
                break

        return trends

    def _extract_keywords_from_title(self, title: str) -> list[str]:
        """
        Extract meaningful keywords from a video title.

        Args:
            title: Video title.

        Returns:
            List of keywords.
        """
        if not title:
            return []

        # Remove common noise patterns
        clean = re.sub(r'\|.*$', '', title)  # Remove after |
        clean = re.sub(r'-.*$', '', clean)   # Remove after -
        clean = re.sub(r'\[.*?\]', '', clean)  # Remove [brackets]
        clean = re.sub(r'\(.*?\)', '', clean)  # Remove (parentheses)
        clean = re.sub(r'#\w+', '', clean)    # Remove hashtags
        clean = re.sub(r'@\w+', '', clean)    # Remove mentions

        # Tokenize and filter
        words = clean.split()
        stop_words = {
            "the", "a", "an", "and", "or", "but", "in", "on", "at", "to",
            "for", "of", "with", "by", "from", "is", "are", "was", "were",
            "be", "been", "being", "have", "has", "had", "do", "does", "did",
            "will", "would", "could", "should", "may", "might", "must",
            "this", "that", "these", "those", "i", "you", "he", "she", "it",
            "we", "they", "what", "which", "who", "whom", "how", "when",
            "where", "why", "just", "only", "very", "really", "so", "too",
            "official", "video", "music", "new", "full", "episode",
        }

        keywords: list[str] = []
        for word in words:
            word = word.strip(".,!?\"'")
            if (
                len(word) >= 3
                and word.lower() not in stop_words
                and not word.isdigit()
            ):
                keywords.append(word)

        # Also extract multi-word phrases (bigrams)
        if len(keywords) >= 2:
            for i in range(len(keywords) - 1):
                bigram = f"{keywords[i]} {keywords[i+1]}"
                if len(bigram) <= 50:
                    keywords.insert(0, bigram)

        return keywords[:10]

    def _map_youtube_category(self, category_id: str) -> TrendCategory:
        """Map YouTube category ID to TrendCategory."""
        mapping = {
            "1": TrendCategory.ENTERTAINMENT,  # Film & Animation
            "2": TrendCategory.GENERAL,        # Autos & Vehicles
            "10": TrendCategory.MUSIC,         # Music
            "15": TrendCategory.GENERAL,       # Pets & Animals
            "17": TrendCategory.SPORTS,        # Sports
            "18": TrendCategory.ENTERTAINMENT, # Short Movies
            "19": TrendCategory.LIFESTYLE,     # Travel & Events
            "20": TrendCategory.GAMING,        # Gaming
            "22": TrendCategory.GENERAL,       # People & Blogs
            "23": TrendCategory.ENTERTAINMENT, # Comedy
            "24": TrendCategory.ENTERTAINMENT, # Entertainment
            "25": TrendCategory.NEWS,          # News & Politics
            "26": TrendCategory.EDUCATION,     # Howto & Style
            "27": TrendCategory.EDUCATION,     # Education
            "28": TrendCategory.SCIENCE,       # Science & Technology
        }
        return mapping.get(category_id, TrendCategory.GENERAL)

    def _get_text(self, obj: dict[str, Any]) -> str:
        """Extract text from YouTube's text object."""
        if not obj:
            return ""
        if "simpleText" in obj:
            return obj["simpleText"]
        if "runs" in obj:
            return "".join(run.get("text", "") for run in obj["runs"])
        return ""

    def _parse_view_count(self, text: str) -> int:
        """Parse view count from text like '1.2M views'."""
        if not text:
            return 0

        text = text.lower().replace(",", "").replace(" views", "").strip()

        try:
            if "k" in text:
                return int(float(text.replace("k", "")) * 1000)
            elif "m" in text:
                return int(float(text.replace("m", "")) * 1000000)
            elif "b" in text:
                return int(float(text.replace("b", "")) * 1000000000)
            else:
                return int(text)
        except (ValueError, TypeError):
            return 0
