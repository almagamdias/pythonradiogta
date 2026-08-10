from __future__ import annotations

import time

from radio.util.timer import SwitchTimer


def main() -> None:
    fired_at: list[float] = []

    def callback() -> None:
        fired_at.append(time.monotonic())

    timer = SwitchTimer(
        delay=1.0,
        callback=callback,
    )

    timer.start()

    # Должен быть ещё активен.
    time.sleep(0.3)
    assert not fired_at

    # Сбрасываем таймер.
    reset_at = time.monotonic()
    timer.start()

    # Через 0.5 секунды после reset callback
    # ещё не должен сработать.
    time.sleep(0.5)
    assert not fired_at

    # Даём таймеру гарантированно завершиться.
    time.sleep(0.7)

    assert len(fired_at) == 1

    elapsed = fired_at[0] - reset_at

    print(f"Callback fired after reset: {elapsed:.2f} seconds")
    print("Timer reset test passed.")


if __name__ == "__main__":
    main()
