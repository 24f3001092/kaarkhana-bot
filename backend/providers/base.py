
from abc import ABC, abstractmethod
from typing import Any
class AIProvider(ABC):
    name = "base"

    @abstractmethod
    async def structured(self, messages: list[dict[str, Any]], schema: dict[str, Any], schema_name: str) -> dict[str, Any]:
        raise NotImplementedError

    @abstractmethod
    async def text(self, messages: list[dict[str, Any]], *, max_tokens: int = 2500) -> str:
        raise NotImplementedError
