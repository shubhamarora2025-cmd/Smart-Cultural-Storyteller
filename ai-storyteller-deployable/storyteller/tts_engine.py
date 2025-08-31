from __future__ import annotations
import os
from typing import Optional
import uuid
import soundfile as sf
import numpy as np

try:
    import pyttsx3
except Exception:
    pyttsx3 = None

try:
    from openai import OpenAI
except Exception:
    OpenAI = None

class TTSEngine:
    def __init__(self, provider: str, openai_api_key: Optional[str]=None, openai_tts_voice: str="alloy"):
        self.provider = provider  # "local", "openai", or "mock"
        self.voice = openai_tts_voice
        self._client = None
        self._engine = None

        if self.provider == "openai" and openai_api_key and OpenAI:
            self._client = OpenAI(api_key=openai_api_key)
        elif self.provider == "local" and pyttsx3 is not None:
            self._engine = pyttsx3.init()

    def narrate(self, text: str, scene_no: int, out_dir: str) -> Optional[str]:
        os.makedirs(out_dir, exist_ok=True)
        if self.provider == "mock":
            # generate a silent placeholder wav to keep UX consistent
            path = os.path.join(out_dir, f"scene_{scene_no:02d}_mock.wav")
            sf.write(path, np.zeros(8000), 8000)
            return path

        if self.provider == "local" and self._engine is not None:
            path = os.path.join(out_dir, f"scene_{scene_no:02d}.wav")
            # pyttsx3 doesn't have simple file API everywhere; we record by speaking to file using driver
            try:
                # Fallback: speak and produce silence file (platform dependent).
                self._engine.save_to_file(text, path)
                self._engine.runAndWait()
                return path
            except Exception:
                # fallback to silent placeholder
                sf.write(path, np.zeros(8000), 8000)
                return path

        if self.provider == "openai" and self._client is not None:
            # Use OpenAI TTS (audio.speech)
            speech = self._client.audio.speech.create(
                model="gpt-4o-mini-tts",
                voice=self.voice,
                input=text,
                format="mp3",
            )
            path = os.path.join(out_dir, f"scene_{scene_no:02d}.mp3")
            with open(path, "wb") as f:
                f.write(speech.read())
            return path

        return None
