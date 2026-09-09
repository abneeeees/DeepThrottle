from typing import Any

from deepthrottle.services.ratelimiter_services import AlgorithmType, RateLimiter
from deepthrottle.storage.base import BaseStorage


class InMemoryStorage(BaseStorage):                                                                                                                                                                          
    def __init__(self) -> None:                                                                                                                                                                              
        self._limiters: dict[str, RateLimiter] = {}                                                                                                                                                          
                                                                                                                                                                                                                
    async def acquire(                                                                                                                                                                                       
        self, key: str, tokens: int = 1, **algo_params: Any                                                                                                                                                  
    ) -> tuple[int | float, bool, float]:                                                                                                                                                                    
        if key not in self._limiters:                                                                                                                                                                        
            strategy_name = algo_params.get("strategy", "TOKEN_BUCKET")                                                                                                                                      
            if isinstance(strategy_name, str):                                                                                                                                                               
                strategy = AlgorithmType[strategy_name.upper()]                                                                                                                                              
            else:                                                                                                                                                                                            
                strategy = strategy_name                                                                                                                                                                     
                                                                                                                                                                                                                
            capacity = int(algo_params.get("capacity", 100))                                                                                                                                                 
            rate = algo_params.get("rate") or algo_params.get("refill_rate")                                                                                                                                 
            rate = float(rate) if rate is not None else None                                                                                                                                                 
            window_size = algo_params.get("window_size_seconds")                                                                                                                                             
            window_size = float(window_size) if window_size is not None else None                                                                                                                            
                                                                                                                                                                                                                
            self._limiters[key] = RateLimiter(                                                                                                                                                               
                algorithm=strategy,                                                                                                                                                                          
                capacity=capacity,                                                                                                                                                                           
                rate=rate,                                                                                                                                                                                   
                window_size_seconds=window_size,                                                                                                                                                             
            )                                                                                                                                                                                                
                                                                                                                                                                                                                
        limiter = self._limiters[key]                                                                                                                                                                        
        remaining, allowed, wait_time = limiter.allow(key)                                                                                                                                                   
        return remaining, allowed, wait_time or 0.0                                                                                                                                                          
                                                                                                                                                                                                                
    async def get_state(self, key: str) -> dict[str, Any]:                                                                                                                                                   
        if key in self._limiters:                                                                                                                                                                            
            return self._limiters[key].get_state()                                                                                                                                                           
        raise KeyError(f"Key '{key}' not found in in-memory storage.")                                                                                                                                       
                                                                                                                                                                                                                
    async def delete(self, key: str) -> bool:                                                                                                                                                                
        if key in self._limiters:                                                                                                                                                                            
            del self._limiters[key]                                                                                                                                                                          
            return True                                                                                                                                                                                      
        return False                                                                                                                                                                                         
                                                                                                                                                                                                                
    async def list_keys(self) -> list[dict[str, Any]]:                                                                                                                                                       
        result: list[dict[str, Any]] = []                                                                                                                                                                    
        for k, v in self._limiters.items():                                                                                                                                                                  
            result.append(                                                                                                                                                                                   
                {                                                                                                                                                                                            
                    "key": k,                                                                                                                                                                                
                    "algorithm": v.algorithm.name,                                                                                                                                                           
                    "rate": v.rate,                                                                                                                                                                          
                    "capacity": v.capacity,                                                                                                                                                                  
                    "window_size_seconds": v.window_size_seconds,                                                                                                                                            
                }                                                                                                                                                                                            
            )                                                                                                                                                                                                
        return result                                                                                                                                                                                        
                                                                                                                                                                                                                
    async def close(self) -> None:                                                                                                                                                                           
        self._limiters.clear()