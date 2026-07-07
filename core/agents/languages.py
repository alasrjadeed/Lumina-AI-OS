"""Multi-Language Support — auto-detect, translate, and respond in any language."""

from __future__ import annotations

LANGUAGE_NAMES: dict[str, str] = {
    "en": "English", "ar": "Arabic (العربية)", "hi": "Hindi (हिन्दी)",
    "ur": "Urdu (اردو)", "bn": "Bengali (বাংলা)", "ml": "Malayalam (മലയാളം)",
    "fr": "French (Français)", "es": "Spanish (Español)", "zh": "Chinese (中文)",
    "ja": "Japanese (日本語)", "ko": "Korean (한국어)", "de": "German (Deutsch)",
    "pt": "Portuguese (Português)", "ru": "Russian (Русский)", "it": "Italian (Italiano)",
    "nl": "Dutch (Nederlands)", "tr": "Turkish (Türkçe)", "fa": "Persian (فارسی)",
    "sw": "Swahili", "th": "Thai (ไทย)", "vi": "Vietnamese (Tiếng Việt)",
    "id": "Indonesian (Bahasa)", "ms": "Malay (Bahasa Melayu)", "ta": "Tamil (தமிழ்)",
    "te": "Telugu (తెలుగు)", "mr": "Marathi (मराठी)", "gu": "Gujarati (ગુજરાતી)",
    "kn": "Kannada (ಕನ್ನಡ)", "pa": "Punjabi (ਪੰਜਾਬੀ)",
}

DETECTION_KEYWORDS: dict[str, list[str]] = {
    "ar": ["ال", "في", "من", "على", "هذا", "كان", "مع", "ما"],
    "hi": ["है", "का", "की", "को", "में", "से", "पर", "और"],
    "ur": ["ہے", "کا", "کی", "کو", "میں", "سے", "پر", "اور"],
    "bn": ["হয়", "এর", "কি", "থেকে", "এ", "একটি", "জন্য"],
    "ml": ["ആണ്", "എന്ന", "അത്", "ഇത്", "ഒരു", "എല്ലാ"],
    "fr": ["le", "la", "les", "des", "est", "pas", "dans", "que"],
    "es": ["que", "los", "las", "del", "una", "por", "con", "para"],
    "zh": ["的", "是", "不", "我", "了", "在", "人", "有"],
    "ja": ["は", "の", "に", "を", "が", "で", "た", "し"],
    "ko": ["이", "가", "은", "는", "을", "를", "에", "의"],
    "de": ["der", "die", "das", "ist", "und", "von", "mit", "sich"],
    "pt": ["que", "não", "com", "uma", "dos", "das", "para", "como"],
    "ru": ["это", "что", "как", "для", "или", "если", "уже", "когда"],
    "it": ["che", "non", "una", "sono", "con", "per", "della", "come"],
}


class LanguageEngine:
    """Detects input language and provides translation guidance to the CEO."""

    def __init__(self, working_language: str = "en"):
        self.working_language = working_language

    def detect(self, text: str) -> str:
        if not text.strip():
            return "en"

        text_sample = text[:200].lower()

        lang_scores: dict[str, int] = {}
        for lang_code, keywords in DETECTION_KEYWORDS.items():
            score = sum(1 for kw in keywords if kw in text_sample)
            if score > 0:
                lang_scores[lang_code] = score

        if not lang_scores:
            has_latin = any(c.isascii() and c.isalpha() for c in text_sample)
            if not has_latin and any(ord(c) > 127 for c in text_sample):
                char_ranges = {
                    "\u0600": "ar", "\u0900": "hi", "\u0980": "bn",
                    "\u0d00": "ml", "\u4e00": "zh", "\u3040": "ja",
                    "\uac00": "ko", "\u0c00": "te", "\u0a00": "pa",
                    "\u0b00": "ta", "\u0a80": "gu", "\u0c80": "kn",
                }
                for text_char in text_sample:
                    for range_start, code in char_ranges.items():
                        if range_start <= text_char <= chr(ord(range_start) + 127):
                            return code
                return "en"
            return "en"

        return max(lang_scores, key=lang_scores.get)

    def get_name(self, lang_code: str) -> str:
        return LANGUAGE_NAMES.get(lang_code, f"Unknown ({lang_code})")

    def build_multilingual_prompt(self, user_text: str) -> str:
        detected = self.detect(user_text)
        lang_name = self.get_name(detected)

        if detected == self.working_language:
            return ""

        working_lang_name = self.get_name(self.working_language)

        return (
            f"LANGUAGE CONTEXT: The user is speaking in {lang_name} (code: {detected}). "
            f"Your internal working language is {working_lang_name}. "
            f"ALWAYS respond to the user in {lang_name}. "
            f"Store your internal reasoning and memory in {working_lang_name}. "
            f"Think in {working_lang_name} but output in {lang_name}. "
            f"The original message will follow."
        )

    def list_languages(self) -> list[dict]:
        return [
            {"code": code, "name": name}
            for code, name in sorted(LANGUAGE_NAMES.items())
        ]

    def set_working_language(self, lang: str):
        if lang in LANGUAGE_NAMES:
            self.working_language = lang


language_engine = LanguageEngine()
