"""Acumen Voice - Speech-to-text and text-to-speech for hands-free interaction."""

import io
import tempfile
import threading
from pathlib import Path
from acumen.core.logger import get_logger

logger = get_logger("acumen.tools.voice")

_whisper_model = None

def get_whisper():
    global _whisper_model
    if _whisper_model is None:
        import whisper
        logger.info("Loading Whisper tiny model...")
        _whisper_model = whisper.load_model("tiny")
        logger.info("Whisper model loaded")
    return _whisper_model

def transcribe_audio(audio_bytes, filename="audio.wav"):
    try:
        with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as f:
            f.write(audio_bytes)
            temp_path = f.name
        model = get_whisper()
        result = model.transcribe(temp_path, language="en")
        text = result["text"].strip()
        Path(temp_path).unlink(missing_ok=True)
        logger.info(f"Transcribed: {text[:50]}")
        return text
    except Exception as e:
        logger.warning(f"Transcription failed: {e}")
        return ""

def transcribe_file(file_path):
    try:
        model = get_whisper()
        result = model.transcribe(str(file_path), language="en")
        text = result["text"].strip()
        logger.info(f"Transcribed file: {text[:50]}")
        return text
    except Exception as e:
        logger.warning(f"Transcription failed: {e}")
        return ""

def speak(text):
    try:
        import pyttsx3
        engine = pyttsx3.init()
        engine.setProperty('rate', 175)
        engine.setProperty('volume', 0.9)
        voices = engine.getProperty('voices')
        if len(voices) > 1:
            engine.setProperty('voice', voices[1].id)
        engine.say(text[:500])
        engine.runAndWait()
        engine.stop()
        logger.info(f"Spoke: {text[:50]}")
    except Exception as e:
        logger.warning(f"TTS failed: {e}")

def speak_async(text):
    t = threading.Thread(target=speak, args=(text,), daemon=True)
    t.start()

def record_audio(duration=5, samplerate=16000):
    try:
        import sounddevice as sd
        import soundfile as sf
        import numpy as np
        logger.info(f"Recording {duration}s of audio...")
        audio = sd.rec(int(duration * samplerate), samplerate=samplerate, channels=1, dtype='float32')
        sd.wait()
        with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as f:
            sf.write(f.name, audio, samplerate)
            temp_path = f.name
        with open(temp_path, 'rb') as f:
            audio_bytes = f.read()
        Path(temp_path).unlink(missing_ok=True)
        logger.info("Recording complete")
        return audio_bytes
    except Exception as e:
        logger.warning(f"Recording failed: {e}")
        return None