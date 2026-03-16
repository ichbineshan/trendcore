"""Ahrefs API client for Keywords Explorer data."""

import httpx
from typing import List

from config.settings import loaded_config
from config.logging import logger


class AhrefsKeywordsExplorer:
    """
    Ahrefs Keywords Explorer API client.

    Provides access to keyword metrics including:
    - Search volume
    - Traffic potential
    - Keyword difficulty
    - CPC (cost per click)
    - Search intent classification
    """

    BASE_URL = "https://api.ahrefs.com/v3/keywords-explorer"

    def __init__(self, api_key: str | None = None):
        self.api_key = api_key or loaded_config.ahrefs_api_key
        self.async_client = httpx.AsyncClient(
            base_url=self.BASE_URL,
            timeout=30.0,
            headers={
                "Authorization": f"Bearer {self.api_key}",
                "Accept": "application/json",
            }
        )

    async def close(self):
        """Close the HTTP client."""
        await self.async_client.aclose()

    async def get_keywords_overview(
        self,
        keywords: List[str],
        country: str = "us",
        select: str = "keyword,volume,traffic_potential,difficulty,cpc,parent_volume,is_informational,is_commercial,is_transactional,is_navigational"
    ) -> dict:
        """
        Get keyword overview metrics for one or more keywords.

        Args:
            keywords: List of keywords to analyze (max 100)
            country: Two-letter country code (default: "us")
            select: Comma-separated fields to return

        Returns:
            JSON response with keyword metrics
        """
        params = {
            "select": select,
            "country": country,
            "keywords": ",".join(keywords[:100]),  # API limit
        }

        try:
            response = await self.async_client.get("/overview", params=params)
            response.raise_for_status()
            return response.json()
        except httpx.HTTPStatusError as e:
            logger.error(f"Ahrefs API error: {e.response.status_code} - {e.response.text}")
            raise
        except Exception as e:
            logger.error(f"Ahrefs request failed: {e}", exc_info=True)
            raise

    async def get_volume_history(
        self,
        keywords: List[str],
        country: str = "us",
    ) -> dict:
        """
        Get historical monthly search volume for keywords.

        Args:
            keywords: List of keywords (max 100)
            country: Two-letter country code

        Returns:
            JSON response with monthly volume history
        """
        params = {
            "select": "keyword,volume_history",
            "country": country,
            "keywords": ",".join(keywords[:100]),
        }

        try:
            response = await self.async_client.get("/volume-history", params=params)
            response.raise_for_status()
            return response.json()
        except httpx.HTTPStatusError as e:
            logger.error(f"Ahrefs volume history error: {e.response.status_code}")
            raise
        except Exception as e:
            logger.error(f"Ahrefs volume history failed: {e}", exc_info=True)
            raise

    async def get_related_terms(
        self,
        keyword: str,
        country: str = "us",
        limit: int = 10,
    ) -> dict:
        """
        Get related keyword suggestions.

        Args:
            keyword: Seed keyword
            country: Two-letter country code
            limit: Max number of results

        Returns:
            JSON response with related keywords and their metrics
        """
        params = {
            "select": "keyword,volume,traffic_potential,difficulty,cpc",
            "country": country,
            "keyword": keyword,
            "limit": limit,
        }

        try:
            response = await self.async_client.get("/related-terms", params=params)
            response.raise_for_status()
            return response.json()
        except httpx.HTTPStatusError as e:
            logger.error(f"Ahrefs related terms error: {e.response.status_code}")
            raise
        except Exception as e:
            logger.error(f"Ahrefs related terms failed: {e}", exc_info=True)
            raise
