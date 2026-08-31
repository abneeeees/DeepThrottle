import time
from queue import Queue, Empty


class LeakyBucket:
    def __init__(self, bucket_capacity: int, leak_rate: float) -> None:
        self.bucket_capacity: int = bucket_capacity
        self.leak_rate: float = leak_rate

        self.q: Queue[float] = Queue(maxsize=bucket_capacity)
        self.last_check: float = time.monotonic()
        self._leak_remainder: float = 0.0

    def _leak(self) -> None:
        now = time.monotonic()
        elapsed = now - self.last_check

        leaked = elapsed * self.leak_rate + self._leak_remainder
        leaked_requests = int(leaked)

        self._leak_remainder = leaked - leaked_requests
        self.last_check = now

        for _ in range(leaked_requests):
            try:
                self.q.get_nowait()
            except Empty:
                break

    def add_request(self, tokens: int = 1) -> tuple[int, bool, float]:
        self._leak()

        if self.q.qsize() + tokens <= self.bucket_capacity:
            for _ in range(tokens):
                self.q.put_nowait(time.monotonic())

            return self.q.qsize(), True, 0.0

        tokens_needed = (self.q.qsize() + tokens) - self.bucket_capacity
        wait_time = tokens_needed / self.leak_rate
        return self.q.qsize(), False, wait_time

    def get_state(self) -> dict[str, float | str]:
        self._leak()

        queue_size = self.q.qsize()

        return {
            "Name": "LeakyBucket",
            "queue_size": float(queue_size),
            "remaining_capacity": float(self.bucket_capacity - queue_size),
        }