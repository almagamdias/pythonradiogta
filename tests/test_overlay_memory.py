from __future__ import annotations

import gc
import tracemalloc
from pathlib import Path

from radio.audio.player import AudioPlayer


OVERLAY_PATH = Path("assets/sounds/switch_noise.ogg")

ITERATIONS = 10_000
REPORT_EVERY = 1_000


def main() -> None:
    player = AudioPlayer(OVERLAY_PATH)

    gc.collect()
    tracemalloc.start()

    snapshot_start = tracemalloc.take_snapshot()

    for i in range(1, ITERATIONS + 1):
        player.play_overlay(
            OVERLAY_PATH,
            loop=True,
        )

        player.stop_overlay()

        if i % REPORT_EVERY == 0:
            gc.collect()

            current, peak = tracemalloc.get_traced_memory()

            print(
                f"{i:>6} iterations | "
                f"current={current / 1024:>8.1f} KiB | "
                f"peak={peak / 1024:>8.1f} KiB"
            )

    gc.collect()

    snapshot_end = tracemalloc.take_snapshot()

    print()
    print("Top memory differences:")

    for stat in snapshot_end.compare_to(
        snapshot_start,
        "lineno",
    )[:10]:
        print(stat)

    current, peak = tracemalloc.get_traced_memory()

    print()
    print(
        f"Final current: {current / 1024:.1f} KiB"
    )
    print(
        f"Final peak:    {peak / 1024:.1f} KiB"
    )

    tracemalloc.stop()


if __name__ == "__main__":
    main()
