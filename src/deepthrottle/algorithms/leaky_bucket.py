import time


class LeakyBucket:
    def __init__(self, bucket_capacity: int, leak_rate: float) -> None:
        self.bucket_capacity: int = bucket_capacity
        self.leak_rate: float = leak_rate                                                                                                                                                                    
        self.water_level: float = 0.0                                                                                                                                                                        
        self.last_check: float = time.monotonic()   

    def _leak(self) -> None:                                                                                                                                                                                 
        now = time.monotonic()                                                                                                                                                                               
        elapsed = now - self.last_check                                                                                                                                                                      
        self.water_level = max(0.0, self.water_level - (elapsed * self.leak_rate))                                                                                                                           
        self.last_check = now

    def add_request(self, tokens: int = 1) -> tuple[int, bool, float]:
        self._leak()

        if self.water_level + tokens <= self.bucket_capacity:
            self.water_level += tokens
            remaining = max(0, int(self.bucket_capacity - self.water_level))                                                                                                                                 
            return remaining, True, 0.0 

        # Bucket is full or request exceeds remaining capacity
        tokens_needed = (self.water_level + tokens) - self.bucket_capacity
        wait_time = tokens_needed / self.leak_rate
        remaining = max(0, int(self.bucket_capacity - self.water_level))
        return remaining, False, wait_time

    def get_state(self) -> dict[str, float | str]:                                                                                                                                                           
        self._leak()                                                                                                                                                                                         
        return {                                                                                                                                                                                             
            "Name": "LeakyBucket",                                                                                                                                                                           
            "water_level": round(self.water_level, 2),                                                                                                                                                       
            "remaining_capacity": max(0, int(self.bucket_capacity - self.water_level)),                                                                                                                      
        }