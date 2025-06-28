# tts_handler.py
# Handles all Text-to-Speech operations using gTTS.

from gtts import gTTS
from playsound import playsound
import os
import threading
import hashlib

# DO NOT import app_settings anymore. It will be passed as an argument.

CACHE_DIR = "tts_cache"
if not os.path.exists(CACHE_DIR):
    os.makedirs(CACHE_DIR)

sound_lock = threading.Lock()

def speak(text, lang_code, keep_cache):
    """
    Generates and plays audio for the given text and language.
    Deletes the file after playing if keep_cache is False.
    """
    if not text:
        print("TTS Error: No text to speak.")
        return

    filepath = None
    try:
        hashed_name = hashlib.md5(text.encode('utf-8')).hexdigest()
        filename = f"{lang_code}_{hashed_name}.mp3"
        filepath = os.path.join(CACHE_DIR, filename)

        if not os.path.exists(filepath):
            print(f"Generating new TTS file for '{text}' ({lang_code})...")
            tts = gTTS(text=text, lang=lang_code, slow=False)
            tts.save(filepath)
        
        with sound_lock:
            print(f"Playing TTS: {filepath}")
            playsound(filepath, block=True) 
            
    except Exception as e:
        print(f"An error occurred in the TTS handler: {e}")
    
    finally:
        # --- FIX: Use the keep_cache argument passed directly to the function ---
        if filepath and os.path.exists(filepath):
            if not keep_cache:
                try:
                    os.remove(filepath)
                    print(f"Deleted cached file: {filepath}")
                except Exception as e:
                    print(f"Error deleting cached file {filepath}: {e}")