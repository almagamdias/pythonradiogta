"""
Audio metadata reader.

This module isolates mutagen from the rest of the project.
"""

from __future__ import annotations

from pathlib import Path

from mutagen import File
from mutagen import MutagenError

from radio.errors import AudioMetadataError
from radio.model.types import Milliseconds


def read_duration(path: Path) -> Milliseconds:
    """
    Read audio duration.

    Parameters
    ----------
    path:
        Path to an audio file.

    Returns
    -------
    Milliseconds
        Audio duration in milliseconds.

    Raises
    ------
    AudioMetadataError
        If the metadata cannot be read.
    """

    audio = _load_audio(path)

    if audio.info is None:
        raise AudioMetadataError(
            f"Missing audio metadata: {path}"
        )

    return round(audio.info.length * 1000)


def _load_audio(path: Path):
    """
    Load audio metadata using mutagen.
    """

    try:
        audio = File(path)

    except (
        FileNotFoundError,
        PermissionError,
        MutagenError,
        OSError,
    ) as exc:
        raise AudioMetadataError(
            f"Unable to read metadata: {path}"
        ) from exc

    if audio is None:
        raise AudioMetadataError(
            f"Unsupported audio format: {path}"
        )

    return audio
