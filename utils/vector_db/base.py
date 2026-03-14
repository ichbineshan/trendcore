"""Abstract base classes for vector database adapters and SQL
vector database operations."""
from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional




class VectorDBAdapter(ABC):
    """Abstract base class for vector database adapters providing
    standardized interface for vector operations."""
    
    @abstractmethod
    async def connect(self) -> None:
        """Establishes a connection to the underlying vector database."""

    @abstractmethod
    async def close(self) -> None:
        """Closes the connection to the vector database."""

