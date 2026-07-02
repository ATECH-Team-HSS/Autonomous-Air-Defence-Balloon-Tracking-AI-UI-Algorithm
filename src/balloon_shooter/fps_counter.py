from __future__ import annotations

import time
from collections import deque


class FPSCounter:
    """Measures frames per second over a rolling window."""

    def __init__(self, avg_over: int = 30) -> None:
        if avg_over < 2:
            raise ValueError("avg_over must be at least 2")
        self._timestamps: deque[float] = deque(maxlen=avg_over)
        self.fps = 0.0

    def update(self) -> float:
        now = time.time()
        self._timestamps.append(now)

        if len(self._timestamps) > 1:
            elapsed = self._timestamps[-1] - self._timestamps[0]
            self.fps = (len(self._timestamps) - 1) / elapsed if elapsed > 0 else 0.0

        return self.fps
