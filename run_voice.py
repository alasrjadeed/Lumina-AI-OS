"""Standalone voice control launcher with multi-language support."""
import asyncio
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault("OPENAI_API_KEY", "")

from core.voice.controller import VoiceController
from core.voice.recorder import AudioRecorder
from core.voice.stt import STTEngine
from core.voice.tts import TTSEngine
from core.voice.languages import list_supported_languages

async def main():
    recorder = AudioRecorder()
    if not recorder.is_available():
        print("No microphone found (arecord/parec/sox required). Voice control unavailable.")
        return

    print("Calibrating microphone for ambient noise...")
    cal = await recorder.calibrate(duration=2.0)
    print(f"  Ambient RMS: {cal['ambient_rms']:.1f}, Threshold: {cal['threshold']}")

    stt = STTEngine()
    tts = TTSEngine()

    langs = list_supported_languages()
    print(f"\nLumina Voice Control — {len(langs)} languages supported")
    print("Say the wake word in your language + your command.")
    print("Examples:")
    print("  English: \"Lumina, what's the weather?\"")
    print("  Arabic:  \"لمينا، ما هو الطقس؟\"")
    print("  Hindi:   \"लुमिना, मौसम कैसा है?\"")
    print("  Chinese: \"卢米娜，天气怎么样？\"")
    print("  Bengali: \"লুমিনা, আবহাওয়া কেমন?\"")
    print("  Urdu:    \"لمینا، موسم کیسا ہے؟\"")
    print("  Filipino: \"Lumina, kamusta panahon?\"")
    print("  Thai:    \"ลูมินา, สภาพอากาศเป็นอย่างไร?\"")
    print("\nSay 'stop' or 'never mind' to interrupt.\n")

    controller = VoiceController(
        recorder=recorder,
        stt_engine=stt,
        tts_engine=tts,
    )

    await controller.start_continuous(wake_word_mode=True)

if __name__ == "__main__":
    asyncio.run(main())
