"""
Simple script to play a WAV audio file.

Works from any directory by locating the WAV file relative to this script.
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
        filename: Absolute path to the WAV file to play
    """
    # Normalize path for cross-platform compatibility
    filename = os.path.normpath(filename)

    if not os.path.exists(filename):
        print(f"Error: File not found.")
        print(f"  Looking for: {filename}")
        print(f"  Current directory: {os.getcwd()}")
        return False

    try:
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
                    return False
        return True
    except Exception as e:
        print(f"Error playing audio: {e}")
        return False


if __name__ == "__main__":
    # Get the directory where this script is located
    script_dir = os.path.dirname(os.path.abspath(__file__))
    wav_file = os.path.join(script_dir, "positive-notification.wav")

    if play_wav_file(wav_file):
        print("Playing: positive-notification.wav")
