"""
Project-specific exceptions.

All internal modules should raise only these exceptions.
"""


class RadioError(Exception):
    """Base exception for the project."""


#
# Library
#

class LibraryError(RadioError):
    """Library loading error."""


class InvalidLibraryError(LibraryError):
    """Invalid library structure."""


class InvalidStationError(LibraryError):
    """Invalid station structure."""


class StationNotFoundError(LibraryError):
    """Station was not found."""


#
# Audio
#

class AudioError(RadioError):
    """Audio subsystem error."""


class AudioMetadataError(AudioError):
    """Unable to read audio metadata."""


class AudioPlaybackError(AudioError):
    """Audio playback error."""
