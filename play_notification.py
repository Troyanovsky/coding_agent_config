"""
Simple script to play a WAV audio file.
"""

import sys
import os

try:
    import winsound
except ImportError:
    winsound = None


def play_wav_file(filename):
    """
    Play a WAV audio file.

    Args:
        filename: Path to the WAV file to play
    """
    if not os.path.exists(filename):
        print(f"Error: File '{filename}' not found.")
        return

    if winsound:
        # Windows: use built-in winsound module
        winsound.PlaySound(filename, winsound.SND_FILENAME)
    else:
        # Cross-platform alternative using simpleaudio or pygame
        try:
            import simpleaudio as sa
            wave_obj = sa.WaveObject.from_wave_file(filename)
            play_obj = wave_obj.play()
            play_obj.wait_done()
        except ImportError:
            try:
                import pygame
                pygame.mixer.init()
                pygame.mixer.music.load(filename)
                pygame.mixer.music.play()
                while pygame.mixer.music.get_busy():
                    pygame.time.Clock().tick(10)
            except ImportError:
                print("Error: No audio playback library available.")
                print("Install one of: pip install simpleaudio | pip install pygame")


if __name__ == "__main__":
    wav_file = "positive-notification.wav"
    play_wav_file(wav_file)
