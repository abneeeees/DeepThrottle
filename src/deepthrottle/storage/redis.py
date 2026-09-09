from math import ceil
from pathlib import Path
from time import time
from typing import Any

import redis.asyncio as redis

from deepthrottle.storage.base import BaseStorage


class RedisStorage(BaseStorage):
    """
    Distributed Redis storage backend executing atomic Lua scripts for rate limiting.
    Ideal for production, multi-worker setups, and horizontally scaled deployments.
    """

    def __init__(self, redis_url: str = "redis://localhost:6379/0") -> None:
        self.redis_url: str = redis_url
        self.client: redis.Redis
        self._scripts: dict[str, Any] = {}

    # Initialize the async Redis client connection pool and register Lua scripts.
    async def connect(self) -> None:
        self.client = redis.from_url(self.redis_url, decode_responses=True)
        await self._load_scripts()

    # Load .lua scripts from the storage/lua directory and register them with Redis.
    async def _load_scripts(self) -> None:
        if not self.client:                                                                                                                                                                                  
            raise RuntimeError("Redis client is not connected.")
            
        path = Path(__file__).parent / "lua"

        for script in path.glob("*.lua"):
            name = script.stem
            with open(script, "r") as f:
                script_text = f.read()
            self._scripts[name] = self.client.register_script(script_text)

    # Execute the appropriate atomic Lua script on Redis.
    async def acquire(self, key: str, tokens: int = 1, **algo_params: Any) -> tuple[int | float, bool, float]:
        if not self.client:
            await self.connect()

        # check if strategy is provided
        strategy = str(algo_params.get("strategy", "token_bucket")).lower()
        script = self._scripts.get(strategy)
        if script is None:
            raise ValueError("Missing 'strategy' in algo_params.")

        redis_key = f"deepthrottle:limiter:{key}"
        now = time()

        if strategy == "token_bucket":                                                                                                                                                                       
            capacity = float(algo_params["capacity"])                                                                                                                                                        
            rate = float(algo_params.get("rate") or algo_params["refill_rate"])                                                                                                                              
            args = [capacity, rate, now, tokens]
            
        elif strategy == "leaky_bucket":                                                                                                                                                                     
            capacity = float(algo_params["capacity"])                                                                                                                                                        
            leak_rate = float(algo_params.get("rate") or algo_params["leak_rate"])                                                                                                                           
            ttl = algo_params.get("ttl", ceil(capacity / leak_rate) * 2)                                                                                                                                     
            args = [capacity, leak_rate, tokens, now, ttl]
            
        elif strategy == "sliding_window_counter":                                                                                                                                                           
            max_requests = int(algo_params.get("capacity") or algo_params["max_requests"])                                                                                                                   
            window_size = float(algo_params["window_size_seconds"])                                                                                                                                          
            ttl = algo_params.get("ttl", ceil(window_size * 2))                                                                                                                                              
            args = [max_requests, window_size, tokens, now, ttl]  

        else:
            raise ValueError(f"Invalid algorithm parameters: {strategy}")

        allowed, remaining, wait_time = await script(keys=[redis_key], args=args)

        _ = await self.client.hset(                                                                                                                                                                              
            redis_key,                                                                                                                                                                                       
            mapping={                                                                                                                                                                                        
                "algorithm": strategy,                                                                                                                                                                       
                "capacity": str(algo_params.get("capacity", "")),                                                                                                                                            
                "rate": str(algo_params.get("rate", "")),                                                                                                                                                    
                "window_size_seconds": str(algo_params.get("window_size_seconds", "")),                                                                                                                      
            },                                                                                                                                                                                               
        )
        
        return float(remaining), bool(int(allowed)), float(wait_time or 0.0)
        
    async def get_state(self, key: str) -> dict[str, Any]:
        if not self.client:
            await self.connect()
            
        result = await self.client.hgetall(f"deepthrottle:limiter:{key}")
        if result:
            ans = {k.decode(): v.decode() if isinstance(v, bytes) else v for k, v in result.items()}
            return ans
            
        raise KeyError(f"Limiter key not found: {key}")

    # Delete a limiter key from Redis.
    async def delete(self, key: str) -> bool:
        deleted_count = await self.client.delete(f"deepthrottle:limiter:{key}")
        return deleted_count > 0

    # List all active rate limiters from Redis.
    async def list_keys(self) -> list[dict[str, Any]]:
        if not self.client:                                                                                                                                                                                  
            await self.connect() 
            
        summaries: list[dict[str, Any]] = []
        prefix = "deepthrottle:limiter:"

        async for raw_key in self.client.scan_iter(match=f"{prefix}*"):                                                                                                                                      
            key = raw_key.removeprefix(prefix)                                                                                                                                                               
            state = await self.client.hgetall(raw_key)                                                                                                                                                       
            summaries.append(
                {
                    "key": key,
                    "algorithm": state.get("algorithm", ""),
                    "rate": state.get("rate", ""),
                    "capacity": state.get("capacity", ""),
                    "window_size_seconds": state.get("window_size_seconds", ""),
                }
            )
        return summaries

    async def close(self) -> None:
        if self.client:
            await self.client.aclose()