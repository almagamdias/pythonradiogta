from __future__ import annotations

from collections.abc import Callable
from threading import Lock, Timer


class SwitchTimer:
    """One-shot timer that can be restarted."""

    def __init__(
        self,
        delay: float,
        callback: Callable[[], None],
    ) -> None:
        self._delay = delay
        self._callback = callback

        self._timer: Timer | None = None
        self._lock = Lock()

    def start(self) -> None:
        """Start or restart the timer."""
        with self._lock:
            self._cancel_locked()

            self._timer = Timer(
                self._delay,
                self._run,
            )
            self._timer.daemon = True
            self._timer.start()

    def cancel(self) -> None:
        """Cancel the current timer."""
        with self._lock:
            self._cancel_locked()

    def _cancel_locked(self) -> None:
        if self._timer is None:
            return

        self._timer.cancel()
        self._timer = None

    def _run(self) -> None:
        with self._lock:
            self._timer = None

        self._callback()
