from __future__ import annotations

from pathlib import Path


AUDIO_EXTENSIONS = frozenset({
    ".ogg",
    ".mp3",
    ".wav",
    ".flac",
})

IMAGE_EXTENSIONS = frozenset({
    ".png",
    ".jpg",
    ".jpeg",
    ".bmp",
    ".webp",
})

def find_files(
    directory: Path,
    extensions: frozenset[str],
) -> list[Path]:
    """
    Return all files in directory with specified extensions.
    """

    return sorted(
        (
            path
            for path in directory.iterdir()
            if path.is_file() and path.suffix.lower() in extensions
        ),
        key=lambda path: path.name.casefold(),
    )

def is_audio_file(path: Path) -> bool:
    return path.is_file() and path.suffix.lower() in AUDIO_EXTENSIONS

def is_image_file(path: Path) -> bool:
    return path.is_file() and path.suffix.lower() in IMAGE_EXTENSIONS

def find_audio(directory: Path) -> list[Path]:
    return find_files(directory, AUDIO_EXTENSIONS)

def find_logo(directory: Path) -> list[Path]:
    return find_files(directory, IMAGE_EXTENSIONS)

def list_directories(directory: Path) -> list[Path]:
    """
    Return child directories sorted by name.
    """

    return sorted(
        (
            path
            for path in directory.iterdir()
            if path.is_dir()
        ),
        key=lambda path: path.name.casefold(),
    )

def normalize_path(path: Path) -> Path:
    """
    Return normalized absolute path.
    """

    return path.expanduser().resolve()
