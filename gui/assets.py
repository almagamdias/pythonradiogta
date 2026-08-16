from __future__ import annotations

from pathlib import Path

from PIL import Image, ImageTk


def load_logo(
    path: Path,
    *,
    size: tuple[int, int],
    alpha: int = 255,
) -> ImageTk.PhotoImage:
    """Load, resize and apply transparency to a station logo."""
    with Image.open(path) as source:
        image = source.convert("RGBA")
        image.thumbnail(
            size,
            Image.Resampling.LANCZOS,
        )

        canvas = Image.new(
            "RGBA",
            size,
            (0, 0, 0, 0),
        )

        x = (size[0] - image.width) // 2
        y = (size[1] - image.height) // 2

        canvas.paste(
            image,
            (x, y),
            image,
        )

        if alpha != 255:
            alpha_channel = canvas.getchannel("A")
            alpha_channel = alpha_channel.point(
                lambda value: value * alpha // 255,
            )
            canvas.putalpha(alpha_channel)

    return ImageTk.PhotoImage(canvas)
