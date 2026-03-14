from typing import Optional
from uuid import UUID

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from collection.models import Collection
from utils.dao import BaseDAO


class CollectionDAO(BaseDAO):
    """Data Access Object for Collection model."""

    def __init__(self, session: AsyncSession):
        super().__init__(session=session, db_model=Collection)

    async def create_collection(
        self,
        collection_id: UUID,
        brand_id: UUID,
        user_req: dict,
        status: str = "pending",
    ) -> Collection:
        """Create a new collection record."""
        collection = Collection(
            id=collection_id,
            brand_id=brand_id,
            status=status,
            user_req=user_req,
        )
        self.session.add(collection)
        return collection

    async def select_by_id(self, collection_id: UUID) -> Optional[Collection]:
        """Select collection by ID."""
        query = select(Collection).where(Collection.id == collection_id)
        result = await self._execute_query(query)
        return result.scalar_one_or_none()

    async def update_status(self, collection_id: UUID, status: str) -> None:
        """Update collection status."""
        query = (
            update(Collection)
            .where(Collection.id == collection_id)
            .values(status=status)
        )
        await self._execute_query(query)

    async def update_overview(
        self,
        collection_id: UUID,
        collection_name: str | None = None,
        overview: str | None = None,
        range_overview: dict | None = None,
    ) -> None:
        """Update collection overview fields."""
        update_values = {}
        if collection_name is not None:
            update_values["collection_name"] = collection_name
        if overview is not None:
            update_values["overview"] = overview
        if range_overview is not None:
            update_values["range_overview"] = range_overview

        if update_values:
            query = (
                update(Collection)
                .where(Collection.id == collection_id)
                .values(**update_values)
            )
            await self._execute_query(query)
