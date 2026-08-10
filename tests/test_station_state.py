from radio.model.station_state import StationState

def main() -> None:
    assert StationState.OFF.value == "off"
    assert StationState.ON_AIR.value == "on_air"
    assert StationState.SWITCHING.value == "switching"

    assert StationState.OFF != StationState.ON_AIR
    assert StationState.ON_AIR != StationState.SWITCHING
    assert StationState.SWITCHING != StationState.OFF

    print("Station state test passed.")


if __name__ == "__main__":
    main()
