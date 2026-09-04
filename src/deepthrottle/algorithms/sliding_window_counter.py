import time


class SlidingWindowCounter:
    """
    A sliding window counter that tracks the number of requests in a given window size.
    - max_requests: that is the maximum number of requests allowed in the window
    - window_size_seconds: the size of the window in seconds
    """
    def __init__ (self, max_requests: int, window_size_seconds: float):
        self.max_requests: int = max_requests
        self.window_size: float = window_size_seconds
        self.previous_window_requests: int = 0
        self.current_window_requests: int = 0
        self.current_window_start: float = time.monotonic()

    def _advance_window(self, now :float) -> None:
        elapsed = now - self.current_window_start
        
        if elapsed >= self.window_size:                                                                                                                                                                      
            windows_passed = int(elapsed // self.window_size)                                                                                                                                                
            if windows_passed == 1:                                                                                                                                                                          
                self.previous_window_requests = self.current_window_requests                                                                                                                                       
            else:                                                                                                                                                                                            
                self.previous_window_requests = 0                                                                                                                                                               
            self.current_window_requests = 0                                                                                                                                                                    
            self.current_window_start += windows_passed * self.window_size

    def add_request(self, cost: int = 1) -> tuple[int, bool, float]:                                                                                                                                         
        now = time.monotonic()                                                                                                                                                                               
        self._advance_window(now)                                                                                                                                                                            
                                                                                                                                                                                                                
        current_elapsed = now - self.current_window_start                                                                                                                                                    
        weight_prev = max(0.0, 1.0 - (current_elapsed / self.window_size))                                                                                                                                   
        estimated_requests = self.current_window_requests + (weight_prev * self.previous_window_requests)                                                                                                          
                                                                                                                                                                                                                
        if estimated_requests + cost <= self.max_requests:                                                                                                                                                   
            self.current_window_requests += cost                                                                                                                                                                
            remaining = max(0, int(self.max_requests - (estimated_requests + cost)))                                                                                                                         
            return remaining, True, 0.0                                                                                                                                                                      
                                                                                                                                                                                                                
        remaining = max(0, int(self.max_requests - estimated_requests))                                                                                                                                      
        wait_time = self.window_size - current_elapsed                                                                                                                                                       
        return remaining, False, wait_time                                                                                                                                                                   
                                                                                                                                                                                                                
    def get_state(self) -> dict[str, float | str]:                                                                                                                                                           
        now = time.monotonic()                                                                                                                                                                               
        self._advance_window(now)                                                                                                                                                                            
        current_elapsed = now - self.current_window_start                                                                                                                                                    
        weight_prev = max(0.0, 1.0 - (current_elapsed / self.window_size))                                                                                                                                   
        estimated = self.current_window_requests + (weight_prev * self.previous_window_requests)                                                                                                                   
        return {                                                                                                                                                                                             
            "Name": "SlidingWindowCounter",                                                                                                                                                                  
            "Window Size": self.window_size,                                                                                                                                                                 
            "Previous Windows Count": self.previous_window_requests,                                                                                                                                            
            "Current Window Count": self.current_window_requests,                                                                                                                                               
            "Estimated Count": round(estimated, 2),                                                                                                                                                          
            "Remaining Requests": max(0, int(self.max_requests - estimated)),                                                                                                                                
        }