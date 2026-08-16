from pathlib import Path

from gui.app import RadioApp
from radio.engine import RadioEngine
from radio.library.gen1 import Gen1Loader


def main() -> None:
    library = Gen1Loader().load(
        Path("test_data/GTA IV")
    )

    engine = RadioEngine(library)

    app = RadioApp(engine)
    app.run()


if __name__ == "__main__":
    main()
