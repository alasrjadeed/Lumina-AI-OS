from __future__ import annotations

import re

from core.memory.semantic import Fact, SemanticMemory


class ConsolidationEngine:
    """Transfers short-term experiences into long-term semantic facts."""

    def __init__(self, semantic: SemanticMemory | None = None):
        self.semantic = semantic or SemanticMemory()

    def consolidate_conversation(self, messages: list[dict[str, str]]) -> list[Fact]:
        extracted: list[Fact] = []
        for msg in messages:
            content = msg.get("content", "")
            role = msg.get("role", "")
            if not content or role == "system":
                continue
            facts = self._extract_facts(content, source=f"conversation:{role}")
            for f in facts:
                self.semantic.learn(f)
                extracted.append(f)
        return extracted

    def consolidate_episode(self, task: str, result: str, agent: str = "") -> list[Fact]:
        facts = self._extract_facts(result, source=f"episode:{agent}:{task[:50]}")
        for f in facts:
            self.semantic.learn(f)
        return facts

    def _extract_facts(self, text: str, source: str = "") -> list[Fact]:
        facts: list[Fact] = []

        sentences = [s.strip() for s in text.replace("\n", " ").split(".") if s.strip()]

        patterns = [
            r"(?i)(\w+(?:\s+\w+){0,3})\s+is\s+(a|an|the)?\s*(.+)",
            r"(?i)(\w+(?:\s+\w+){0,3})\s+are\s+(.+)",
            r"(?i)(\w+(?:\s+\w+){0,3})\s+has\s+(.+)",
            r"(?i)(\w+(?:\s+\w+){0,3})\s+uses\s+(.+)",
            r"(?i)(\w+(?:\s+\w+){0,3})\s+provides\s+(.+)",
            r"(?i)(\w+(?:\s+\w+){0,3})\s+contains\s+(.+)",
            r"(?i)(\w+(?:\s+\w+){0,3})\s+means\s+(.+)",
            r"(?i)(\w+(?:\s+\w+){0,3})\s+requires\s+(.+)",
        ]

        for sentence in sentences:
            if len(sentence) < 10:
                continue
            for pattern in patterns:
                m = re.search(pattern, sentence)
                if m:
                    groups = m.groups()
                    if len(groups) == 3:
                        subj, _, obj = groups
                        pred = "is"
                    else:
                        subj, obj = groups
                        # determine predicate from pattern keywords
                        kw = r"\s+(is|are|has|uses|provides|contains|means|requires)\s+"
                        pred_match = re.search(kw, sentence, re.IGNORECASE)
                        pred = pred_match.group(1).lower() if pred_match else "is"
                    subj = subj.strip()
                    obj = obj.strip().rstrip(".,!?;:")
                    if len(subj) > 3 and len(obj) > 3 and len(subj) < 80 and len(obj) < 200:
                        facts.append(Fact(subject=subj, predicate=pred, obj=obj, source=source))
                    break

        return facts
