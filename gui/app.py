from __future__ import annotations

from radio.engine import RadioEngine

from gui.window import RadioWindow


class RadioApp:
    """Application entry point for the radio GUI."""

    def __init__(self, engine: RadioEngine) -> None:
        self._window = RadioWindow(engine)

    def run(self) -> None:
        """Run the GUI event loop."""
        self._window.run()
