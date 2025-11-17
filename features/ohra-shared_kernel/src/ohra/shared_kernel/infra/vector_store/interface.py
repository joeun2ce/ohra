from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional


class VectorStoreInterface(ABC):
    @abstractmethod
    async def upsert(self, id: str, vector: List[float], metadata: Dict[str, Any]) -> None:
        pass

    @abstractmethod
    async def search(
        self, query_vector: List[float], top_k: int = 5, filter: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        pass

    @abstractmethod
    async def delete(self, ids: List[str]) -> None:
        pass

    @abstractmethod
    async def create_collection(self, collection_name: str, vector_size: int) -> None:
        pass
