"""
Reddit Trends Scraper.

Fetches trending topics from Reddit using the Reddit API (PRAW)
and/or JSON API endpoints for unauthenticated access.
"""

from __future__ import annotations

import re
from datetime import datetime
from typing import TYPE_CHECKING, Any, Optional

import aiohttp
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


class RedditScraper(BaseScraper):
    """
    Scraper for Reddit trending content.

    Uses Reddit's public JSON API to fetch hot posts from specified
    subreddits without requiring authentication for basic access.

    For authenticated access (higher rate limits), configure
    Reddit API credentials in settings.

    The scraper extracts:
    - Hot/Rising post titles
    - Post scores and engagement metrics
    - Subreddit categorization
    - Keywords and hashtags from titles
    """

    source = TrendSource.REDDIT

    # Reddit API endpoints
    REDDIT_BASE = "https://www.reddit.com"
    OAUTH_BASE = "https://oauth.reddit.com"

    # HTTP headers
    HEADERS = {
        "User-Agent": "YTShortsFactory/1.0 (Trend Analysis Bot)",
        "Accept": "application/json",
    }

    def __init__(self, settings: "Settings") -> None:
        """Initialize Reddit scraper."""
        super().__init__(settings)
        self._session: Optional[aiohttp.ClientSession] = None
        self._access_token: Optional[str] = None
        self._token_expires: Optional[datetime] = None

    @property
    def enabled(self) -> bool:
        """Check if Reddit scraping is enabled."""
        return self.settings.trends.enable_reddit

    @property
    def subreddits(self) -> list[str]:
        """Get list of subreddits to monitor."""
        return self.settings.trends.subreddits_list

    @property
    def has_credentials(self) -> bool:
        """Check if Reddit API credentials are configured."""
        client_id = self.settings.trends.reddit_client_id
        client_secret = self.settings.trends.reddit_client_secret.get_secret_value()
        return bool(client_id and client_secret)

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
        """Validate Reddit API credentials."""
        if not self.has_credentials:
            logger.debug("No Reddit credentials configured, using public API")
            return True  # Public API works without credentials

        try:
            token = await self._get_access_token()
            return token is not None
        except Exception as e:
            logger.warning(f"Reddit credential validation failed: {e}")
            return False

    async def _get_access_token(self) -> Optional[str]:
        """
        Get OAuth access token for authenticated requests.

        Returns:
            Access token string or None.
        """
        # Return cached token if still valid
        if self._access_token and self._token_expires:
            if datetime.utcnow() < self._token_expires:
                return self._access_token

        if not self.has_credentials:
            return None

        client_id = self.settings.trends.reddit_client_id
        client_secret = self.settings.trends.reddit_client_secret.get_secret_value()

        session = await self._get_session()

        auth = aiohttp.BasicAuth(client_id, client_secret)
        data = {"grant_type": "client_credentials"}

        try:
            async with session.post(
                "https://www.reddit.com/api/v1/access_token",
                auth=auth,
                data=data,
            ) as response:
                if response.status != 200:
                    logger.warning(f"Reddit OAuth failed: {response.status}")
                    return None

                result = await response.json()
                self._access_token = result.get("access_token")

                # Token expires in 'expires_in' seconds (usually 3600)
                expires_in = result.get("expires_in", 3600)
                from datetime import timedelta
                self._token_expires = datetime.utcnow() + timedelta(
                    seconds=expires_in - 60  # Refresh 1 min early
                )

                return self._access_token

        except Exception as e:
            logger.error(f"Reddit OAuth error: {e}")
            return None

    async def fetch_trends(
        self,
        query: Optional[str] = None,
        max_results: int = 10,
    ) -> ScrapingResult:
        """
        Fetch Reddit trending topics.

        Aggregates hot posts from configured subreddits.

        Args:
            query: Optional filter (not used for Reddit).
            max_results: Maximum trends to return.

        Returns:
            ScrapingResult with trends.
        """
        if not self.subreddits:
            return ScrapingResult(
                success=False,
                source=self.source,
                error="No subreddits configured",
            )

        all_trends: list[TrendData] = []
        errors: list[str] = []

        # Fetch from each subreddit
        posts_per_sub = max(max_results // len(self.subreddits), 3)

        for subreddit in self.subreddits:
            try:
                trends = await self._fetch_subreddit(subreddit, posts_per_sub)
                all_trends.extend(trends)
            except Exception as e:
                logger.warning(f"Failed to fetch r/{subreddit}: {e}")
                errors.append(f"r/{subreddit}: {str(e)}")

        if not all_trends:
            return ScrapingResult(
                success=False,
                source=self.source,
                error="; ".join(errors) if errors else "No trends found",
            )

        # Sort by score and deduplicate
        all_trends.sort(key=lambda t: t.score, reverse=True)

        seen_keywords: set[str] = set()
        unique_trends: list[TrendData] = []
        for trend in all_trends:
            keyword_lower = trend.keyword.lower()
            if keyword_lower not in seen_keywords:
                seen_keywords.add(keyword_lower)
                unique_trends.append(trend)

        return ScrapingResult(
            success=True,
            source=self.source,
            trends=unique_trends[:max_results],
        )

    async def _fetch_subreddit(
        self,
        subreddit: str,
        max_posts: int,
    ) -> list[TrendData]:
        """
        Fetch hot posts from a specific subreddit.

        Args:
            subreddit: Subreddit name (without r/).
            max_posts: Maximum posts to fetch.

        Returns:
            List of TrendData from subreddit.
        """
        session = await self._get_session()

        # Try authenticated first, fall back to public
        token = await self._get_access_token()

        if token:
            url = f"{self.OAUTH_BASE}/r/{subreddit}/hot.json"
            headers = {"Authorization": f"Bearer {token}"}
        else:
            url = f"{self.REDDIT_BASE}/r/{subreddit}/hot.json"
            headers = {}

        params = {
            "limit": min(max_posts * 2, 25),  # Fetch extra for filtering
            "raw_json": 1,
        }

        async with session.get(url, params=params, headers=headers) as response:
            if response.status == 403:
                raise ScrapingError(f"Access denied to r/{subreddit}")
            elif response.status == 404:
                raise ScrapingError(f"Subreddit r/{subreddit} not found")
            elif response.status != 200:
                raise ScrapingError(f"Reddit API error: {response.status}")

            data = await response.json()

        return self._parse_subreddit_response(data, subreddit, max_posts)

    def _parse_subreddit_response(
        self,
        data: dict[str, Any],
        subreddit: str,
        max_posts: int,
    ) -> list[TrendData]:
        """
        Parse Reddit API response into TrendData list.

        Args:
            data: Reddit API response.
            subreddit: Source subreddit name.
            max_posts: Maximum posts to return.

        Returns:
            List of TrendData.
        """
        trends: list[TrendData] = []

        posts = data.get("data", {}).get("children", [])

        for post_wrapper in posts:
            post = post_wrapper.get("data", {})

            # Skip stickied/pinned posts
            if post.get("stickied") or post.get("pinned"):
                continue

            title = post.get("title", "")
            if not title or len(title) < 10:
                continue

            # Extract keywords
            keywords = self._extract_keywords_from_title(title)
            if not keywords:
                continue

            primary_keyword = keywords[0]

            # Get metrics
            score = post.get("score", 0)
            upvote_ratio = post.get("upvote_ratio", 0.5)
            num_comments = post.get("num_comments", 0)
            created_utc = post.get("created_utc", 0)

            # Calculate engagement metrics
            engagement = score + (num_comments * 2)  # Weight comments more
            hours_old = (datetime.utcnow().timestamp() - created_utc) / 3600

            # Estimate growth rate based on score per hour
            if hours_old > 0:
                growth_rate = (score / hours_old) * 10  # Normalize
            else:
                growth_rate = score

            # Determine category from subreddit
            category = self._subreddit_to_category(subreddit)

            # Calculate preliminary score
            trend_score = self._calculate_post_score(
                score, upvote_ratio, num_comments, hours_old
            )

            # Extract hashtags from flair and title
            hashtags = self._extract_hashtags(title, post.get("link_flair_text", ""))

            trends.append(
                TrendData(
                    keyword=primary_keyword,
                    source=self.source,
                    score=trend_score,
                    volume=engagement,
                    growth_rate=growth_rate,
                    competition=self._estimate_competition(engagement, growth_rate),
                    category=category,
                    related_keywords=keywords[1:5],
                    hashtags=hashtags,
                    description=title,
                    url=f"https://reddit.com{post.get('permalink', '')}",
                    raw_data={
                        "subreddit": subreddit,
                        "post_id": post.get("id"),
                        "author": post.get("author"),
                        "score": score,
                        "num_comments": num_comments,
                        "created_utc": created_utc,
                    },
                )
            )

            if len(trends) >= max_posts:
                break

        return trends

    def _calculate_post_score(
        self,
        score: int,
        upvote_ratio: float,
        num_comments: int,
        hours_old: float,
    ) -> float:
        """
        Calculate a normalized trend score for a post.

        Args:
            score: Reddit score (upvotes - downvotes).
            upvote_ratio: Percentage of upvotes.
            num_comments: Number of comments.
            hours_old: Age in hours.

        Returns:
            Normalized score between 0 and 1.
        """
        # Normalize score (logarithmic for high scores)
        import math
        score_component = min(math.log10(max(score, 1) + 1) / 5, 1.0)

        # Upvote ratio (higher is better)
        ratio_component = upvote_ratio

        # Engagement (comments relative to score)
        if score > 0:
            engagement_component = min(num_comments / score, 1.0)
        else:
            engagement_component = 0.5

        # Freshness decay (newer is better)
        if hours_old <= 1:
            freshness = 1.0
        elif hours_old <= 6:
            freshness = 0.9
        elif hours_old <= 12:
            freshness = 0.7
        elif hours_old <= 24:
            freshness = 0.5
        else:
            freshness = max(0.2, 1 - (hours_old / 168))  # Decay over a week

        # Weighted combination
        final_score = (
            score_component * 0.35
            + ratio_component * 0.20
            + engagement_component * 0.20
            + freshness * 0.25
        )

        return round(min(final_score, 1.0), 3)

    def _extract_keywords_from_title(self, title: str) -> list[str]:
        """
        Extract meaningful keywords from a post title.

        Args:
            title: Post title.

        Returns:
            List of keywords.
        """
        if not title:
            return []

        # Remove common patterns
        clean = re.sub(r'\[.*?\]', '', title)  # [tags]
        clean = re.sub(r'\(.*?\)', '', clean)  # (parenthetical)
        clean = re.sub(r'https?://\S+', '', clean)  # URLs
        clean = re.sub(r'/r/\w+', '', clean)  # Subreddit mentions
        clean = re.sub(r'/u/\w+', '', clean)  # User mentions

        # Tokenize
        words = clean.split()

        stop_words = {
            "the", "a", "an", "and", "or", "but", "in", "on", "at", "to",
            "for", "of", "with", "by", "from", "is", "are", "was", "were",
            "be", "been", "being", "have", "has", "had", "do", "does", "did",
            "will", "would", "could", "should", "may", "might", "must",
            "this", "that", "these", "those", "i", "you", "he", "she", "it",
            "we", "they", "what", "which", "who", "whom", "how", "when",
            "where", "why", "just", "only", "very", "really", "so", "too",
            "my", "your", "his", "her", "its", "our", "their", "me", "him",
            "us", "them", "can", "don't", "doesn't", "didn't", "won't",
            "wouldn't", "couldn't", "shouldn't", "not", "no", "yes",
            "about", "after", "before", "up", "down", "out", "over",
            "into", "through", "during", "including", "until", "against",
            "among", "throughout", "despite", "towards", "upon", "concerning",
        }

        keywords: list[str] = []
        for word in words:
            word = word.strip(".,!?\"'():;-")
            if (
                len(word) >= 3
                and word.lower() not in stop_words
                and not word.isdigit()
                and not word.startswith(('http', 'www'))
            ):
                keywords.append(word)

        # Create bigrams for phrase extraction
        if len(keywords) >= 2:
            bigrams = [
                f"{keywords[i]} {keywords[i+1]}"
                for i in range(len(keywords) - 1)
            ]
            # Insert most likely phrases at the front
            for bigram in bigrams[:3]:
                if len(bigram) <= 50:
                    keywords.insert(0, bigram)

        return keywords[:10]

    def _extract_hashtags(self, title: str, flair: Optional[str]) -> list[str]:
        """Extract hashtags from title and flair."""
        hashtags: list[str] = []

        # Extract #hashtags from title
        title_tags = re.findall(r'#(\w+)', title)
        hashtags.extend(title_tags)

        # Convert flair to hashtag
        if flair:
            flair_clean = re.sub(r'\W+', '', flair)
            if flair_clean:
                hashtags.append(flair_clean)

        return list(set(hashtags))[:5]

    def _subreddit_to_category(self, subreddit: str) -> TrendCategory:
        """Map subreddit to content category."""
        subreddit_lower = subreddit.lower()

        category_map = {
            # Technology
            "technology": TrendCategory.TECHNOLOGY,
            "programming": TrendCategory.TECHNOLOGY,
            "python": TrendCategory.TECHNOLOGY,
            "javascript": TrendCategory.TECHNOLOGY,
            "webdev": TrendCategory.TECHNOLOGY,
            "machinelearning": TrendCategory.TECHNOLOGY,
            "artificial": TrendCategory.TECHNOLOGY,
            "android": TrendCategory.TECHNOLOGY,
            "apple": TrendCategory.TECHNOLOGY,
            "gadgets": TrendCategory.TECHNOLOGY,
            "hardware": TrendCategory.TECHNOLOGY,
            "software": TrendCategory.TECHNOLOGY,

            # Gaming
            "gaming": TrendCategory.GAMING,
            "games": TrendCategory.GAMING,
            "pcgaming": TrendCategory.GAMING,
            "ps5": TrendCategory.GAMING,
            "xbox": TrendCategory.GAMING,
            "nintendo": TrendCategory.GAMING,

            # Science
            "science": TrendCategory.SCIENCE,
            "space": TrendCategory.SCIENCE,
            "physics": TrendCategory.SCIENCE,
            "chemistry": TrendCategory.SCIENCE,
            "biology": TrendCategory.SCIENCE,

            # Entertainment
            "movies": TrendCategory.ENTERTAINMENT,
            "television": TrendCategory.ENTERTAINMENT,
            "netflix": TrendCategory.ENTERTAINMENT,
            "entertainment": TrendCategory.ENTERTAINMENT,

            # Finance
            "finance": TrendCategory.FINANCE,
            "investing": TrendCategory.FINANCE,
            "stocks": TrendCategory.FINANCE,
            "cryptocurrency": TrendCategory.FINANCE,
            "bitcoin": TrendCategory.FINANCE,
            "wallstreetbets": TrendCategory.FINANCE,

            # News
            "news": TrendCategory.NEWS,
            "worldnews": TrendCategory.NEWS,
            "politics": TrendCategory.NEWS,

            # Education
            "todayilearned": TrendCategory.EDUCATION,
            "explainlikeimfive": TrendCategory.EDUCATION,
            "askscience": TrendCategory.EDUCATION,

            # Sports
            "sports": TrendCategory.SPORTS,
            "nfl": TrendCategory.SPORTS,
            "nba": TrendCategory.SPORTS,
            "soccer": TrendCategory.SPORTS,

            # Lifestyle
            "fitness": TrendCategory.LIFESTYLE,
            "health": TrendCategory.LIFESTYLE,
            "food": TrendCategory.LIFESTYLE,
            "travel": TrendCategory.LIFESTYLE,
        }

        return category_map.get(subreddit_lower, TrendCategory.GENERAL)
