from __future__ import annotations

from pathlib import Path

from PIL import Image, ImageTk


def load_logo_image(
    path: Path,
    *,
    size: tuple[int, int],
) -> Image.Image:
    """Load and resize a station logo as RGBA."""
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

    return canvas


def make_logo_frame(
    image: Image.Image,
    *,
    alpha: int,
) -> ImageTk.PhotoImage:
    """Create one cached Tk frame for a logo alpha."""
    frame = image.copy()

    alpha_channel = frame.getchannel("A")

    alpha_channel = alpha_channel.point(
        lambda value: value * alpha // 255,
    )

    frame.putalpha(alpha_channel)

    return ImageTk.PhotoImage(frame)
