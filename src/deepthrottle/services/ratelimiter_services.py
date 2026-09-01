from enum import Enum

from deepthrottle.algorithms.leaky_bucket import LeakyBucket
from deepthrottle.algorithms.sliding_window_counter import SlidingWindowCounter
from deepthrottle.algorithms.token_bucket import TokenBucket


class AlgorithmType(Enum):
    LEAKY_BUCKET = LeakyBucket
    TOKEN_BUCKET = TokenBucket
    SLIDING_WINDOW_COUNTER = SlidingWindowCounter


class RateLimiter:
    def __init__(
        self,
        algorithm: AlgorithmType,
        rate: float,
        capacity: int,
        window_size_seconds: float | None = None,
    ):
        self.algorithm: AlgorithmType = algorithm
        self.capacity: float | int = capacity
        self.window_size_seconds: float | None = window_size_seconds
        self.rate: float = rate

        if window_size_seconds is not None:
            self._algorithm_instance = algorithm.value(capacity, window_size_seconds)
        else:
            self._algorithm_instance = algorithm.value(capacity, rate)

    def allow(self, key: str) -> tuple[float | int, bool, float | None]:
        tokens: float | int
        allowed: bool
        wait_time: float | None
        
        tokens, allowed, wait_time = self._algorithm_instance.add_request()
        return tokens, allowed, wait_time


    def get_state(self, key: str) -> dict[str, float | str]:
        return self._algorithm_instance.get_state()