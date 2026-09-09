from abc import ABC, abstractmethod
from typing import Any


class BaseStorage(ABC):
    
    @abstractmethod
    async def acquire(
        self, key: str, tokens: int = 1, **algo_params: Any
    ) -> tuple[int | float, bool, float]:
        pass

    @abstractmethod
    async def get_state(self, key: str) -> dict[str, Any]:
        pass

    @abstractmethod
    async def delete(self, key: str) -> bool:
        pass

    @abstractmethod
    async def list_keys(self) -> list[dict[str, Any]]:
        pass

    @abstractmethod
    async def close(self) -> None:
        pass
