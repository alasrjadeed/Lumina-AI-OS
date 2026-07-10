"""Multi-language support for voice control.

Maps languages (ISO 639-1) to:
- Edge-TTS voice names (best quality neural voices)
- gTTS language codes (fallback)
- STT language hints
- Wake-word translations
"""

from __future__ import annotations

from dataclasses import dataclass

LANGUAGE_NAMES = {
    "en": "English",
    "ar": "Arabic",
    "ur": "Urdu",
    "hi": "Hindi",
    "bn": "Bengali",
    "zh": "Chinese",
    "fil": "Filipino",
    "th": "Thai",
    "ja": "Japanese",
    "ko": "Korean",
    "fr": "French",
    "de": "German",
    "es": "Spanish",
    "pt": "Portuguese",
    "ru": "Russian",
    "tr": "Turkish",
    "vi": "Vietnamese",
    "id": "Indonesian",
    "ms": "Malay",
    "fa": "Persian",
    "sw": "Swahili",
    "nl": "Dutch",
    "it": "Italian",
    "pl": "Polish",
    "uk": "Ukrainian",
    "ro": "Romanian",
    "cs": "Czech",
    "el": "Greek",
    "hu": "Hungarian",
    "sv": "Swedish",
    "da": "Danish",
    "fi": "Finnish",
    "he": "Hebrew",
    "ta": "Tamil",
    "te": "Telugu",
    "mr": "Marathi",
    "gu": "Gujarati",
    "kn": "Kannada",
    "ml": "Malayalam",
    "pa": "Punjabi",
    "ne": "Nepali",
    "si": "Sinhala",
    "km": "Khmer",
    "my": "Burmese",
    "lo": "Lao",
    "am": "Amharic",
}


@dataclass
class LanguageVoice:
    code: str
    name: str
    edge_voice: str
    gtts_code: str = ""
    whisper_code: str = ""
    native_name: str = ""
    wake_word: str = ""


LANGUAGE_VOICES: dict[str, LanguageVoice] = {
    "en": LanguageVoice(
        "en",
        "English",
        "en-US-JennyNeural",
        gtts_code="en",
        whisper_code="en",
        native_name="English",
        wake_word="lumina",
    ),
    "ar": LanguageVoice(
        "ar",
        "Arabic",
        "ar-SA-ZariyahNeural",
        gtts_code="ar",
        whisper_code="ar",
        native_name="العربية",
        wake_word="لمينا",
    ),
    "ur": LanguageVoice(
        "ur",
        "Urdu",
        "ur-PK-AsadNeural",
        gtts_code="ur",
        whisper_code="ur",
        native_name="اردو",
        wake_word="لمینا",
    ),
    "hi": LanguageVoice(
        "hi",
        "Hindi",
        "hi-IN-SwaraNeural",
        gtts_code="hi",
        whisper_code="hi",
        native_name="हिन्दी",
        wake_word="लुमिना",
    ),
    "bn": LanguageVoice(
        "bn",
        "Bengali",
        "bn-BD-NabanitaNeural",
        gtts_code="bn",
        whisper_code="bn",
        native_name="বাংলা",
        wake_word="লুমিনা",
    ),
    "zh": LanguageVoice(
        "zh",
        "Chinese",
        "zh-CN-XiaoxiaoNeural",
        gtts_code="zh-CN",
        whisper_code="zh",
        native_name="中文",
        wake_word="卢米娜",
    ),
    "fil": LanguageVoice(
        "fil",
        "Filipino",
        "fil-PH-AngeloNeural",
        gtts_code="tl",
        whisper_code="tl",
        native_name="Filipino",
        wake_word="lumina",
    ),
    "th": LanguageVoice(
        "th",
        "Thai",
        "th-TH-PremwadeeNeural",
        gtts_code="th",
        whisper_code="th",
        native_name="ไทย",
        wake_word="ลูมินา",
    ),
    "ja": LanguageVoice(
        "ja",
        "Japanese",
        "ja-JP-NanamiNeural",
        gtts_code="ja",
        whisper_code="ja",
        native_name="日本語",
        wake_word="ルミナ",
    ),
    "ko": LanguageVoice(
        "ko",
        "Korean",
        "ko-KR-SunHiNeural",
        gtts_code="ko",
        whisper_code="ko",
        native_name="한국어",
        wake_word="루미나",
    ),
    "fr": LanguageVoice(
        "fr",
        "French",
        "fr-FR-DeniseNeural",
        gtts_code="fr",
        whisper_code="fr",
        native_name="Français",
        wake_word="lumina",
    ),
    "de": LanguageVoice(
        "de",
        "German",
        "de-DE-KatjaNeural",
        gtts_code="de",
        whisper_code="de",
        native_name="Deutsch",
        wake_word="lumina",
    ),
    "es": LanguageVoice(
        "es",
        "Spanish",
        "es-ES-ElviraNeural",
        gtts_code="es",
        whisper_code="es",
        native_name="Español",
        wake_word="lumina",
    ),
    "pt": LanguageVoice(
        "pt",
        "Portuguese",
        "pt-BR-FranciscaNeural",
        gtts_code="pt",
        whisper_code="pt",
        native_name="Português",
        wake_word="lumina",
    ),
    "ru": LanguageVoice(
        "ru",
        "Russian",
        "ru-RU-SvetlanaNeural",
        gtts_code="ru",
        whisper_code="ru",
        native_name="Русский",
        wake_word="люмина",
    ),
    "tr": LanguageVoice(
        "tr",
        "Turkish",
        "tr-TR-EmelNeural",
        gtts_code="tr",
        whisper_code="tr",
        native_name="Türkçe",
        wake_word="lumina",
    ),
    "vi": LanguageVoice(
        "vi",
        "Vietnamese",
        "vi-VN-HoaiMyNeural",
        gtts_code="vi",
        whisper_code="vi",
        native_name="Tiếng Việt",
        wake_word="lumina",
    ),
    "id": LanguageVoice(
        "id",
        "Indonesian",
        "id-ID-GadisNeural",
        gtts_code="id",
        whisper_code="id",
        native_name="Bahasa Indonesia",
        wake_word="lumina",
    ),
    "ms": LanguageVoice(
        "ms",
        "Malay",
        "ms-MY-YasminNeural",
        gtts_code="ms",
        whisper_code="ms",
        native_name="Bahasa Melayu",
        wake_word="lumina",
    ),
    "fa": LanguageVoice(
        "fa",
        "Persian",
        "fa-IR-DilaraNeural",
        gtts_code="fa",
        whisper_code="fa",
        native_name="فارسی",
        wake_word="لومینا",
    ),
    "sw": LanguageVoice(
        "sw",
        "Swahili",
        "sw-TZ-RehemaNeural",
        gtts_code="sw",
        whisper_code="sw",
        native_name="Kiswahili",
        wake_word="lumina",
    ),
    "nl": LanguageVoice(
        "nl",
        "Dutch",
        "nl-NL-ColetteNeural",
        gtts_code="nl",
        whisper_code="nl",
        native_name="Nederlands",
        wake_word="lumina",
    ),
    "it": LanguageVoice(
        "it",
        "Italian",
        "it-IT-ElsaNeural",
        gtts_code="it",
        whisper_code="it",
        native_name="Italiano",
        wake_word="lumina",
    ),
    "pl": LanguageVoice(
        "pl",
        "Polish",
        "pl-PL-AgnieszkaNeural",
        gtts_code="pl",
        whisper_code="pl",
        native_name="Polski",
        wake_word="lumina",
    ),
    "uk": LanguageVoice(
        "uk",
        "Ukrainian",
        "uk-UA-PolinaNeural",
        gtts_code="uk",
        whisper_code="uk",
        native_name="Українська",
        wake_word="люміна",
    ),
    "ro": LanguageVoice(
        "ro",
        "Romanian",
        "ro-RO-AlinaNeural",
        gtts_code="ro",
        whisper_code="ro",
        native_name="Română",
        wake_word="lumina",
    ),
    "cs": LanguageVoice(
        "cs",
        "Czech",
        "cs-CZ-VlastaNeural",
        gtts_code="cs",
        whisper_code="cs",
        native_name="Čeština",
        wake_word="lumina",
    ),
    "el": LanguageVoice(
        "el",
        "Greek",
        "el-GR-AthinaNeural",
        gtts_code="el",
        whisper_code="el",
        native_name="Ελληνικά",
        wake_word="λούμινα",
    ),
    "hu": LanguageVoice(
        "hu",
        "Hungarian",
        "hu-HU-NoemiNeural",
        gtts_code="hu",
        whisper_code="hu",
        native_name="Magyar",
        wake_word="lumina",
    ),
    "sv": LanguageVoice(
        "sv",
        "Swedish",
        "sv-SE-SofieNeural",
        gtts_code="sv",
        whisper_code="sv",
        native_name="Svenska",
        wake_word="lumina",
    ),
    "da": LanguageVoice(
        "da",
        "Danish",
        "da-DK-ChristelNeural",
        gtts_code="da",
        whisper_code="da",
        native_name="Dansk",
        wake_word="lumina",
    ),
    "fi": LanguageVoice(
        "fi",
        "Finnish",
        "fi-FI-SelmaNeural",
        gtts_code="fi",
        whisper_code="fi",
        native_name="Suomi",
        wake_word="lumina",
    ),
    "he": LanguageVoice(
        "he",
        "Hebrew",
        "he-IL-HilaNeural",
        gtts_code="he",
        whisper_code="he",
        native_name="עברית",
        wake_word="לומינה",
    ),
    "ta": LanguageVoice(
        "ta",
        "Tamil",
        "ta-IN-PallaviNeural",
        gtts_code="ta",
        whisper_code="ta",
        native_name="தமிழ்",
        wake_word="லுமினா",
    ),
    "te": LanguageVoice(
        "te",
        "Telugu",
        "te-IN-ShrutiNeural",
        gtts_code="te",
        whisper_code="te",
        native_name="తెలుగు",
        wake_word="లుమినా",
    ),
    "mr": LanguageVoice(
        "mr",
        "Marathi",
        "mr-IN-AarohiNeural",
        gtts_code="mr",
        whisper_code="mr",
        native_name="मराठी",
        wake_word="लुमिना",
    ),
    "gu": LanguageVoice(
        "gu",
        "Gujarati",
        "gu-IN-DhwaniNeural",
        gtts_code="gu",
        whisper_code="gu",
        native_name="ગુજરાતી",
        wake_word="લુમિના",
    ),
    "kn": LanguageVoice(
        "kn",
        "Kannada",
        "kn-IN-SapnaNeural",
        gtts_code="kn",
        whisper_code="kn",
        native_name="ಕನ್ನಡ",
        wake_word="ಲುಮಿನಾ",
    ),
    "ml": LanguageVoice(
        "ml",
        "Malayalam",
        "ml-IN-SobhanaNeural",
        gtts_code="ml",
        whisper_code="ml",
        native_name="മലയാളം",
        wake_word="ലുമിന",
    ),
    "pa": LanguageVoice(
        "pa",
        "Punjabi",
        "pa-IN-OjasNeural",
        gtts_code="pa",
        whisper_code="pa",
        native_name="ਪੰਜਾਬੀ",
        wake_word="ਲੁਮਿਨਾ",
    ),
    "ne": LanguageVoice(
        "ne",
        "Nepali",
        "ne-NP-HemkalaNeural",
        gtts_code="ne",
        whisper_code="ne",
        native_name="नेपाली",
        wake_word="लुमिना",
    ),
    "si": LanguageVoice(
        "si",
        "Sinhala",
        "si-LK-ThiliniNeural",
        gtts_code="si",
        whisper_code="si",
        native_name="සිංහල",
        wake_word="ලුමිනා",
    ),
    "km": LanguageVoice(
        "km",
        "Khmer",
        "km-KH-SreymomNeural",
        gtts_code="km",
        whisper_code="km",
        native_name="ភាសាខ្មែរ",
        wake_word="លូមីណា",
    ),
    "my": LanguageVoice(
        "my",
        "Burmese",
        "my-MM-NilarNeural",
        gtts_code="my",
        whisper_code="my",
        native_name="မြန်မာဘာသာ",
        wake_word="လူမီနာ",
    ),
    "am": LanguageVoice(
        "am",
        "Amharic",
        "am-ET-MekdesNeural",
        gtts_code="am",
        whisper_code="am",
        native_name="አማርኛ",
        wake_word="ሉሚና",
    ),
}


def detect_language(text: str) -> str:
    """Heuristic language detection based on Unicode script ranges.
    Returns ISO 639-1 code. Defaults to 'en'.
    """
    if not text:
        return "en"
    for ch in text:
        cp = ord(ch)
        if 0x0600 <= cp <= 0x06FF:
            return "ar"
        if 0x0750 <= cp <= 0x077F:
            return "ar"
        if 0x08A0 <= cp <= 0x08FF:
            return "ar"
        if 0xFB50 <= cp <= 0xFDFF or 0xFE70 <= cp <= 0xFEFF:
            return "ar"
        if 0x0900 <= cp <= 0x097F:
            return "hi"
        if 0x0980 <= cp <= 0x09FF:
            return "bn"
        if 0x0A80 <= cp <= 0x0AFF:
            return "gu"
        if 0x0B00 <= cp <= 0x0B7F:
            return "or"
        if 0x0B80 <= cp <= 0x0BFF:
            return "ta"
        if 0x0C00 <= cp <= 0x0C7F:
            return "te"
        if 0x0C80 <= cp <= 0x0CFF:
            return "kn"
        if 0x0D00 <= cp <= 0x0D7F:
            return "ml"
        if 0x0D80 <= cp <= 0x0DFF:
            return "si"
        if 0x0E00 <= cp <= 0x0E7F:
            return "th"
        if 0x0F00 <= cp <= 0x0FFF:
            return "dz"
        if 0x1000 <= cp <= 0x109F:
            return "my"
        if 0x1780 <= cp <= 0x17FF or 0x19E0 <= cp <= 0x19FF:
            return "km"
        if 0x1A00 <= cp <= 0x1A1F:
            return "bug"
        if 0x2E80 <= cp <= 0x2EFF or 0x3000 <= cp <= 0x303F:
            return "zh"
        if 0x4E00 <= cp <= 0x9FFF or 0x3400 <= cp <= 0x4DBF:
            return "zh"
        if 0xF900 <= cp <= 0xFAFF:
            return "zh"
        if 0xAC00 <= cp <= 0xD7AF:
            return "ko"
        if 0x3040 <= cp <= 0x309F or 0x30A0 <= cp <= 0x30FF:
            return "ja"
        if 0x0400 <= cp <= 0x04FF or 0x0500 <= cp <= 0x052F:
            return "ru"
        if 0x0590 <= cp <= 0x05FF or 0xFB00 <= cp <= 0xFB4F:
            return "he"
        if 0x0600 <= cp <= 0x06FF:
            return "fa"
        if 0x0600 <= cp <= 0x06FF:
            return "ur"
        if 0x10D0 <= cp <= 0x10FF:
            return "ka"
        if 0x1C00 <= cp <= 0x1C4F:
            return "lep"
    return "en"


def get_voice_for_language(lang_code: str, gender: str = "female") -> LanguageVoice:
    """Get the best Edge-TTS voice for a language code."""
    if lang_code in LANGUAGE_VOICES:
        return LANGUAGE_VOICES[lang_code]
    if lang_code[:2] in LANGUAGE_VOICES:
        return LANGUAGE_VOICES[lang_code[:2]]
    return LANGUAGE_VOICES["en"]


def get_wake_word(lang_code: str, default: str = "lumina") -> str:
    """Get the wake word translation for a language."""
    lv = get_voice_for_language(lang_code)
    return lv.wake_word or default


def list_supported_languages() -> list[dict]:
    return [
        {"code": k, "name": v.name, "native": v.native_name, "voice": v.edge_voice}
        for k, v in sorted(LANGUAGE_VOICES.items())
    ]
