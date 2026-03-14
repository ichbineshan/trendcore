"""
Pinterest image fetching service using Apify.

This service fetches relevant fashion images from Pinterest for trend keywords
to display as thumbnails in the trend tiles carousel UI.

Uses the epctex/pinterest-scraper actor from Apify Store.
Docs: https://apify.com/epctex/pinterest-scraper
API Reference: https://docs.apify.com/api/client/python/docs/overview
"""
import logging
from typing import List, Optional, Dict, Any

from apify_client import ApifyClientAsync

from config.settings import loaded_config

logger = logging.getLogger(__name__)


class PinterestImageFetcher:
    """
    Fetch Pinterest images for trend keywords using Apify's Pinterest Scraper.
    
    Uses the official Apify Python SDK for reliability and automatic retries.
    SDK Docs: https://docs.apify.com/api/client/python/docs/overview
    """
    
    # Default actor if not configured
    DEFAULT_ACTOR_NAME = "epctex/pinterest-scraper"
    
    def __init__(self, api_token: Optional[str] = None, actor_name: Optional[str] = None):
        """
        Initialize the Pinterest image fetcher.
        
        Args:
            api_token: Apify API token. Defaults to config value.
            actor_name: Actor name in format 'username/actor-name'. Defaults to config or default value.
        """
        self.api_token = api_token or getattr(loaded_config, 'apify_api_token', None)
        
        # Get actor name from config or use default
        configured_actor = getattr(loaded_config, 'apify_pinterest_actor_id', None)
        self.actor_name = actor_name or configured_actor or self.DEFAULT_ACTOR_NAME
        
        # Initialize the Apify async client
        self._client: Optional[ApifyClientAsync] = None
        if self.api_token:
            self._client = ApifyClientAsync(self.api_token)
        else:
            logger.warning("Apify API token not configured. Pinterest image fetching will fail.")
    
    async def verify_actor_exists(self) -> bool:
        """
        Verify that the configured actor exists and is accessible.
        
        Returns:
            True if actor exists and is accessible, False otherwise.
        """
        if not self._client:
            logger.error("Cannot verify actor: Apify API token not configured")
            return False
        
        try:
            actor_client = self._client.actor(self.actor_name)
            actor_info = await actor_client.get()
            
            if actor_info:
                logger.info(f"Verified actor exists: {actor_info.get('name', self.actor_name)}")
                return True
            else:
                logger.error(f"Actor not found: {self.actor_name}")
                return False
                
        except Exception as e:
            logger.error(f"Error verifying actor: {e}", exc_info=True)
            return False
    
    async def get_actor_info(self) -> Optional[Dict[str, Any]]:
        """
        Get detailed information about the configured actor.
        
        Returns:
            Actor info dict or None if not found.
        """
        if not self._client:
            return None
            
        try:
            actor_client = self._client.actor(self.actor_name)
            return await actor_client.get()
        except Exception as e:
            logger.error(f"Error getting actor info: {e}")
            return None
    
    async def fetch_images(
        self, 
        query: str, 
        limit: int = 5,
        timeout: int = 120,
        verify_actor: bool = True
    ) -> List[str]:
        """
        Fetch Pinterest images for a search query.
        
        Args:
            query: Search term (e.g., "cargo shorts men fashion")
            limit: Max number of images to fetch (default: 5)
            timeout: Request timeout in seconds (default: 120) - used for actor run timeout
            verify_actor: Whether to verify actor exists before running (default: True)
            
        Returns:
            List of image URLs. Empty list on failure.
        """
        if not self._client:
            logger.error("Cannot fetch Pinterest images: Apify API token not configured")
            return []
        
        try:
            # Input schema for epctex/pinterest-scraper
            actor_input = {
                "search": query,
                "maxItems": limit,
                "endPage": 1,
                "proxy": {
                    "useApifyProxy": True
                }
            }
            
            logger.info(f"Running Pinterest scraper ({self.actor_name}) for query: '{query}'")
            
            # Get actor client and run the actor
            actor_client = self._client.actor(self.actor_name)
            
            # Run actor and wait for it to finish
            # timeout_secs parameter controls how long to wait for the actor to complete
            call_result = await actor_client.call(
                run_input=actor_input,
                timeout_secs=timeout
            )
            
            if not call_result:
                logger.error(f"Actor run failed for query: '{query}'")
                return []
            
            # Fetch results from the Actor run's default dataset
            dataset_id = call_result.get('defaultDatasetId')
            if not dataset_id:
                logger.error(f"No dataset ID returned for query: '{query}'")
                return []
            
            dataset_client = self._client.dataset(dataset_id)
            list_result = await dataset_client.list_items()
            items = list_result.items if list_result else []
            
            image_urls = self._extract_image_urls(items, limit)
            
            logger.info(f"Fetched {len(image_urls)} Pinterest images for query: '{query}'")
            return image_urls
                
        except TimeoutError:
            logger.error(f"Timeout fetching Pinterest images for '{query}'")
            return []
        except Exception as e:
            logger.error(f"Failed to fetch Pinterest images for '{query}': {e}", exc_info=True)
            return []
    
    def _extract_image_urls(self, items: List[dict], limit: int) -> List[str]:
        """
        Extract image URLs from Apify Pinterest scraper response.
        Handles multiple shapes:
        - Top-level url/image/imageUrl
        - images dict with size keys (e.g., 236x, 474x, 736x, orig, original)
        - lists of images
        """
        if not items:
            return []

        # Normalize single dict to list
        if isinstance(items, dict):
            items = [items]

        image_urls = []
        size_priority = ["orig", "original", "1200x", "736x", "474x", "564x", "400x", "236x", "75x", "url"]

        def pick_from_images(images_dict: dict) -> Optional[str]:
            # Try known size keys in priority order
            for size in size_priority:
                if size in images_dict:
                    val = images_dict[size]
                    if isinstance(val, str) and val.startswith("http"):
                        return val
                    if isinstance(val, dict) and "url" in val and isinstance(val["url"], str) and val["url"].startswith("http"):
                        return val["url"]
            # Fallback: any url inside nested dict
            for v in images_dict.values():
                if isinstance(v, str) and v.startswith("http"):
                    return v
                if isinstance(v, dict) and "url" in v and isinstance(v["url"], str) and v["url"].startswith("http"):
                    return v["url"]
            return None

        for item in items:
            if len(image_urls) >= limit:
                break
            if not isinstance(item, dict):
                continue

            url = None

            # 1) Direct fields
            for field in ['image_url', 'imageUrl', 'image', 'media', 'url']:
                if field not in item:
                    continue
                value = item[field]
                if isinstance(value, str) and value.startswith('http') and self._is_image_url(value):
                    url = value
                    break
                if isinstance(value, dict):
                    candidate = value.get("url")
                    if isinstance(candidate, str) and candidate.startswith("http"):
                        url = candidate
                        break
                if isinstance(value, list) and value:
                    first = value[0]
                    if isinstance(first, str) and first.startswith("http"):
                        url = first
                        break
                    if isinstance(first, dict) and "url" in first and isinstance(first["url"], str) and first["url"].startswith("http"):
                        url = first["url"]
                        break
            if url:
                image_urls.append(url)
                continue

            # 2) images dict with sizes (e.g., images -> 236x -> url)
            if "images" in item and isinstance(item["images"], dict):
                candidate = pick_from_images(item["images"])
                if candidate:
                    image_urls.append(candidate)
                    continue

        return image_urls[:limit]
    
    def _is_image_url(self, url: str) -> bool:
        """Check if URL is likely an image URL."""
        image_indicators = ['.jpg', '.jpeg', '.png', '.gif', '.webp', 'pinimg.com']
        url_lower = url.lower()
        return any(ind in url_lower for ind in image_indicators)
    
    def build_search_query(
        self, 
        canonical_form: str, 
        section: Optional[str] = None,
        product_category: Optional[str] = None,
        trend_type: Optional[str] = None
    ) -> str:
        """
        Build an optimized Pinterest search query from trend attributes.
        
        Args:
            canonical_form: The trend keyword (e.g., "cargo shorts")
            section: Gender section (e.g., "men", "women", "kids")
            product_category: Product category for additional context
            trend_type: Trend type (Colour, Pattern, etc.) for context
            
        Returns:
            Optimized search query string
        """
        parts = [canonical_form]
        
        if section:
            section_lower = section.lower()
            if section_lower == "men":
                parts.append("men's fashion")
            elif section_lower == "women":
                parts.append("women's fashion")
            elif section_lower == "kids":
                parts.append("kids fashion")
            else:
                parts.append("fashion")
        else:
            parts.append("fashion")
        
        if product_category:
            if product_category.lower() not in canonical_form.lower():
                parts.append(product_category)
        
        if trend_type:
            trend_type_lower = trend_type.lower()
            if trend_type_lower == "colour":
                parts.append("color trend")
            elif trend_type_lower == "pattern":
                parts.append("print pattern")
            elif trend_type_lower == "fabric":
                parts.append("textile material")
        
        return " ".join(parts)
    
    async def fetch_images_for_trend(
        self,
        canonical_form: str,
        section: Optional[str] = None,
        product_category: Optional[str] = None,
        trend_type: Optional[str] = None,
        limit: int = 5
    ) -> List[str]:
        """
        Convenience method to fetch images for a trend using optimized query.
        
        Args:
            canonical_form: The trend keyword
            section: Gender section
            product_category: Product category
            trend_type: Trend type classification
            limit: Number of images to fetch
            
        Returns:
            List of image URLs
        """
        query = self.build_search_query(
            canonical_form=canonical_form,
            section=section,
            product_category=product_category,
            trend_type=trend_type
        )
        return await self.fetch_images(query, limit=limit)
