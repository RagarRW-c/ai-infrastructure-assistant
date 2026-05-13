import time
from collections import defaultdict, deque
from threading import Lock

from fastapi import Request


class RateLimiter:
    def __init__(self, max_requests: int, window_seconds: int):
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self._requests: dict[str, deque[float]] = defaultdict(deque)
        self._lock = Lock()

    def check(self, key: str, now: float | None = None) -> tuple[bool, int]:
        if self.max_requests <= 0 or self.window_seconds <= 0:
            return True, 0

        current_time = now if now is not None else time.monotonic()
        window_start = current_time - self.window_seconds

        with self._lock:
            requests = self._requests[key]
            while requests and requests[0] <= window_start:
                requests.popleft()

            if len(requests) >= self.max_requests:
                retry_after = max(1, int(requests[0] + self.window_seconds - current_time) + 1)
                return False, retry_after

            requests.append(current_time)
            return True, 0

    def reset(self) -> None:
        with self._lock:
            self._requests.clear()


def get_client_identifier(request: Request) -> str:
    forwarded_for = request.headers.get("x-forwarded-for")
    if forwarded_for:
        return forwarded_for.split(",", 1)[0].strip()

    real_ip = request.headers.get("x-real-ip")
    if real_ip:
        return real_ip.strip()

    if request.client:
        return request.client.host

    return "unknown"
