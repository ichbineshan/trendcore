from uuid import UUID

import uuid6

from collection.dao import CollectionDAO
from collection.models import Collection
from config.logging import logger
from utils.connection_handler import get_connection_handler_for_app


class CollectionService:
    """Service layer for Collection operations."""

    @staticmethod
    async def create_collection(
        brand_id: UUID,
        user_req: dict,
    ) -> UUID:
        """Create a new collection record with pending status."""
        collection_id = uuid6.uuid7()

        async with get_connection_handler_for_app() as connection_handler:
            dao = CollectionDAO(connection_handler.session)
            await dao.create_collection(
                collection_id=collection_id,
                brand_id=brand_id,
                user_req=user_req,
                status="pending",
            )
            await connection_handler.session.commit()
            logger.info(f"Created new collection: {collection_id}")

        return collection_id

    @staticmethod
    async def get_collection_by_id(collection_id: UUID) -> Collection | None:
        """Get collection by ID."""
        async with get_connection_handler_for_app() as connection_handler:
            dao = CollectionDAO(connection_handler.session)
            return await dao.select_by_id(collection_id)

    @staticmethod
    async def update_collection_status(collection_id: UUID, status: str) -> None:
        """Update collection status."""
        async with get_connection_handler_for_app() as connection_handler:
            dao = CollectionDAO(connection_handler.session)
            await dao.update_status(collection_id, status)
            await connection_handler.session.commit()

    @staticmethod
    async def update_collection_overview(
        collection_id: UUID,
        collection_name: str | None = None,
        overview: str | None = None,
        range_overview: dict | None = None,
    ) -> None:
        """Update collection overview fields."""
        async with get_connection_handler_for_app() as connection_handler:
            dao = CollectionDAO(connection_handler.session)
            await dao.update_overview(
                collection_id=collection_id,
                collection_name=collection_name,
                overview=overview,
                range_overview=range_overview,
            )
            await connection_handler.session.commit()

    @staticmethod
    async def get_collections_by_brand_id(brand_id: UUID) -> list[Collection]:
        """Get all collections for a brand."""
        async with get_connection_handler_for_app() as connection_handler:
            dao = CollectionDAO(connection_handler.session)
            return await dao.select_by_brand_id(brand_id)

    @staticmethod
    async def update_collection_image_url(collection_id: UUID, image_url: str) -> None:
        """Update collection image URL."""
        async with get_connection_handler_for_app() as connection_handler:
            dao = CollectionDAO(connection_handler.session)
            await dao.update_image_url(collection_id, image_url)
            await connection_handler.session.commit()
