from enum import Enum

from src.deepthrottle.algorithms.leaky_bucket import LeakyBucket
from src.deepthrottle.algorithms.sliding_window_counter import SlidingWindowCounter
from src.deepthrottle.algorithms.token_bucket import TokenBucket


class AlgorithmType(Enum):
    LEAKY_BUCKET = LeakyBucket
    TOKEN_BUCKET = TokenBucket
    SLIDING_WINDOW_COUNTER = SlidingWindowCounter

class RateLimiter:
    def __init__ (
        self,
        algorithm: AlgorithmType,
        capacity: int,
        rate: float | None = None,
        window_size_seconds: float | None = None,
    ):
        self.algorithm: AlgorithmType = algorithm 
        self.capacity = capacity
        self.rate = rate
        self.window_size_seconds = window_size_seconds

        if algorithm == AlgorithmType.SLIDING_WINDOW_COUNTER:
            if window_size_seconds is None:
                raise ValueError("SlidingWindowCounter requires 'window_size_seconds'.")
            self._algorithm_instance = algorithm.value(max_requests=capacity, window_size_seconds=window_size_seconds)

        elif algorithm in (AlgorithmType.TOKEN_BUCKET, AlgorithmType.LEAKY_BUCKET):
            if rate is None:
                raise ValueError(f"{algorithm.name} requires 'rate'.")
            self._algorithm_instance = self.algorithm.value(capacity, rate)
            

    def allow(self, key: str) -> tuple[float | int, bool, float | None]:
        tokens: float | int
        allowed: bool
        wait_time: float | None
        
        tokens, allowed, wait_time = self._algorithm_instance.add_request()
        return tokens, allowed, wait_time

    def get_state(self) -> dict[str, float | str]:
        return self._algorithm_instance.get_state()