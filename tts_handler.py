# tts_handler.py
# Handles all Text-to-Speech operations using gTTS and playsound.

from gtts import gTTS
from playsound import playsound
import os
import threading
import hashlib

# Import the settings from the main app to check the cache setting
from powerlang import app_settings

CACHE_DIR = "tts_cache"
if not os.path.exists(CACHE_DIR):
    os.makedirs(CACHE_DIR)

sound_lock = threading.Lock()

def speak(text, lang_code, keep_cache):
    """
    Generates and plays audio for the given text and language.
    Deletes the file after playing if the cache setting is disabled.
    """
    if not text or not lang_code:
        print("TTS Error: No text to speak.")
        return
        
    # Prevent multiple sounds from playing at once.
    if sound_lock.locked():
        print("Audio is already playing. New request ignored.")
        return

    filepath = None
    try:
        with sound_lock:
            hashed_name = hashlib.md5(text.encode('utf-8')).hexdigest()
            filename = f"{lang_code}_{hashed_name}.mp3"
            filepath = os.path.join(CACHE_DIR, filename)

            if not os.path.exists(filepath):
                print(f"Generating new TTS file for '{text}' ({lang_code})...")
                tts = gTTS(text=text, lang=lang_code, slow=False)
                tts.save(filepath)
            
            print(f"Playing TTS: {filepath}")
            playsound(filepath, block=True)
            
    except Exception as e:
        print(f"An error occurred in the TTS handler: {e}")
    
    finally:
        if filepath and os.path.exists(filepath) and not keep_cache:
            try:
                os.remove(filepath)
                print(f"Deleted cached file: {filepath}")
            except Exception as e:
                print(f"Error deleting cached file {filepath}: {e}")