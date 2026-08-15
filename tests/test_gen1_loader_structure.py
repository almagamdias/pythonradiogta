from __future__ import annotations

import shutil
import tempfile
from pathlib import Path

from radio.library.gen1 import Gen1Loader


TEST_DATA_ROOT = Path("test_data/GTA IV")


def create_station(
    root: Path,
    name: str,
    audio_sources: list[Path],
    *,
    extra_files: list[str] | None = None,
) -> Path:
    station_dir = root / name
    station_dir.mkdir()

    for source in audio_sources:
        shutil.copy2(
            source,
            station_dir / source.name,
        )

    for extra_name in extra_files or []:
        (station_dir / extra_name).touch()

    return station_dir


def main() -> None:
    print("Testing Gen1 loader filesystem structure...")

    massiveb = (
        TEST_DATA_ROOT
        / "04_MASSIVEB"
        / "MASSIVEB_MIX.ogg"
    )

    thebeat = (
        TEST_DATA_ROOT
        / "12_THEBEAT"
        / "THEBEAT_MIX.ogg"
    )

    ramjam = (
        TEST_DATA_ROOT
        / "13_RAMJAM"
        / "RAMJAM_MIX.ogg"
    )

    assert massiveb.is_file()
    assert thebeat.is_file()
    assert ramjam.is_file()

    with tempfile.TemporaryDirectory() as temp_dir:
        root = Path(temp_dir)

        # 1. Normal Gen1 station.
        create_station(
            root,
            "04_MASSIVEB",
            [massiveb],
            extra_files=[
                "logo.png",
                "readme.txt",
            ],
        )

        # 2. Another normal station.
        create_station(
            root,
            "12_THEBEAT",
            [thebeat],
        )

        # 3. Third normal station.
        create_station(
            root,
            "13_RAMJAM",
            [ramjam],
        )

        # 4. Directory without audio must not become a station.
        empty_dir = root / "NOT_A_STATION"
        empty_dir.mkdir()
        (empty_dir / "readme.txt").touch()

        print()
        print("Loading stations...")

        library = Gen1Loader().load(root)

        print(f"Stations detected: {len(library)}")

        assert len(library) == 3

        station_names = [
            station.name
            for station in library
        ]

        print("Detected stations:")

        for station in library:
            print(
                f"  {station.name}: "
                f"{station.songs[0].path.name} "
                f"({station.songs[0].duration} ms)"
            )

        assert station_names == [
            "04_MASSIVEB",
            "12_THEBEAT",
            "13_RAMJAM",
        ]

        # Every Gen1 station must contain exactly one audio source.
        for station in library:
            assert len(station.songs) == 1
            assert station.songs[0].path.suffix.lower() == ".ogg"
            assert station.songs[0].duration > 0

        # The directory without audio must not appear.
        assert "NOT_A_STATION" not in station_names

        print()
        print(
            "Directory without audio is correctly ignored."
        )

        print()
        print("Testing multiple audio files...")

        invalid_root = root / "invalid"
        invalid_root.mkdir()

        create_station(
            invalid_root,
            "BROKEN_STATION",
            [
                massiveb,
                thebeat,
            ],
        )

        try:
            Gen1Loader().load(invalid_root)
        except ValueError as exc:
            print(
                "Multiple audio files correctly rejected."
            )
            print(f"Error: {exc}")
        else:
            raise AssertionError(
                "Gen1 station with multiple audio files "
                "was accepted"
            )

    print()
    print(
        "Gen1 loader filesystem structure test passed."
    )


if __name__ == "__main__":
    main()
