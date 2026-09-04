import time


class TokenBucket:
    def __init__(self, bucket_capacity: int, refill_rate: float) -> None:
        self.bucket_capacity: float = bucket_capacity
        self.refill_rate: float = refill_rate
        self.tokens: float = bucket_capacity
        self.last_refill: float = time.monotonic()

    def _refill_tokens(self):
        now = time.monotonic()
        elapsed = now - self.last_refill
        tokens_to_add = elapsed * self.refill_rate
        self.tokens = min(self.bucket_capacity, self.tokens + tokens_to_add)
        self.last_refill = now

    def add_request(self, token: float = 1.0) -> tuple[float, bool, float]:
        self._refill_tokens()

        if self.tokens >= token:
            self.tokens -= token
            return self.tokens, True, 0.0
        else:
            tokens_needed = token - self.tokens
            wait_time = tokens_needed / self.refill_rate
            return self.tokens, False, wait_time

    def get_state(self) -> dict[str, float | str]:
        self._refill_tokens()
        return {
            "Name": "TokenBucket",
            "Tokens Left": self.tokens,
            "Last Refill": self.last_refill,
        }