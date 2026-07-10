from __future__ import annotations

import json
import os

SETTINGS_PATH = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "jarvis_settings.json"
)

DEFAULT_SETTINGS = {
    "wake_word": "jarvis",
    "language": "en",
    "stt_provider": "faster_whisper",
    "tts_provider": "piper",
    "llm_provider": "ollama",
    "ollama_model": "qwen2.5-coder:0.5b",
    "ollama_base_url": "http://localhost:11434",
    "push_to_talk_key": "<ctrl>+<shift>+j",
    "mic_device": "",
    "speaker_device": "",
    "continuous_listening": True,
    "wake_word_enabled": True,
    "silero_vad": True,
    "offline_mode": True,
    "cloud_fallback": True,
    "proactive_notifications": True,
    "theme": "dark",
    "overlay_enabled": True,
    "tts_speed": 1.0,
    "tts_voice": "amy",
}


class JarvisSettings:
    def __init__(self, path: str = SETTINGS_PATH):
        self.path = path
        self._data: dict = {}
        self.load()

    def load(self) -> dict:
        if os.path.exists(self.path):
            try:
                with open(self.path) as f:
                    self._data = json.load(f)
            except (json.JSONDecodeError, OSError):
                self._data = {}
        else:
            self._data = {}
        for key, val in DEFAULT_SETTINGS.items():
            self._data.setdefault(key, val)
        self.save()
        return self._data

    def save(self) -> None:
        try:
            with open(self.path, "w") as f:
                json.dump(self._data, f, indent=2)
        except OSError:
            pass

    def get(self, key: str, default=None):
        return self._data.get(key, default)

    def set(self, key: str, value) -> None:
        self._data[key] = value
        self.save()

    def __getitem__(self, key: str):
        return self._data[key]

    def __setitem__(self, key: str, value):
        self._data[key] = value

    @property
    def all(self) -> dict:
        return dict(self._data)
