from __future__ import annotations

import tkinter as tk

from radio.engine import RadioEngine
from radio.model.station import Station

from gui.assets import load_logo


SLOT_WIDTH = 190
SLOT_HEIGHT = 130
SLOT_GAP = 10

CANVAS_WIDTH = (
    SLOT_WIDTH * 5
    + SLOT_GAP * 4
)

ANIMATION_DURATION_MS = 100
ANIMATION_STEPS = 10

STEP_WIDTH = SLOT_WIDTH + SLOT_GAP


class StationCarousel:
    """Display five stations around the pending station."""

    VISIBLE_COUNT = 5
    CENTER_OFFSET = 2

    LOGO_SIZE = (180, 115)

    def __init__(
        self,
        parent: tk.Misc,
        engine: RadioEngine,
    ) -> None:
        self._engine = engine

        self._canvas = tk.Canvas(
            parent,
            width=CANVAS_WIDTH,
            height=SLOT_HEIGHT,
            highlightthickness=0,
        )

        self._canvas.pack(
            padx=20,
            pady=40,
        )

        self._images: list[object | None] = []

        self._items: list[int] = []

        self._animation_running = False
        self._animation_direction = 0
        self._animation_step = 0
        self._animation_delta = 0.0
        self._animation_queue: list[int] = []

        self._visible_indices: list[int] = []

        self._draw_slots()
        self.refresh()

    def _draw_slots(self) -> None:
        """Draw the fixed five carousel slots."""
        for position in range(
            self.VISIBLE_COUNT
        ):
            x = position * STEP_WIDTH

            self._canvas.create_rectangle(
                x,
                0,
                x + SLOT_WIDTH,
                SLOT_HEIGHT,
                outline="",
                fill="",
                tags="slot",
            )

    def refresh(self) -> None:
        """Synchronously rebuild the visible five stations."""
        if self._animation_running:
            return

        stations = self._engine.stations

        if not stations:
            return

        center = self._center_index()

        self._visible_indices = [
            (
                center + offset
            ) % len(stations)
            for offset in range(-2, 3)
        ]

        self._rebuild_visible()

    def _rebuild_visible(self) -> None:
        """Rebuild the five visible Canvas items."""
        self._canvas.delete("station")

        self._items.clear()
        self._images.clear()

        for position, station_index in enumerate(
            self._visible_indices
        ):
            station = self._engine.stations[
                station_index
            ]

            item = self._create_station(
                position,
                station,
            )

            self._items.append(item)

    def _create_station(
        self,
        position: int,
        station: Station,
    ) -> int:
        """Create one station at a carousel position."""
        x = (
            position * STEP_WIDTH
            + SLOT_WIDTH // 2
        )

        y = SLOT_HEIGHT // 2

        if station.logo is None:
            item = self._canvas.create_text(
                x,
                y,
                text=station.name,
                tags="station",
            )

            self._images.append(None)

            return item

        image = load_logo(
            station.logo,
            size=self.LOGO_SIZE,
        )

        self._images.append(image)

        return self._canvas.create_image(
            x,
            y,
            image=image,
            anchor=tk.CENTER,
            tags="station",
        )

    def animate_next(self) -> None:
        """Queue one forward carousel movement."""
        self._animation_queue.append(1)

        if not self._animation_running:
            self._start_queued_animation()


    def animate_previous(self) -> None:
        """Queue one backward carousel movement."""
        self._animation_queue.append(-1)

        if not self._animation_running:
            self._start_queued_animation()

    def _start_animation(
        self,
        *,
        direction: int,
    ) -> None:
        if self._animation_running:
            return

        stations = self._engine.stations

        if not stations:
            return

        if len(stations) <= 1:
            return

        self._animation_running = True
        self._animation_direction = direction
        self._animation_step = 0
        self._animation_delta = 0.0

        self._prepare_animation()

        self._animate_step()

    def _prepare_animation(self) -> None:
        """Create the incoming station outside the visible area."""
        stations = self._engine.stations

        current_center = self._visible_indices[
            self.CENTER_OFFSET
        ]

        if self._animation_direction > 0:
            incoming_index = (
                current_center + 3
            ) % len(stations)

            incoming_position = self.VISIBLE_COUNT

        else:
            incoming_index = (
                current_center - 3
            ) % len(stations)

            incoming_position = -1

        station = stations[incoming_index]

        item = self._create_station(
            incoming_position,
            station,
        )

        self._items.append(item)

    def _animate_step(self) -> None:
        """Animate one frame of the current carousel movement."""
        if not self._animation_running:
            return

        if self._animation_step >= ANIMATION_STEPS:
            self._finish_animation()
            return

        self._animation_step += 1

        linear_progress = (
            self._animation_step
            / ANIMATION_STEPS
        )

        # Smooth ease-in-out.
        progress = (
            3 * linear_progress ** 2
            - 2 * linear_progress ** 3
        )

        current_distance = (
            STEP_WIDTH * progress
        )

        delta = (
            current_distance
            - self._animation_delta
        )

        self._animation_delta = current_distance

        if self._animation_direction > 0:
            delta_x = -delta
        else:
            delta_x = delta

        for item in self._items:
            self._canvas.move(
                item,
                delta_x,
                0,
            )

        delay = max(
            1,
            ANIMATION_DURATION_MS
            // ANIMATION_STEPS,
        )

        self._canvas.after(
            delay,
            self._animate_step,
        )

    def _start_queued_animation(self) -> None:
        """Start the next queued carousel movement."""
        if self._animation_running:
            return

        if not self._animation_queue:
            return

        direction = self._animation_queue.pop(0)

        self._animation_running = True
        self._animation_direction = direction
        self._animation_step = 0
        self._animation_delta = 0.0

        self._prepare_animation()

        self._animate_step()

    def _finish_animation(self) -> None:
        """Finish one animation and continue the visual queue."""
        direction = self._animation_direction

        self._animation_running = False
        self._animation_direction = 0
        self._animation_step = 0
        self._animation_delta = 0.0

        if direction > 0:
            # next_station:
            # 04 12 13 18 19
            # ->
            # 12 13 18 19 23
            self._visible_indices = [
                (index + 1)
                % len(self._engine.stations)
                for index in self._visible_indices
            ]

        else:
            # previous_station:
            # 12 13 18 19 23
            # <-
            # 04 12 13 18 19
            self._visible_indices = [
                (index - 1)
                % len(self._engine.stations)
                for index in self._visible_indices
            ]

        self._rebuild_visible()

        if self._animation_queue:
            self._start_queued_animation()

    def _center_index(self) -> int:
        """Return the station index represented in the center."""
        pending = self._engine.pending_station

        if pending is not None:
            for index, station in enumerate(
                self._engine.stations
            ):
                if station is pending:
                    return index

        for index, station in enumerate(
            self._engine.stations
        ):
            if station is self._engine.current_station:
                return index

        return 0
