from __future__ import annotations

import tkinter as tk
from pathlib import Path
from tkinter import Misc

from PIL import Image, ImageTk

from radio.engine import RadioEngine
from radio.model.station import Station

from gui.assets import (
    load_logo_image,
    make_logo_frame,
)


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

FADE_OUT_DELAY_MS = 1600
FADE_OUT_DURATION_MS = 400
FADE_OUT_STEPS = 20

FADE_OUT_STEP_MS = (
    FADE_OUT_DURATION_MS // FADE_OUT_STEPS
)

# Positional logo gradient.
GRADIENT_CENTER_ALPHA = 255
GRADIENT_SIDE_ALPHA = 150
GRADIENT_EDGE_ALPHA = 35


class StationCarousel:
    """Display five stations around the pending station."""

    VISIBLE_COUNT = 5
    CENTER_OFFSET = 2

    LOGO_SIZE = (180, 115)

    def __init__(
        self,
        parent: Misc,
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

        # Canvas item IDs.
        self._items: list[int] = []

        # Currently displayed PIL images.
        self._logo_images: list[
            Image.Image | None
        ] = []

        # Currently displayed Tk images.
        self._images: list[
            ImageTk.PhotoImage | None
        ] = []

        # Cache of resized RGBA logos.
        self._logo_cache: dict[
            Path,
            Image.Image,
        ] = {}

        # Cache of Tk frames.
        #
        # Key:
        #     (logo path, alpha)
        #
        # This prevents expensive Pillow work during
        # repeated animation/fade frames.
        self._frame_cache: dict[
            tuple[Path, int],
            ImageTk.PhotoImage,
        ] = {}

        # Maps Canvas item -> original logo path.
        self._item_logo_paths: dict[
            int,
            Path,
        ] = {}

        # Maps Canvas item -> original resized PIL image.
        self._item_logo_images: dict[
            int,
            Image.Image,
        ] = {}

        # Current five visible station indices.
        self._visible_indices: list[int] = []

        # Animation state.
        self._animation_running = False
        self._animation_direction = 0
        self._animation_step = 0
        self._animation_delta = 0.0

        self._animation_queue: list[int] = []

        # Global carousel alpha.
        #
        # 0   = completely transparent
        # 255 = completely visible
        #
        # This is separate from the positional gradient.
        self._alpha = 0

        # Fade-out timers.
        self._fade_out_delay_id: str | None = None
        self._fade_out_after_id: str | None = None

        self._draw_slots()

        # Build everything while invisible.
        self.refresh()

    def set_transparent(self) -> None:
        self._alpha = 0

    # ------------------------------------------------------------------
    # Slots
    # ------------------------------------------------------------------

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

    # ------------------------------------------------------------------
    # Visibility
    # ------------------------------------------------------------------

    def show(self) -> None:
        """Show the carousel immediately."""
        self._cancel_fade_out()

        if self._alpha == 255:
            return

        self._alpha = 255

        self._rebuild_visible()

    def schedule_fade_out(self) -> None:
        """Schedule fade-out after final station selection."""
        self._cancel_fade_out()

        if self._alpha <= 0:
            return

        self._fade_out_delay_id = self._canvas.after(
            FADE_OUT_DELAY_MS,
            self._start_fade_out,
        )

    def _start_fade_out(self) -> None:
        """Start the fade-out."""
        self._fade_out_delay_id = None

        if self._alpha <= 0:
            return

        self._fade_out_step()

    def _fade_out_step(self) -> None:
        """Perform one fade-out frame."""
        if self._alpha <= 0:
            self._alpha = 0
            self._fade_out_after_id = None
            return

        self._alpha = max(
            0,
            self._alpha
            - (
                255
                // FADE_OUT_STEPS
            ),
        )

        self._rebuild_visible()

        if self._alpha <= 0:
            self._alpha = 0
            self._fade_out_after_id = None
            return

        self._fade_out_after_id = (
            self._canvas.after(
                FADE_OUT_STEP_MS,
                self._fade_out_step,
            )
        )

    def _cancel_fade_out(self) -> None:
        """Cancel pending or active fade-out."""
        if self._fade_out_delay_id is not None:
            self._canvas.after_cancel(
                self._fade_out_delay_id,
            )

            self._fade_out_delay_id = None

        if self._fade_out_after_id is not None:
            self._canvas.after_cancel(
                self._fade_out_after_id,
            )

            self._fade_out_after_id = None

    # ------------------------------------------------------------------
    # Logo cache
    # ------------------------------------------------------------------

    def _get_logo_image(
        self,
        path: Path,
    ) -> Image.Image:
        """Return cached resized RGBA logo."""
        image = self._logo_cache.get(path)

        if image is None:
            image = load_logo_image(
                path,
                size=self.LOGO_SIZE,
            )

            self._logo_cache[path] = image

        return image

    def _get_logo_frame(
        self,
        path: Path,
        image: Image.Image,
        alpha: int,
    ) -> ImageTk.PhotoImage:
        """Return cached Tk image for a logo alpha."""
        alpha = max(
            0,
            min(
                255,
                alpha,
            ),
        )

        key = (
            path,
            alpha,
        )

        frame = self._frame_cache.get(key)

        if frame is None:
            frame = make_logo_frame(
                image,
                alpha=alpha,
            )

            self._frame_cache[key] = frame

        return frame

    # ------------------------------------------------------------------
    # Positional gradient
    # ------------------------------------------------------------------

    def _gradient_alpha(
        self,
        x: float,
    ) -> int:
        """
        Return positional alpha based on Canvas X.

        The center is fully visible.
        Moving away from the center gradually
        reduces the logo opacity.
        """
        center_x = (
            self.CENTER_OFFSET * STEP_WIDTH
            + SLOT_WIDTH / 2
        )

        distance = abs(
            x - center_x
        )

        first_range = STEP_WIDTH
        second_range = STEP_WIDTH * 2

        if distance >= second_range:
            return GRADIENT_EDGE_ALPHA

        if distance >= first_range:
            progress = (
                distance - first_range
            ) / STEP_WIDTH

            return int(
                GRADIENT_SIDE_ALPHA
                + (
                    GRADIENT_EDGE_ALPHA
                    - GRADIENT_SIDE_ALPHA
                )
                * progress
            )

        progress = (
            distance / STEP_WIDTH
        )

        return int(
            GRADIENT_CENTER_ALPHA
            + (
                GRADIENT_SIDE_ALPHA
                - GRADIENT_CENTER_ALPHA
            )
            * progress
        )

    def _set_item_alpha(
        self,
        item: int,
        alpha: int,
    ) -> None:
        """Update one Canvas logo alpha."""
        path = self._item_logo_paths.get(
            item
        )

        if path is None:
            return

        image = self._item_logo_images.get(
            item
        )

        if image is None:
            return

        frame = self._get_logo_frame(
            path,
            image,
            alpha,
        )

        self._canvas.itemconfigure(
            item,
            image=frame,
        )

    def _update_gradient(self) -> None:
        """
        Update logo transparency according to
        current Canvas position.
        """
        for item in self._items:
            coords = self._canvas.coords(
                item
            )

            if not coords:
                continue

            x = coords[0]

            gradient_alpha = (
                self._gradient_alpha(x)
            )

            # Combine positional gradient with
            # global fade alpha.
            alpha = (
                gradient_alpha
                * self._alpha
                // 255
            )

            self._set_item_alpha(
                item,
                alpha,
            )

    # ------------------------------------------------------------------
    # Station layout
    # ------------------------------------------------------------------

    def refresh(self) -> None:
        """Synchronously rebuild the five visible stations."""
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
        self._canvas.delete(
            "station"
        )

        self._items.clear()
        self._logo_images.clear()
        self._images.clear()

        self._item_logo_paths.clear()
        self._item_logo_images.clear()

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

            self._items.append(
                item
            )

        # Apply the positional gradient
        # immediately after creating items.
        self._update_gradient()

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

            self._logo_images.append(
                None
            )

            self._images.append(
                None
            )

            return item

        logo = self._get_logo_image(
            station.logo
        )

        self._logo_images.append(
            logo
        )

        # Initial frame. The actual positional
        # alpha is applied by _update_gradient().
        image = self._get_logo_frame(
            station.logo,
            logo,
            0,
        )

        item = self._canvas.create_image(
            x,
            y,
            image=image,
            anchor=tk.CENTER,
            tags="station",
        )

        self._images.append(
            image
        )

        self._item_logo_paths[
            item
        ] = station.logo

        self._item_logo_images[
            item
        ] = logo

        return item

    # ------------------------------------------------------------------
    # Carousel animation
    # ------------------------------------------------------------------

    def animate_next(self) -> None:
        """Queue one forward carousel movement."""
        self._cancel_fade_out()

        # First input makes the carousel visible.
        self.show()

        self._animation_queue.append(
            1
        )

        if not self._animation_running:
            self._start_queued_animation()

    def animate_previous(self) -> None:
        """Queue one backward carousel movement."""
        self._cancel_fade_out()

        # First input makes the carousel visible.
        self.show()

        self._animation_queue.append(
            -1
        )

        if not self._animation_running:
            self._start_queued_animation()

    def _start_queued_animation(self) -> None:
        """Start the next queued movement."""
        if self._animation_running:
            return

        if not self._animation_queue:
            return

        direction = (
            self._animation_queue.pop(0)
        )

        self._start_animation(
            direction=direction,
        )

    def _start_animation(
        self,
        *,
        direction: int,
    ) -> None:
        """Start one carousel animation."""
        stations = self._engine.stations

        if not stations:
            return

        if len(stations) <= 1:
            return

        self._animation_running = True
        self._animation_direction = (
            direction
        )
        self._animation_step = 0
        self._animation_delta = 0.0

        self._prepare_animation()

        self._animate_step()

    def _prepare_animation(self) -> None:
        """Create incoming station outside visible area."""
        stations = self._engine.stations

        current_center = (
            self._visible_indices[
                self.CENTER_OFFSET
            ]
        )

        if self._animation_direction > 0:
            incoming_index = (
                current_center + 3
            ) % len(stations)

            incoming_position = (
                self.VISIBLE_COUNT
            )

        else:
            incoming_index = (
                current_center - 3
            ) % len(stations)

            incoming_position = -1

        station = stations[
            incoming_index
        ]

        item = self._create_station(
            incoming_position,
            station,
        )

        self._items.append(item)

        # The incoming item is initially outside
        # the normal gradient area, so update it now.
        self._update_gradient()

    def _animate_step(self) -> None:
        """Animate one frame."""
        if not self._animation_running:
            return

        if (
            self._animation_step
            >= ANIMATION_STEPS
        ):
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

        self._animation_delta = (
            current_distance
        )

        if (
            self._animation_direction
            > 0
        ):
            delta_x = -delta
        else:
            delta_x = delta

        for item in self._items:
            self._canvas.move(
                item,
                delta_x,
                0,
            )

        # Recalculate gradient using the
        # new physical positions.
        self._update_gradient()

        delay = max(
            1,
            ANIMATION_DURATION_MS
            // ANIMATION_STEPS,
        )

        self._canvas.after(
            delay,
            self._animate_step,
        )

    def _finish_animation(self) -> None:
        """Finish one movement and continue the queue."""
        direction = (
            self._animation_direction
        )

        self._animation_running = False
        self._animation_direction = 0
        self._animation_step = 0
        self._animation_delta = 0.0

        if direction > 0:
            self._visible_indices = [
                (
                    index + 1
                )
                % len(
                    self._engine.stations
                )
                for index in self._visible_indices
            ]

        else:
            self._visible_indices = [
                (
                    index - 1
                )
                % len(
                    self._engine.stations
                )
                for index in self._visible_indices
            ]

        self._rebuild_visible()

        if self._animation_queue:
            self._start_queued_animation()

    # ------------------------------------------------------------------
    # Center station
    # ------------------------------------------------------------------

    def _center_index(self) -> int:
        """Return the station index represented in the center."""
        pending = (
            self._engine.pending_station
        )

        if pending is not None:
            for index, station in enumerate(
                self._engine.stations
            ):
                if station is pending:
                    return index

        current = (
            self._engine.current_station
        )

        if current is not None:
            for index, station in enumerate(
                self._engine.stations
            ):
                if station is current:
                    return index

        return 0
