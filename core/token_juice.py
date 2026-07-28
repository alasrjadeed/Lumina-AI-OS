"""TokenJuice — compress tool outputs before they hit the LLM context window."""

from __future__ import annotations

import json
import re
from typing import Any

_MAX_TOKENS_DEFAULT = 2048
_MAX_LINES_DEFAULT = 100


def estimate_tokens(text: str) -> int:
    return len(text) // 4


def compress_json(data: str | dict | list, max_tokens: int = _MAX_TOKENS_DEFAULT) -> str:
    if not data:
        return ""

    if isinstance(data, str):
        try:
            parsed = json.loads(data)
        except (json.JSONDecodeError, ValueError):
            return _compress_text(data, max_tokens)
    else:
        parsed = data

    return _compress_structured(parsed, max_tokens)


def compress_tool_output(
    output: str,
    max_tokens: int = _MAX_TOKENS_DEFAULT,
    max_lines: int = _MAX_LINES_DEFAULT,
) -> str:
    if not output:
        return ""

    if estimate_tokens(output) <= max_tokens:
        lines = output.split("\n")
        if len(lines) <= max_lines:
            return output

    if _looks_like_json(output):
        return compress_json(output, max_tokens)

    if _looks_like_html(output):
        return _compress_html(output, max_tokens)

    return _compress_text(output, max_tokens, max_lines)


def _looks_like_json(text: str) -> bool:
    text = text.strip()
    return (text.startswith("{") and text.endswith("}")) or (text.startswith("[") and text.endswith("]"))


def _looks_like_html(text: str) -> bool:
    return bool(re.search(r'<[a-z][\s>]', text.strip()[:200]))


def _compress_text(text: str, max_tokens: int = _MAX_TOKENS_DEFAULT, max_lines: int = _MAX_LINES_DEFAULT) -> str:
    lines = text.split("\n")

    if len(lines) > max_lines:
        kept = lines[: max_lines // 2]
        kept.append(f"\n... [{len(lines) - max_lines} lines suppressed] ...\n")
        kept.extend(lines[-max_lines // 4:])
        lines = kept

    result = "\n".join(lines)

    if estimate_tokens(result) > max_tokens:
        ratio = max_tokens / estimate_tokens(result)
        keep_chars = int(len(result) * ratio)
        result = result[:keep_chars]
        result += f"\n\n[... truncated to ~{max_tokens} tokens ...]"

    return result


def _compress_structured(data: Any, max_tokens: int = _MAX_TOKENS_DEFAULT) -> str:
    if isinstance(data, dict):
        compressed = {}
        for k, v in data.items():
            if isinstance(v, (str, int, float, bool)) or v is None:
                compressed[k] = v
            elif isinstance(v, (list, dict)):
                serialized = json.dumps(v, ensure_ascii=False)
                if estimate_tokens(serialized) > max_tokens // (len(data) or 1):
                    compressed[k] = f"[{type(v).__name__} with {len(v)} items]"
                else:
                    compressed[k] = _compress_structured(v, max_tokens // (len(data) or 1))
            else:
                compressed[k] = str(v)[:200]
        result = json.dumps(compressed, ensure_ascii=False, indent=2)
        if estimate_tokens(result) > max_tokens:
            result = result[:max_tokens * 4]
            result += "\n[... truncated ...]"
        return result

    if isinstance(data, list):
        items = []
        for item in data[:20]:
            if isinstance(item, (str, int, float, bool)) or item is None:
                items.append(item)
            elif isinstance(item, dict):
                items.append({k: v for k, v in item.items() if isinstance(v, (str, int, float, bool)) or v is None})
            else:
                items.append(str(item)[:100])
        if len(data) > 20:
            items.append(f"... [{len(data) - 20} more items] ...")
        return json.dumps(items, ensure_ascii=False, indent=2)

    return str(data)[:max_tokens * 4]


def _compress_html(html: str, max_tokens: int = _MAX_TOKENS_DEFAULT) -> str:
    text = re.sub(r'<style[^>]*>.*?</style>', '', html, flags=re.DOTALL)
    text = re.sub(r'<script[^>]*>.*?</script>', '', text, flags=re.DOTALL)
    text = re.sub(r'<[^>]+>', ' ', text)
    text = re.sub(r'\s+', ' ', text).strip()
    return _compress_text(text, max_tokens)
