from pathlib import Path
import time

from radio.audio.player import AudioPlayer


path = Path(r"test_data\GTA IV\02_LIBERTYROCK\EVILWOMAN.ogg")

player = AudioPlayer(path)

print("Starting...")
player.play()

time.sleep(10)

print("Stopping...")
player.stop()

print("Done.")
