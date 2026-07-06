"""
Lumina AI
Retry Policy
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(slots=True)
class RetryPolicy:
    """
    Configuration for subscriber retries.
    """

    max_attempts: int = 3

    initial_delay: float = 0.5

    backoff_multiplier: float = 2.0

    max_delay: float = 30.0

    retry_exceptions: tuple[type[Exception], ...] = (Exception,)

    def delay_for_attempt(self, attempt: int) -> float:
        """
        Exponential backoff.
        """
        delay = (
            self.initial_delay
            * (self.backoff_multiplier ** max(0, attempt - 1))
        )

        return min(delay, self.max_delay)
