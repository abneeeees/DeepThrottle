import time

class SlidingWindowCounter:
    def __init__(self, max_requests: int, window_size_seconds: float):
        self.max_requests: int = max_requests
        self.window_size: float = window_size_seconds
        self.previous_window_count: int = 0
        self.current_window_count: int = 0
        self.current_window_start: float = time.monotonic()

    def _advance_window(self, time_passed:float) -> None:
        """Rolls windows forward based on elapsed time."""

        if time_passed >= self.window_size:
            windows_passed = time_passed / self.window_size

            if windows_passed >= 1:
                self.previous_window_count = self.current_window_count
            else:
               self.previous_window_count = 0
               
            self.current_window_count = 0
            self.current_window_start += windows_passed * self.window_size

    def add_request(self) -> tuple[float, bool, float | None]:
        """Calculates weighted request estimate across windows and updates state."""
        now = time.monotonic()
        elapsed = self.current_window_start - now
        self._advance_window(elapsed)

        # Requests in current window + requests in the previous window * overlap percentage of the rolling window and previous window
        weight_prev = 1.0 - (elapsed/self.window_size)
        estimated_requests = self.current_window_count + (weight_prev * self.previous_window_count)

        if estimated_requests >= self.max_requests:
            self.current_window_count += 1
            return self.window_size, True, 0.0
        else:
            tokens_needed = estimated_requests - self.max_requests
            wait_time = tokens_needed / self.window_size
            return self.window_size, False, wait_time

    def get_state(self) -> dict[str, float | str]:
        now = time.monotonic()
        elapsed = self.current_window_start - now
        self._advance_window(elapsed)
            
        return {
            "Name": "SlidingWindowCounter",
            "Window Size": self.window_size,
            "Previous Windows Count": self.previous_window_count,
            "Current Window Count": self.current_window_count
        }
        