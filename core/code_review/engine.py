"""Advanced Code Review Engine — static analysis, AI review, quality scoring, history."""

from __future__ import annotations

import asyncio
import json
import os
import re
import time
import uuid
from datetime import datetime
from typing import Any

from core.log import log
from core.provider import engine as ai_engine

HISTORY_PATH = os.path.expanduser("~/.lumina/code_reviews.json")

COMMON_ISSUES: dict[str, list[dict]] = {
    "python": [
        {"id": "sec-1", "severity": "critical", "title": "SQL Injection", "pattern": r"execute\(.*f['\"]|execute\(.*\+|raw_input"},
        {"id": "sec-2", "severity": "critical", "title": "Command Injection", "pattern": r"os\.system\(|subprocess\.call\(|subprocess\.Popen\(|eval\(|exec\("},
        {"id": "sec-3", "severity": "high", "title": "Hardcoded Secret", "pattern": r"(api_key|password|secret|token)\s*=\s*['\"][^'\"]+['\"]"},
        {"id": "perf-1", "severity": "warning", "title": "Inefficient Loop", "pattern": r"for\s+\w+\s+in\s+range\(len\("},
        {"id": "style-1", "severity": "info", "title": "Line Too Long", "pattern": r"^.{100,}$", "multiline": True},
        {"id": "style-2", "severity": "info", "title": "Missing Docstring", "pattern": r"^def |^class ", "check_missing": "docstring"},
        {"id": "bug-1", "severity": "high", "title": "Bare Except", "pattern": r"except\s*:"},
        {"id": "bug-2", "severity": "high", "title": "Mutable Default Arg", "pattern": r"def \w+\(.*=\s*\[|=\s*\{\}|=\s*set\(\)"},
        {"id": "bug-3", "severity": "medium", "title": "Potential Unused Variable", "pattern": r"^\s+\w+\s*=\s*.+$", "multiline": False},
    ],
    "javascript": [
        {"id": "sec-js-1", "severity": "critical", "title": "InnerHTML Assignment", "pattern": r"\.innerHTML\s*="},
        {"id": "sec-js-2", "severity": "critical", "title": "eval() Usage", "pattern": r"eval\(|new Function\("},
        {"id": "sec-js-3", "severity": "high", "title": "Hardcoded Secret", "pattern": r"(api_key|password|secret|token)\s*[:=]\s*['\"][^'\"]+['\"]"},
        {"id": "bug-js-1", "severity": "high", "title": "== Comparison", "pattern": r"==[^=]"},
        {"id": "bug-js-2", "severity": "medium", "title": "Console Left In", "pattern": r"console\.(log|warn|error)\("},
        {"id": "style-js-1", "severity": "info", "title": "var Usage", "pattern": r"\bvar\b"},
        {"id": "perf-js-1", "severity": "warning", "title": "Nested Loop", "pattern": r"for.*\{[^}]*for"},
    ],
    "typescript": [
        {"id": "sec-ts-1", "severity": "critical", "title": "Any Type Leak", "pattern": r":\s*any"},
        {"id": "sec-ts-2", "severity": "high", "title": "Non-null Assertion", "pattern": r"!\.\w+|as\s+\w+"},
        {"id": "bug-ts-1", "severity": "high", "title": "Missing Error Handling", "pattern": r"catch\s*\(.*\)\s*\{\s*\}"},
    ],
    "java": [
        {"id": "sec-java-1", "severity": "critical", "title": "SQL Injection", "pattern": r"Statement\.execute|jdbcTemplate\.execute"},
        {"id": "bug-java-1", "severity": "medium", "title": "Null Check Missing", "pattern": r"\.equals\(|\.length\(\)"},
    ],
    "go": [
        {"id": "sec-go-1", "severity": "critical", "title": "Error Ignored", "pattern": r"_\s*:=\s*\w+\(\)"},
        {"id": "style-go-1", "severity": "info", "title": "Naked Return", "pattern": r"return\n"},
    ],
    "rust": [
        {"id": "sec-rust-1", "severity": "high", "title": "unwrap() Usage", "pattern": r"\.unwrap\(\)"},
        {"id": "sec-rust-2", "severity": "medium", "title": "expect() Usage", "pattern": r"\.expect\("},
    ],
}

DIMENSIONS = [
    {"id": "security", "label": "Security", "icon": "Shield", "color": "red"},
    {"id": "bugs", "label": "Bugs & Errors", "icon": "Bug", "color": "orange"},
    {"id": "performance", "label": "Performance", "icon": "Zap", "color": "amber"},
    {"id": "style", "label": "Style & Format", "icon": "Palette", "color": "blue"},
    {"id": "best_practices", "label": "Best Practices", "icon": "CheckCircle", "color": "emerald"},
    {"id": "maintainability", "label": "Maintainability", "icon": "FileText", "color": "violet"},
]


class Issue:
    def __init__(self, id: str, severity: str, title: str, description: str = "",
                 line: int = 0, column: int = 0, snippet: str = "",
                 dimension: str = "", suggestion: str = ""):
        self.id = id
        self.severity = severity
        self.title = title
        self.description = description
        self.line = line
        self.column = column
        self.snippet = snippet
        self.dimension = dimension
        self.suggestion = suggestion

    def to_dict(self) -> dict:
        return {"id": self.id, "severity": self.severity, "title": self.title,
                "description": self.description, "line": self.line,
                "column": self.column, "snippet": self.snippet,
                "dimension": self.dimension, "suggestion": self.suggestion}


class ReviewResult:
    def __init__(self, review_id: str, language: str, code: str, score: int = 0,
                 issues: list[Issue] | None = None, summary: str = "",
                 ai_feedback: str = "", dimensions: dict | None = None,
                 stats: dict | None = None):
        self.review_id = review_id
        self.language = language
        self.code = code
        self.score = score
        self.issues = issues or []
        self.summary = summary
        self.ai_feedback = ai_feedback
        self.dimensions = dimensions or {}
        self.stats = stats or {}
        self.created_at = datetime.now().isoformat()

    def to_dict(self) -> dict:
        return {"review_id": self.review_id, "language": self.language,
                "code_preview": self.code[:500], "code_length": len(self.code),
                "score": self.score, "issues": [i.to_dict() for i in self.issues],
                "summary": self.summary, "ai_feedback": self.ai_feedback,
                "dimensions": self.dimensions, "stats": self.stats,
                "created_at": self.created_at}


LANG_ALIASES = {
    "py": "python", "js": "javascript", "ts": "typescript",
    "golang": "go", "rs": "rust", "kt": "kotlin",
    "cpp": "cpp", "cxx": "cpp", "cs": "csharp", "rb": "ruby",
    "pl": "perl", "sh": "bash", "yml": "yaml",
}


class CodeReviewEngine:
    def __init__(self):
        self._history: list[ReviewResult] = []
        self._load()

    def _load(self):
        if os.path.exists(HISTORY_PATH):
            try:
                with open(HISTORY_PATH) as f:
                    data = json.load(f)
                for d in data[-100:]:
                    r = ReviewResult(d["review_id"], d["language"], d.get("code_preview", ""))
                    r.score = d.get("score", 0)
                    r.issues = [Issue(**i) for i in d.get("issues", [])]
                    r.summary = d.get("summary", "")
                    r.ai_feedback = d.get("ai_feedback", "")
                    r.dimensions = d.get("dimensions", {})
                    r.stats = d.get("stats", {})
                    r.created_at = d.get("created_at", "")
                    self._history.append(r)
            except Exception as e:
                log.error("Failed to load review history: %s", e)

    def _save(self):
        try:
            data = [r.to_dict() for r in self._history[-100:]]
            with open(HISTORY_PATH, "w") as f:
                json.dump(data, f, indent=2)
        except Exception as e:
            log.error("Failed to save reviews: %s", e)

    def get_issues_for_lang(self, lang: str) -> list[dict]:
        lang = LANG_ALIASES.get(lang, lang)
        return COMMON_ISSUES.get(lang, [])

    def get_all_issue_patterns(self) -> dict:
        return {k: v for k, v in COMMON_ISSUES.items() if v}

    async def review(self, code: str, language: str) -> ReviewResult:
        lang = LANG_ALIASES.get(language, language)
        review_id = uuid.uuid4().hex[:12]
        issues: list[Issue] = []
        dim_scores: dict[str, dict] = {}

        # 1. Static analysis — pattern matching
        patterns = COMMON_ISSUES.get(lang, [])
        lines = code.split("\n")
        for pattern in patterns:
            pid = pattern["id"]
            severity = pattern["severity"]
            title = pattern["title"]
            pat = pattern["pattern"]
            multiline = pattern.get("multiline", False)

            dim = pid.split("-")[0]
            if dim == "sec":
                dimension = "security"
            elif dim == "perf":
                dimension = "performance"
            elif dim == "bug":
                dimension = "bugs"
            elif dim == "style":
                dimension = "style"
            else:
                dimension = "best_practices"

            if multiline:
                matches = list(re.finditer(pat, code, re.MULTILINE))
            else:
                matches = list(re.finditer(pat, code))

            for m in matches:
                line_no = code[:m.start()].count("\n") + 1
                snippet = lines[line_no - 1].strip()[:120] if line_no <= len(lines) else ""
                suggestion = self._suggest_fix(title, snippet)
                issues.append(Issue(
                    id=pid, severity=severity, title=title,
                    description=f"Found in {lang} code at line {line_no}",
                    line=line_no, snippet=snippet,
                    dimension=dimension, suggestion=suggestion,
                ))

        # Check for missing docstrings (style-2 special case)
        if lang == "python" and '"""' not in code and "'''" not in code:
            func_count = len(re.findall(r"^def ", code, re.MULTILINE))
            class_count = len(re.findall(r"^class ", code, re.MULTILINE))
            if func_count + class_count > 2:
                issues.append(Issue(
                    id="style-2", severity="info", title="Missing Docstrings",
                    description=f"{func_count} functions and {class_count} classes without docstrings",
                    dimension="style",
                    suggestion="Add docstrings to all public functions and classes",
                ))

        # 2. AI review for deeper analysis
        ai_feedback = ""
        try:
            ai_feedback = await self._ai_review(code, lang)
        except Exception as e:
            ai_feedback = f"AI review unavailable: {e}"

        # 3. Calculate scores per dimension
        dim_scores = {}
        severity_weights = {"critical": 10, "high": 5, "warning": 3, "medium": 2, "info": 1}
        for dim_info in DIMENSIONS:
            dim_id = dim_info["id"]
            dim_issues = [i for i in issues if i.dimension == dim_id]
            count = len(dim_issues)
            weighted = sum(severity_weights.get(i.severity, 1) for i in dim_issues)
            dim_scores[dim_id] = {"count": count, "weighted": weighted, "label": dim_info["label"]}

        total_weighted = sum(d["weighted"] for d in dim_scores.values())
        max_possible = 10 * len(DIMENSIONS)
        score = max(0, min(100, int(100 - (total_weighted / max_possible) * 100)))

        # 4. Generate summary
        critical = len([i for i in issues if i.severity == "critical"])
        high = len([i for i in issues if i.severity == "high"])
        warnings = len([i for i in issues if i.severity in ("warning", "medium")])
        infos = len([i for i in issues if i.severity == "info"])

        summary = (
            f"Found {len(issues)} issues: "
            f"{critical} critical, {high} high, {warnings} medium/warning, {infos} info. "
            f"Quality score: {score}/100."
        )

        result = ReviewResult(
            review_id=review_id, language=lang, code=code,
            score=score, issues=issues, summary=summary,
            ai_feedback=ai_feedback, dimensions=dim_scores,
            stats={"critical": critical, "high": high, "medium": warnings, "info": infos},
        )
        self._history.insert(0, result)
        self._save()
        return result

    async def _ai_review(self, code: str, lang: str) -> str:
        prompt = (
            f"Review this {lang} code for bugs, security issues, and improvements. "
            f"Be concise. List up to 5 specific findings:\n\n```{lang}\n{code[:3000]}\n```"
        )
        try:
            resp = await asyncio.wait_for(
                ai_engine.chat([{"role": "user", "content": prompt}]),
                timeout=30.0,
            )
            return resp.get("message", {}).get("content", "")[:2000]
        except asyncio.TimeoutError:
            return "AI review unavailable: provider timed out (30s)"
        except Exception as e:
            return f"AI review error: {e}"

    def _suggest_fix(self, title: str, snippet: str) -> str:
        suggestions = {
            "SQL Injection": "Use parameterized queries or ORM methods instead of string formatting",
            "Command Injection": "Use subprocess.run with a list instead of shell=True",
            "Hardcoded Secret": "Move secrets to environment variables or .env file",
            "Inefficient Loop": "Use enumerate() or direct iteration instead of range(len())",
            "Line Too Long": "Break line into multiple lines (PEP 8: max 79 characters)",
            "Missing Docstring": "Add docstring (triple-quoted) after function/class definition",
            "Bare Except": "Specify exception type(s) to catch instead of bare except:",
            "Mutable Default Arg": "Use None as default and create mutable inside function body",
            "InnerHTML Assignment": "Use textContent or DOM manipulation methods instead",
            "eval() Usage": "Avoid eval(). Use JSON.parse() for JSON or safer alternatives",
            "== Comparison": "Use === strict equality to avoid type coercion bugs",
            "Any Type Leak": "Replace `any` with specific types or use `unknown`",
            "Error Ignored": "Handle errors explicitly instead of using `_`",
            "unwrap() Usage": "Use pattern matching or `if let` for safe unwrapping",
            "console.log": "Remove console.log before production deployment",
            "Nested Loop": "Consider using a Set/Map or flat map to avoid O(n²)",
        }
        return suggestions.get(title, "")

    def get_history(self, limit: int = 20) -> list[ReviewResult]:
        return self._history[:limit]

    def get_review(self, review_id: str) -> ReviewResult | None:
        for r in self._history:
            if r.review_id == review_id:
                return r
        return None


review_engine = CodeReviewEngine()
