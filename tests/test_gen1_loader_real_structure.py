from __future__ import annotations

from pathlib import Path

from radio.library.gen1 import Gen1Loader


TEST_ROOT = Path("test_data/GTA IV")

EXPECTED_STATIONS = [
    "04_MASSIVEB",
    "12_THEBEAT",
    "13_RAMJAM",
    "18_ELECTROCHOC",
    "19_THECLASSICS",
]


def main() -> None:
    print("Testing Gen1 loader with real filesystem structure...")

    assert TEST_ROOT.is_dir(), (
        f"Test data directory does not exist: {TEST_ROOT}"
    )

    print()
    print("Loading real Gen1 stations...")

    library = Gen1Loader().load(TEST_ROOT)

    print(f"Stations detected: {len(library)}")

    assert len(library) == len(EXPECTED_STATIONS)

    station_names = [
        station.name
        for station in library
    ]

    print()
    print("Detected stations:")

    for station in library:
        song = station.songs[0]

        print(
            f"  {station.name}: "
            f"{song.path.name} "
            f"({song.duration} ms)"
        )

    print()
    print("Checking station order...")

    assert station_names == EXPECTED_STATIONS

    print("Station order is correct.")

    print()
    print("Checking every station...")

    for station in library:
        # Gen1 = exactly one audio source.
        assert len(station.songs) == 1

        song = station.songs[0]

        # The station directory is the parent of its audio source.
        station_dir = song.path.parent

        # Station directory must exist.
        assert station_dir.is_dir()

        # Song file must actually exist.
        assert song.path.is_file()

        # Gen1 source must be OGG.
        assert song.path.suffix.lower() == ".ogg"

        # Metadata reader must have obtained a real duration.
        assert song.duration > 0

        # The audio file must be located inside a directory
        # whose name matches the station name.
        assert station_dir.name == station.name

        print(
            f"  OK: {station.name} "
            f"-> {song.path.name} "
            f"-> {song.duration} ms"
        )

    print()
    print("Checking UNUSED directory...")

    assert not any(
        station.name == "UNUSED"
        for station in library
    )

    print("UNUSED is correctly ignored.")

    print()
    print("Checking expected audio files...")

    expected_files = {
        "04_MASSIVEB": "MASSIVEB_MIX.ogg",
        "12_THEBEAT": "THEBEAT_MIX.ogg",
        "13_RAMJAM": "RAMJAM_MIX.ogg",
        "18_ELECTROCHOC": "ELECTRO_MIX.ogg",
        "19_THECLASSICS": "THECLASSICS_MIX.ogg",
    }

    for station in library:
        expected_file = expected_files[station.name]
        actual_file = station.songs[0].path.name

        assert actual_file == expected_file

        print(
            f"  {station.name}: "
            f"{actual_file}"
        )

    print()
    print("Checking that non-audio files do not affect loading...")

    for station in library:
        song = station.songs[0]
        station_dir = song.path.parent

        audio_files = [
            path
            for path in station_dir.iterdir()
            if path.is_file()
            and path.suffix.lower() == ".ogg"
        ]

        assert len(audio_files) == 1
        assert audio_files[0] == song.path

    print(
        "Every station contains exactly one .ogg source."
    )

    print()
    print("Real Gen1 filesystem structure test passed.")


if __name__ == "__main__":
    main()
