from pathlib import Path

from radio.library.gen1 import Gen1Loader


def main() -> None:
    loader = Gen1Loader()

    library = loader.load(
        Path("test_data/GTA IV")
    )

    print(f"Stations: {len(library.stations)}")
    print()

    for station in library.stations:
        song = station.songs[0]

        print(station.name)
        print(f"  Song     : {song.title}")
        print(f"  Duration : {song.duration} ms")
        print(f"  Logo     : {station.logo}")
        print()


if __name__ == "__main__":
    main()
