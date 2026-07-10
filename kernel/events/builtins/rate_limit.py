from __future__ import annotations

import time

from kernel.events.event import Event
from kernel.events.middleware import BaseMiddleware


class TokenBucket:
    def __init__(self, rate: float, burst: int) -> None:
        self._rate = rate
        self._burst = burst
        self._tokens = float(burst)
        self._last = time.time()

    def consume(self) -> bool:
        now = time.time()
        elapsed = now - self._last
        self._tokens = min(float(self._burst), self._tokens + elapsed * self._rate)
        self._last = now
        if self._tokens >= 1.0:
            self._tokens -= 1.0
            return True
        return False


class RateLimitMiddleware(BaseMiddleware):
    def __init__(
        self,
        default_rate: float = 100.0,
        default_burst: int = 50,
    ) -> None:
        self._default_rate = default_rate
        self._default_burst = default_burst
        self._buckets: dict[str, TokenBucket] = {}
        self._overrides: dict[str, tuple[float, int]] = {}

    def set_rate(
        self,
        key: str,
        rate: float,
        burst: int,
    ) -> None:
        self._overrides[key] = (rate, burst)
        self._buckets.pop(key, None)

    def _bucket(self, key: str) -> TokenBucket:
        if key not in self._buckets:
            rate, burst = self._overrides.get(
                key,
                (self._default_rate, self._default_burst),
            )
            self._buckets[key] = TokenBucket(rate, burst)
        return self._buckets[key]

    async def before_publish(self, event: Event) -> Event:
        source_key = event.source or event.name
        if not self._bucket(source_key).consume():
            raise RuntimeError(f"Rate limit exceeded for '{source_key}'")
        return event
