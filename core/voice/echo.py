from __future__ import annotations

import difflib
import re
import time
from collections.abc import Callable
from typing import Any


class EchoDetector:
    """Detects assistant speech looped back through the microphone.

    Improved with:
    - N-gram fingerprinting for partial-match echo detection
    - Short-term and long-term utterance history
    - Time-weighted scoring (recent echoes weigh more)
    """
    def __init__(
        self,
        similarity_threshold: float = 0.55,
        ngram_threshold: float = 0.5,
        short_term_ttl: float = 5.0,
        long_term_ttl: float = 30.0,
        ngram_size: int = 3,
    ):
        self.similarity_threshold = similarity_threshold
        self.ngram_threshold = ngram_threshold
        self.short_term_ttl = short_term_ttl
        self.long_term_ttl = long_term_ttl
        self.ngram_size = ngram_size
        self._recent: list[dict] = []
        self._long_term: list[dict] = []

    def record_utterance(self, text: str) -> None:
        cleaned = self._clean(text)
        if not cleaned or len(cleaned) < 2:
            return
        now = time.time()
        entry = {"text": cleaned, "time": now, "fingerprint": self._fingerprint(cleaned)}
        self._recent.append(entry)
        self._long_term.append(entry)
        if len(self._recent) > 10:
            self._recent.pop(0)
        if len(self._long_term) > 50:
            self._long_term.pop(0)

    def is_echo(self, heard_text: str) -> bool:
        cleaned = self._clean(heard_text)
        if not cleaned or len(cleaned) < 3:
            return False

        now = time.time()
        cleaned_fp = self._fingerprint(cleaned)

        all_entries = []
        for entry in self._recent:
            age = now - entry["time"]
            if age <= self.short_term_ttl:
                all_entries.append(entry)

        if not all_entries:
            for entry in self._long_term:
                age = now - entry["time"]
                if self.short_term_ttl < age <= self.long_term_ttl:
                    all_entries.append(entry)

        if not all_entries:
            return False

        for entry in all_entries:
            age = now - entry["time"]
            weight = max(0.3, 1.0 - (age / self.long_term_ttl))

            ratio = difflib.SequenceMatcher(None, cleaned, entry["text"]).ratio()
            if ratio * weight >= self.similarity_threshold:
                return True

            fp_overlap = self._ngram_overlap(cleaned_fp, entry["fingerprint"])
            if fp_overlap * weight >= self.ngram_threshold:
                return True

            words_heard = set(cleaned.split())
            words_prev = set(entry["text"].split())
            if words_heard and words_prev:
                overlap = len(words_heard & words_prev) / max(len(words_heard), len(words_prev))
                if overlap * weight >= self.similarity_threshold:
                    return True

            if len(cleaned) > 10 and len(entry["text"]) > 10:
                shorter = cleaned if len(cleaned) < len(entry["text"]) else entry["text"]
                longer = entry["text"] if len(cleaned) < len(entry["text"]) else cleaned
                if shorter in longer:
                    return True

        return False

    def _fingerprint(self, text: str) -> set[str]:
        words = text.split()
        ngrams: set[str] = set()
        for i in range(len(words) - self.ngram_size + 1):
            ngrams.add(" ".join(words[i:i + self.ngram_size]))
        return ngrams

    @staticmethod
    def _ngram_overlap(fp1: set[str], fp2: set[str]) -> float:
        if not fp1 or not fp2:
            return 0.0
        intersection = fp1 & fp2
        return len(intersection) / max(len(fp1), len(fp2))

    def clear(self) -> None:
        self._recent.clear()
        self._long_term.clear()

    @staticmethod
    def _clean(text: str) -> str:
        text = text.lower().strip()
        text = re.sub(r"[^\w\s]", "", text)
        text = re.sub(r"\s+", " ", text)
        return text.strip()
