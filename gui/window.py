from __future__ import annotations

import time
import tkinter as tk

from radio.engine import RadioEngine

from gui.carousel import StationCarousel

BACKEND_INPUT_COOLDOWN_MS = 100


class RadioWindow:
    """Main radio window."""

    MOUSE_WHEEL_DEBOUNCE = 0.08

    def __init__(self, engine: RadioEngine) -> None:
        self._engine = engine

        self._root = tk.Tk()
        self._root.title("GTA Radio Simulator")
        self._root.geometry("1150x340")
        self._root.resizable(False, False)

        self._carousel = StationCarousel(
            self._root,
            engine,
        )

        self._backend_input_locked = False

        self._last_wheel_time = 0.0

        self._bind_input()

    def _bind_input(self) -> None:
        self._root.bind(
            "<Left>",
            self._previous_station,
        )
        self._root.bind(
            "<Right>",
            self._next_station,
        )

        # Linux/X11 wheel events.
        self._root.bind(
            "<Button-4>",
            self._wheel_up,
        )
        self._root.bind(
            "<Button-5>",
            self._wheel_down,
        )

    def _previous_station(
        self,
        event: tk.Event | None = None,
    ) -> None:
        if self._backend_input_locked:
            return

        self._backend_input_locked = True

        self._engine.previous_station()
        self._carousel.animate_previous()

        self._root.after(
            BACKEND_INPUT_COOLDOWN_MS,
            self._unlock_backend_input,
        )


    def _next_station(
        self,
        event: tk.Event | None = None,
    ) -> None:
        if self._backend_input_locked:
            return

        self._backend_input_locked = True

        self._engine.next_station()
        self._carousel.animate_next()

        self._root.after(
            BACKEND_INPUT_COOLDOWN_MS,
            self._unlock_backend_input,
        )


    def _unlock_backend_input(self) -> None:
        self._backend_input_locked = False

    def _wheel_allowed(self) -> bool:
        now = time.monotonic()

        if (
            now - self._last_wheel_time
            < self.MOUSE_WHEEL_DEBOUNCE
        ):
            return False

        self._last_wheel_time = now
        return True

    def _wheel_up(
        self,
        event: tk.Event | None = None,
    ) -> None:
        if not self._wheel_allowed():
            return

        self._next_station()

    def _wheel_down(
        self,
        event: tk.Event | None = None,
    ) -> None:
        if not self._wheel_allowed():
            return

        self._previous_station()

    def run(self) -> None:
        """Start the GUI event loop."""
        self._root.mainloop()
