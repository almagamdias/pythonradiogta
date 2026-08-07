from radio import RadioEngine
from pathlib import Path

from radio.util.filesystem import (
    find_audio,
    find_logo,
    list_directories,
)


def main() -> None:
    root = Path("test_data/GTA IV")

    print("Directories:")

    for station in list_directories(root):
        print(f"\n{station.name}")

        print(" Audio:")
        for file in find_audio(station):
            print(f"   {file.name}")

        print(" Logo:")
        for file in find_logo(station):
            print(f"   {file.name}")

if __name__ == "__main__":
    main()
