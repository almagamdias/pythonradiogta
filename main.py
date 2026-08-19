from pathlib import Path

from radio.engine import RadioEngine
from radio.library.gen1 import Gen1Loader

from gui.app import RadioApp


TEST_ROOT = Path("test_data/GTA IV")


def main() -> None:
    loader = Gen1Loader()
    library = loader.load(TEST_ROOT)

    engine = RadioEngine(library)

    engine.play()

    app = RadioApp(engine)
    app.run()


if __name__ == "__main__":
    main()
