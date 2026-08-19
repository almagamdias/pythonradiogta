from __future__ import annotations

import time
import tkinter as tk

from radio.engine import RadioEngine
from radio.model.station_state import StationState

from gui.carousel import StationCarousel


BACKEND_INPUT_COOLDOWN_MS = 30


class RadioWindow:
    """Main radio window."""

    MOUSE_WHEEL_DEBOUNCE = 0.08

    def __init__(
        self,
        engine: RadioEngine,
    ) -> None:
        self._engine = engine

        self._root = tk.Tk()
        self._root.title("GTA Radio Simulator")
        self._root.geometry("1150x340")
        self._root.resizable(
            False,
            False,
        )

        self._root.protocol(
            "WM_DELETE_WINDOW",
            self._on_close,
        )

        self._carousel = StationCarousel(
            self._root,
            engine,
        )

        self._backend_input_locked = False
        self._last_wheel_time = 0.0

        self._last_pending_station = (
            engine.pending_station
        )

        self._last_current_station = (
            engine.current_station
        )

        self._pending_poll_id: str | None = None

        self._play_button = tk.Button(
            self._root,
            text="▶ PLAY",
            width=12,
            command=self._toggle_playback,
        )

        self._play_button.pack(
            pady=(0, 5),
        )

        self._bind_input()
        self._update_play_button()
        self._poll_pending_station()

    # ------------------------------------------------------------------
    # Window
    # ------------------------------------------------------------------

    def _on_close(self) -> None:
        """Stop radio playback and close the GUI."""
        self._engine.stop()
        self._root.destroy()

    # ------------------------------------------------------------------
    # Playback
    # ------------------------------------------------------------------

    def _toggle_playback(self) -> None:
        """Start or stop radio playback."""
        if self._engine.state is StationState.OFF:
            self._engine.play()
        else:
            self._engine.stop()
            self._carousel.set_transparent()
            self._carousel.refresh()

        self._update_play_button()

    def _update_play_button(self) -> None:
        """Update the play/stop button text."""
        if self._engine.state is StationState.OFF:
            self._play_button.configure(
                text="▶ PLAY",
            )
            return

        self._play_button.configure(
            text="■ STOP",
        )

    # ------------------------------------------------------------------
    # Engine state polling
    # ------------------------------------------------------------------

    def _poll_pending_station(self) -> None:
        """Watch radio state for carousel visibility."""

        pending = self._engine.pending_station
        current = self._engine.current_station

        pending_changed = (
            pending is not self._last_pending_station
        )

        current_changed = (
            current is not self._last_current_station
        )

        if pending_changed:
            self._last_pending_station = pending

            if pending is not None:
                # A station selection has started.
                self._carousel.show()

        if current_changed:
            self._last_current_station = current

        # The selection is finalized when there is no pending
        # station and the current station is up to date.
        if (
            pending is None
            and (
                pending_changed
                or current_changed
            )
        ):
            self._carousel.schedule_fade_out()

        self._update_play_button()

        self._pending_poll_id = self._root.after(
            50,
            self._poll_pending_station,
        )

    # ------------------------------------------------------------------
    # Input
    # ------------------------------------------------------------------

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

        # Space toggles radio playback.
        self._root.bind(
            "<space>",
            self._toggle_playback_event,
        )

    def _toggle_playback_event(
        self,
        event: tk.Event | None = None,
    ) -> str:
        """Toggle playback from the keyboard."""
        self._toggle_playback()

        return "break"

    def _previous_station(
        self,
        event: tk.Event | None = None,
    ) -> None:
        if self._backend_input_locked:
            return

        self._backend_input_locked = True

        if self._engine.state is StationState.OFF:
            self._engine.play()

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

        if self._engine.state is StationState.OFF:
            self._engine.play()

        self._engine.next_station()
        self._carousel.animate_next()

        self._root.after(
            BACKEND_INPUT_COOLDOWN_MS,
            self._unlock_backend_input,
        )

    def _unlock_backend_input(self) -> None:
        self._backend_input_locked = False

    # ------------------------------------------------------------------
    # Mouse wheel
    # ------------------------------------------------------------------

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

    # ------------------------------------------------------------------
    # Main loop
    # ------------------------------------------------------------------

    def run(self) -> None:
        """Start the GUI event loop."""
        self._root.mainloop()
