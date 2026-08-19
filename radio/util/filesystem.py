"""
Filesystem utilities.

All filesystem operations used by the project are centralized here.
"""

from __future__ import annotations

from pathlib import Path

from radio.constants import LOGO_NAMES

_AUDIO_EXTENSIONS = frozenset({
    ".ogg",
    ".mp3",
    ".wav",
    ".flac",
})


def list_directories(root: Path) -> list[Path]:
    """
    Return sorted child directories.
    """

    return sorted(
        (
            path
            for path in root.iterdir()
            if path.is_dir()
        ),
        key=lambda path: path.name.casefold(),
    )


def find_audio_files(directory: Path) -> list[Path]:
    """
    Return sorted audio files in a directory.
    """

    return sorted(
        (
            path
            for path in directory.iterdir()
            if path.is_file()
            and path.suffix.casefold() in _AUDIO_EXTENSIONS
        ),
        key=lambda path: path.name.casefold(),
    )


def find_logo(directory: Path) -> Path | None:
    """
    Return station logo if it exists.
    """

    for logo_name in LOGO_NAMES:
        logo = directory / logo_name

        if logo.is_file():
            return logo

    return None
