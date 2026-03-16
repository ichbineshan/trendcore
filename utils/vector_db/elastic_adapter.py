"""Elasticsearch adapter implementation for vector database operations and search functionality."""
import asyncio
import logging
from typing import Optional

from elasticsearch import AsyncElasticsearch

from config.settings import loaded_config
from styles.types import Filters
from .base import VectorDBAdapter
from .embeddings import EmbeddingGenerator

logger = logging.getLogger(__name__)


class ElasticSearchAdapter(VectorDBAdapter):
    """Elasticsearch adapter for vector search operations."""



    def __init__(self):
        """Initializes the Elasticsearch adapter and sets up the embedding generator."""

        self.client = None
        self.embedding_generator = EmbeddingGenerator(
            api_key=loaded_config.openai_gpt4_key
        )

    async def connect(self, retries=3, delay=2) -> None:
        """Connect to Elasticsearch with retries."""
        for attempt in range(retries):
            try:
                self.client = AsyncElasticsearch(
                    hosts=[loaded_config.elastic_search_url]
                )
                await self.client.info()
                return
            except Exception as e:  # pylint: disable=broad-exception-caught
                if attempt < retries - 1:
                    await asyncio.sleep(delay * (2**attempt))  # Exponential backoff
                else:
                    # pylint: disable=raise-missing-from
                    raise ConnectionError(
                        f"Failed to connect to Elasticsearch: {str(e)}"
                    )

    async def close(self) -> None:
        """Closes the Elasticsearch client connection if initialized."""

        if self.client:
            await self.client.close()

    async def ensure_index_exists(
        self,
        index_name: str,
        mappings: Optional[dict] = None,
        settings: Optional[dict] = None
    ) -> bool:
        """
        Create Elasticsearch index if it doesn't exist with custom mappings and settings.
        
        This is a generic utility method that can be used for any index type.
        If mappings and settings are not provided, creates a basic index.
        
        Args:
            index_name: Name of the index to create
            mappings: Optional custom mappings for the index (dict with "properties" key)
            settings: Optional custom settings for the index
            
        Returns:
            True if index exists or was created successfully, False otherwise
            
        Example:
            mappings = {
                "properties": {
                    "field_name": {"type": "text"},
                    "embeddings": {"type": "dense_vector", "dims": 1536}
                }
            }
            settings = {"number_of_shards": 1, "number_of_replicas": 1}
            await adapter.ensure_index_exists("my-index", mappings, settings)
        """
        try:
            if not self.client:
                await self.connect()
            
            # Check if index already exists
            exists = await self.client.indices.exists(index=index_name)
            
            if exists:
                logger.info(f"Index '{index_name}' already exists")
                return True
            
            # Build index configuration
            index_body = {}
            
            if mappings:
                index_body["mappings"] = mappings
            
            if settings:
                index_body["settings"] = settings
            
            # Create the index
            response = await self.client.indices.create(
                index=index_name,
                body=index_body if index_body else None
            )
            
            logger.info(f"Successfully created index '{index_name}': {response}")
            return True
            
        except Exception as e:
            logger.error(
                f"Failed to create index '{index_name}': {e}",
                exc_info=True
            )
            return False

    async def similarity_search(
            self,
            index_name: str,
            query: str,
            filters: Optional[Filters] = None,
            max_results: int | None = 20
    ):
        try:

            query_vector = await self.embedding_generator.generate_embedding(query)
            es_filters = []

            if filters and filters.category:
                es_filters.append(
                    {
                        "terms": {
                            "category": (
                                filters.category
                                if isinstance(filters.category, list)
                                else [filters.category]
                            )
                        }
                    }
                )

            if filters and filters.year:
                es_filters.append({"term": {"year": filters.year}})

            if filters and filters.season:
                es_filters.append({"term": {"season": filters.season}})

            es_query = {
                "size": max_results,
                "min_score": 0.60,
                "knn": {
                    "field": "embeddings",
                    "query_vector": query_vector,
                    "k": max_results,
                    "num_candidates": 100,
                    "filter": es_filters
                }
            }

            await self.connect()
            data = await self.client.search(index=index_name, body=es_query)
            return data["hits"]["hits"]
        except Exception as e:
            logger.error(
                f"Error Fetching  similar data from elastic  : {e}", exc_info=True
            )
            raise e

    async def get_micro_trends_by_macro_ids(
        self,
        index_name: str,
        macro_ids: list[str],
        max_per_macro: int = 15
    ) -> list:
        """Fetches micro trends by their associated macro trend IDs using aggregations.

        Uses Elasticsearch aggregations with top_hits to ensure balanced results
        per macro trend, preventing any single macro from dominating the results.

        Args:
            index_name: The Elasticsearch index to search.
            macro_ids: List of macro trend IDs to find related micro trends.
            max_per_macro: Maximum number of micro trends to return per macro trend.

        Returns:
            List of matching micro trend documents in the same format as before
            (list of hits with _id, _source, etc.).
        """
        try:
            if not macro_ids:
                return []

            es_query = {
                "size": 0,
                "query": {
                    "terms": {
                        "macro_trend_id": macro_ids
                    }
                },
                "aggs": {
                    "by_macro": {
                        "terms": {
                            "field": "macro_trend_id",
                            "size": len(macro_ids)
                        },
                        "aggs": {
                            "top_micros": {
                                "top_hits": {
                                    "size": max_per_macro
                                }
                            }
                        }
                    }
                }
            }

            await self.connect()
            data = await self.client.search(index=index_name, body=es_query)

            # Flatten aggregation results to match previous return format
            results = []
            buckets = data.get("aggregations", {}).get("by_macro", {}).get("buckets", [])
            for bucket in buckets:
                hits = bucket.get("top_micros", {}).get("hits", {}).get("hits", [])
                results.extend(hits)

            return results
        except Exception as e:
            logger.error(
                f"Error fetching micro trends by macro IDs: {e}", exc_info=True
            )
            raise e

    async def delete_document_by_term(self, index_name: str, term: str, value: str | int | float) -> int:
        """
        Delete documents matching a specific term.

        Args:
            index_name: Name of the index
            term: Field name to match
            value: Value to match

        Returns:
            Number of deleted documents
        """
        try:
            if not self.client:
                await self.connect()

            query = {
                "query": {
                    "term": {
                        term: value
                    }
                }
            }

            response = await self.client.delete_by_query(
                index=index_name,
                body=query,
                refresh=True
            )

            deleted_count = response.get("deleted", 0)
            logger.info(f"Deleted {deleted_count} documents from {index_name} where {term}={value}")
            return deleted_count

        except Exception as e:
            logger.error(f"Failed to delete documents from {index_name}: {e}", exc_info=True)
            raise e
