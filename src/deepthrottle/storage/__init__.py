from deepthrottle.storage.base import BaseStorage
from deepthrottle.storage.in_memory import InMemoryStorage
from deepthrottle.storage.redis import RedisStorage


# Factory function to instantiate the configured storage backend.
def get_storage(backend_type: str = "memory", **kwargs) -> BaseStorage:
    if backend_type == "redis":
        return RedisStorage(**kwargs)
    return InMemoryStorage()


__all__ = ["BaseStorage", "InMemoryStorage", "RedisStorage", "get_storage"]
