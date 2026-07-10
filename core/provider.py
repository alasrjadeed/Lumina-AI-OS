from __future__ import annotations

import asyncio
import json
import random
import time
from collections.abc import AsyncIterator
from typing import Any

import httpx

from config.settings import settings

TIMEOUT = 60.0
MAX_RETRIES = 3
BASE_DELAY = 1.0
MAX_DELAY = 10.0


class ProviderError(Exception): ...


class _SharedClient:
    _client: httpx.AsyncClient | None = None
    _lock = asyncio.Lock()

    @classmethod
    async def get(cls) -> httpx.AsyncClient:
        if cls._client is None:
            async with cls._lock:
                if cls._client is None:
                    limits = httpx.Limits(max_keepalive_connections=20, max_connections=100)
                    cls._client = httpx.AsyncClient(timeout=httpx.Timeout(TIMEOUT), limits=limits)
        return cls._client


async def retry_request(
    method: str,
    url: str,
    *,
    json: dict | None = None,
    headers: dict[str, str] | None = None,
    timeout: float = TIMEOUT,  # pyright: ignore[reportCallIssue]
    max_retries: int = MAX_RETRIES,
    stream: bool = False,
) -> httpx.Response:
    client = await _SharedClient.get()
    last_error: Exception | None = None
    for attempt in range(1, max_retries + 1):
        try:
            if stream:
                return await client.send(
                    client.build_request(method, url, json=json, headers=headers),
                    stream=True,
                    timeout=httpx.Timeout(timeout),  # pyright: ignore[reportCallIssue]
                )
            resp = await client.request(
                method, url, json=json, headers=headers, timeout=httpx.Timeout(timeout)
            )
            resp.raise_for_status()
            return resp
        except httpx.HTTPStatusError as e:
            status = e.response.status_code
            if status in (429, 502, 503, 504) and attempt < max_retries:
                delay = _backoff(attempt)
                await asyncio.sleep(delay)
                last_error = e
                continue
            raise ProviderError(f"HTTP {status} from {url.split('?', maxsplit=1)[0]}: {e}") from e
        except (httpx.TimeoutException, httpx.ConnectError, httpx.RemoteProtocolError) as e:
            if attempt < max_retries:
                delay = _backoff(attempt)
                await asyncio.sleep(delay)
                last_error = e
                continue
            raise ProviderError(f"{type(e).__name__} after {attempt} attempts: {e}") from e
    raise ProviderError(f"Request failed after {max_retries} retries") from last_error


def _backoff(attempt: int) -> float:
    delay = min(BASE_DELAY * (2 ** (attempt - 1)), MAX_DELAY)
    jitter = random.uniform(0, delay * 0.5)
    return delay + jitter


class AIProvider:
    def __init__(self):
        self.name = "ai_provider"
        self.api_key: str | None = None
        self.base_url: str = ""
        self.model: str = ""

    async def _post(self, url: str, payload: dict, headers: dict | None = None) -> dict:
        hdrs = {"Content-Type": "application/json"}
        if self.api_key:
            hdrs["Authorization"] = f"Bearer {self.api_key}"
        if headers:
            hdrs.update(headers)
        resp = await retry_request("POST", url, json=payload, headers=hdrs)
        return resp.json()

    async def chat(self, messages: list[dict], tools: list[dict] | None = None, **kwargs) -> dict:
        raise NotImplementedError

    async def chat_stream(
        self, messages: list[dict], tools: list[dict] | None = None, **kwargs
    ) -> AsyncIterator[str]:
        if False:
            yield
        raise NotImplementedError

    def _openai_chat(self, data: dict) -> dict:
        choice = data["choices"][0]
        message = choice["message"]
        result = {
            "role": message.get("role", "assistant"),
            "content": message.get("content", ""),
        }
        if "tool_calls" in message and message["tool_calls"]:
            result["tool_calls"] = message["tool_calls"]
        return {"message": result}

    def _build_payload(
        self, messages: list[dict], tools: list[dict] | None = None, **kwargs
    ) -> dict:
        return {
            "model": kwargs.get("model", self.model),
            "messages": messages,
            "temperature": kwargs.get("temperature", settings.temperature),
            "max_tokens": kwargs.get("max_tokens", settings.max_tokens),
            "stream": False,
        }


class OllamaProvider(AIProvider):
    OLLAMA_TIMEOUT = 120.0

    def __init__(self):
        self.name = "ollama"
        self.base_url = settings.ollama_base_url
        self.model = settings.ollama_model

    async def chat(self, messages: list[dict], tools: list[dict] | None = None, **kwargs) -> dict:
        payload: dict[str, Any] = {
            "model": kwargs.get("model", self.model),
            "messages": messages,
            "stream": False,
            "options": {
                "temperature": kwargs.get("temperature", settings.temperature),
                "num_predict": kwargs.get("max_tokens", settings.max_tokens),
            },
        }
        if tools:
            payload["tools"] = tools
        try:
            resp = await retry_request(
                "POST",
                f"{self.base_url}/api/chat",
                json=payload,
                timeout=self.OLLAMA_TIMEOUT,
            )
            data = resp.json()
        except ProviderError as e:
            raise ProviderError(f"Ollama ({self.model}): {e}") from e
        message = data.get("message", {})
        result = {
            "role": message.get("role", "assistant"),
            "content": message.get("content", ""),
        }
        if "tool_calls" in message:
            result["tool_calls"] = message["tool_calls"]
        return {"message": result}

    async def chat_stream(
        self, messages: list[dict], tools: list[dict] | None = None, **kwargs
    ) -> AsyncIterator[str]:  # pyright: ignore[reportIncompatibleMethodOverride]
        payload: dict[str, Any] = {
            "model": kwargs.get("model", self.model),
            "messages": messages,
            "stream": True,
            "options": {
                "temperature": kwargs.get("temperature", settings.temperature),
                "num_predict": kwargs.get("max_tokens", settings.max_tokens),
            },
        }
        if tools:
            payload["tools"] = tools
        try:
            resp = await retry_request(
                "POST",
                f"{self.base_url}/api/chat",
                json=payload,
                timeout=self.OLLAMA_TIMEOUT,
                stream=True,
            )
        except ProviderError as e:
            raise ProviderError(f"Ollama stream ({self.model}): {e}") from e
        async for line in resp.aiter_lines():
            if not line.strip():
                continue
            try:
                chunk = json.loads(line)
            except json.JSONDecodeError:
                continue
            if chunk.get("done"):
                return
            content = chunk.get("message", {}).get("content", "")
            if content:
                yield content

    async def check_health(self):
        try:
            resp = await retry_request(
                "GET", f"{self.base_url}/api/tags", timeout=5.0, max_retries=1
            )
            return resp.status_code == 200
        except Exception:
            return False

    async def list_models(self) -> list[dict]:
        resp = await retry_request("GET", f"{self.base_url}/api/tags", timeout=10.0)
        data = resp.json()
        return data.get("models", [])

    async def pull_model(self, model: str) -> None:
        payload = {"name": model, "stream": False}
        await retry_request("POST", f"{self.base_url}/api/pull", json=payload, timeout=300.0)


class OpenRouterProvider(AIProvider):
    def __init__(self):
        self.name = "openrouter"
        self.api_key = settings.openrouter_api_key
        self.base_url = "https://openrouter.ai/api/v1"
        self.model = getattr(settings, "openrouter_model", "cohere/north-mini-code:free")

    async def chat(self, messages: list[dict], tools: list[dict] | None = None, **kwargs) -> dict:
        payload = self._build_payload(messages, tools, **kwargs)
        data = await self._post(f"{self.base_url}/chat/completions", payload)
        return self._openai_chat(data)

    async def chat_stream(
        self, messages: list[dict], tools: list[dict] | None = None, **kwargs
    ) -> AsyncIterator[str]:
        payload = self._build_payload(messages, tools, **kwargs)
        payload["stream"] = True
        resp = await retry_request(
            "POST",
            f"{self.base_url}/chat/completions",
            json=payload,
            headers={"Authorization": f"Bearer {self.api_key}"},
            stream=True,
        )
        async for line in resp.aiter_lines():
            if line.startswith("data: "):
                chunk = line[6:]
                if chunk == "[DONE]":
                    return
                try:
                    delta = json.loads(chunk)["choices"][0].get("delta", {})
                except (json.JSONDecodeError, KeyError, IndexError):
                    continue
                content = delta.get("content", "")
                if content:
                    yield content


class DeepSeekProvider(AIProvider):
    def __init__(self):
        self.name = "deepseek"
        self.api_key = settings.deepseek_api_key
        self.base_url = "https://api.deepseek.com"
        self.model = getattr(settings, "deepseek_model", "deepseek-chat")

    async def chat(self, messages: list[dict], tools: list[dict] | None = None, **kwargs) -> dict:
        payload = self._build_payload(messages, tools, **kwargs)
        data = await self._post(f"{self.base_url}/v1/chat/completions", payload)
        return self._openai_chat(data)

    async def chat_stream(
        self, messages: list[dict], tools: list[dict] | None = None, **kwargs
    ) -> AsyncIterator[str]:  # pyright: ignore[reportIncompatibleMethodOverride]
        payload = self._build_payload(messages, tools, **kwargs)
        payload["stream"] = True
        resp = await retry_request(
            "POST",
            f"{self.base_url}/chat/completions",
            json=payload,
            headers={"Authorization": f"Bearer {self.api_key}"},
            stream=True,
        )
        async for line in resp.aiter_lines():
            if line.startswith("data: "):
                chunk = line[6:]
                if chunk == "[DONE]":
                    return
                try:
                    delta = json.loads(chunk)["choices"][0].get("delta", {})
                except (json.JSONDecodeError, KeyError, IndexError):
                    continue
                content = delta.get("content", "")
                if content:
                    yield content


class OpenAIProvider(AIProvider):
    def __init__(self):
        self.name = "openai"
        self.api_key = settings.openai_api_key
        self.base_url = settings.openai_base_url or "https://api.openai.com/v1"
        self.model = getattr(settings, "openai_model", "gpt-4o-mini")

    async def chat(self, messages: list[dict], tools: list[dict] | None = None, **kwargs) -> dict:
        payload = self._build_payload(messages, tools, **kwargs)
        data = await self._post(f"{self.base_url}/chat/completions", payload)
        return self._openai_chat(data)

    async def chat_stream(
        self, messages: list[dict], tools: list[dict] | None = None, **kwargs
    ) -> AsyncIterator[str]:  # pyright: ignore[reportIncompatibleMethodOverride]
        payload = self._build_payload(messages, tools, **kwargs)
        payload["stream"] = True
        resp = await retry_request(
            "POST",
            f"{self.base_url}/chat/completions",
            json=payload,
            headers={"Authorization": f"Bearer {self.api_key}"},
            stream=True,
        )
        async for line in resp.aiter_lines():
            if line.startswith("data: "):
                chunk = line[6:]
                if chunk == "[DONE]":
                    return
                try:
                    delta = json.loads(chunk)["choices"][0].get("delta", {})
                except (json.JSONDecodeError, KeyError, IndexError):
                    continue
                content = delta.get("content", "")
                if content:
                    yield content


class GroqProvider(AIProvider):
    def __init__(self):
        self.name = "groq"
        self.api_key = settings.groq_api_key
        self.base_url = "https://api.groq.com/openai/v1"
        self.model = settings.groq_model

    async def chat(self, messages: list[dict], tools: list[dict] | None = None, **kwargs) -> dict:
        payload = self._build_payload(messages, tools, **kwargs)
        data = await self._post(f"{self.base_url}/chat/completions", payload)
        return self._openai_chat(data)

    async def chat_stream(
        self, messages: list[dict], tools: list[dict] | None = None, **kwargs
    ) -> AsyncIterator[str]:
        payload = self._build_payload(messages, tools, **kwargs)
        payload["stream"] = True
        resp = await retry_request(
            "POST",
            f"{self.base_url}/chat/completions",
            json=payload,
            headers={"Authorization": f"Bearer {self.api_key}"},
            stream=True,
        )
        async for line in resp.aiter_lines():
            if line.startswith("data: "):
                chunk = line[6:]
                if chunk == "[DONE]":
                    return
                try:
                    delta = json.loads(chunk)["choices"][0].get("delta", {})
                except (json.JSONDecodeError, KeyError, IndexError):
                    continue
                content = delta.get("content", "")
                if content:
                    yield content


class GeminiProvider(AIProvider):
    def __init__(self):
        self.name = "gemini"
        self.api_key = settings.gemini_api_key
        self.base_url = "https://generativelanguage.googleapis.com/v1beta"
        self.model = getattr(settings, "gemini_model", "gemini-1.5-flash")

    async def chat(self, messages: list[dict], tools: list[dict] | None = None, **kwargs) -> dict:
        model = kwargs.get("model", self.model)
        contents = []
        for m in messages:
            role = "model" if m["role"] == "assistant" else "user"
            contents.append({"role": role, "parts": [{"text": m["content"]}]})
        payload: dict[str, Any] = {"contents": contents}
        data = await self._post(
            f"{self.base_url}/models/{model}:generateContent?key={self.api_key}",
            payload,
            headers={},
        )
        parts = data.get("candidates", [{}])[0].get("content", {}).get("parts", [{}])
        text = parts[0].get("text", "") if parts else ""
        return {"message": {"role": "assistant", "content": text}}


class CloudflareAIProvider(AIProvider):
    def __init__(self):
        self.name = "cloudflare"
        self.api_key = settings.cloudflare_api_token
        self.account_id = settings.cloudflare_account_id
        self.base_url = f"https://api.cloudflare.com/client/v4/accounts/{self.account_id}/ai/run"
        self.model = "@cf/meta/llama-3.3-70b-instruct-fp8-fast"

    async def chat(self, messages: list[dict], tools: list[dict] | None = None, **kwargs) -> dict:
        model = kwargs.get("model", self.model)
        payload = {
            "messages": messages,
            "max_tokens": kwargs.get("max_tokens", settings.max_tokens),
            "temperature": kwargs.get("temperature", settings.temperature),
        }
        headers = {"Authorization": f"Bearer {self.api_key}"}
        resp = await retry_request(
            "POST",
            f"{self.base_url}/{model}",
            json=payload,
            headers=headers,
        )
        data = resp.json()
        text = data.get("result", {}).get("response", "")
        return {"message": {"role": "assistant", "content": text}}


class NVIDIAProvider(AIProvider):
    def __init__(self):
        self.name = "nvidia"
        self.api_key = settings.nvidia_api_key
        self.base_url = "https://integrate.api.nvidia.com/v1"
        self.model = getattr(settings, "nvidia_model", "nvidia/llama-3.1-nemotron-70b-instruct")

    async def chat(self, messages: list[dict], tools: list[dict] | None = None, **kwargs) -> dict:
        payload = self._build_payload(messages, tools, **kwargs)
        data = await self._post(f"{self.base_url}/chat/completions", payload)
        return self._openai_chat(data)


class _ProviderSlot:
    def __init__(self, provider: AIProvider):
        self.provider = provider
        self.consecutive_failures = 0
        self.cooldown_until: float = 0.0
        self.last_error: str = ""


class AIEngine:
    def __init__(self):
        self._slots: list[_ProviderSlot] = []
        self._init_providers()

    def _init_providers(self):
        order = [
            ("ollama", OllamaProvider),
            ("groq", GroqProvider),
            ("openrouter", OpenRouterProvider),
            ("deepseek", DeepSeekProvider),
            ("openai", OpenAIProvider),
            ("gemini", GeminiProvider),
            ("cloudflare", CloudflareAIProvider),
            ("nvidia", NVIDIAProvider),
        ]
        key_map = {
            "ollama": True,
            "openrouter": bool(settings.openrouter_api_key),
            "groq": bool(settings.groq_api_key),
            "gemini": bool(settings.gemini_api_key),
            "deepseek": bool(settings.deepseek_api_key),
            "openai": bool(settings.openai_api_key),
            "cloudflare": bool(settings.cloudflare_api_token and settings.cloudflare_account_id),
            "nvidia": bool(settings.nvidia_api_key),
        }
        for name, cls in order:
            if key_map.get(name):
                self._slots.append(_ProviderSlot(cls()))

    @property
    def providers(self) -> list[AIProvider]:
        return [s.provider for s in self._slots]

    def _get_available(self) -> list[_ProviderSlot]:
        now = time.time()
        available = []
        for slot in self._slots:
            if slot.cooldown_until > now:
                continue
            available.append(slot)
        return available or self._slots

    def _record_failure(self, slot: _ProviderSlot, error: str) -> None:
        slot.consecutive_failures += 1
        slot.last_error = error
        if slot.consecutive_failures >= 3:
            slot.cooldown_until = time.time() + min(60 * slot.consecutive_failures, 300)

    def _record_success(self, slot: _ProviderSlot) -> None:
        slot.consecutive_failures = 0
        slot.cooldown_until = 0.0
        slot.last_error = ""

    async def chat(self, messages: list[dict], tools: list[dict] | None = None, **kwargs) -> dict:
        errors = []
        for slot in self._get_available():
            try:
                result = await slot.provider.chat(messages, tools=tools, **kwargs)
                self._record_success(slot)
                return result
            except Exception as e:
                self._record_failure(slot, str(e))
                errors.append(f"{slot.provider.name}: {e}")
                continue
        raise Exception("All providers failed:\n" + "\n".join(errors))

    async def chat_stream(
        self, messages: list[dict], tools: list[dict] | None = None, **kwargs
    ) -> AsyncIterator[str]:  # pyright: ignore[reportGeneralTypeIssues]
        errors = []
        for slot in self._get_available():
            try:
                stream = slot.provider.chat_stream(messages, tools=tools, **kwargs)
                async for token in stream:  # pyright: ignore[reportGeneralTypeIssues]
                    yield token
                self._record_success(slot)
                return
            except NotImplementedError:
                errors.append(f"{slot.provider.name}: streaming not supported")
                continue
            except Exception as e:
                self._record_failure(slot, str(e))
                errors.append(f"{slot.provider.name}: {e}")
                continue
        raise Exception("All providers failed for streaming:\n" + "\n".join(errors))

    async def check_health(self):  # pyright: ignore[reportAttributeAccessIssue]
        for slot in self._slots:
            p = slot.provider
            if hasattr(p, "check_health"):
                try:
                    ok = await p.check_health()  # pyright: ignore[reportAttributeAccessIssue]
                    if ok:
                        return True
                except Exception:
                    continue
        return False

    async def status(self) -> list[dict]:
        results = []
        for slot in self._slots:
            p = slot.provider
            healthy = False
            if hasattr(p, "check_health"):
                try:
                    healthy = await p.check_health()  # pyright: ignore[reportAttributeAccessIssue]
                except Exception:
                    healthy = False
            results.append(
                {
                    "name": p.name,
                    "model": p.model,
                    "healthy": healthy,
                    "consecutive_failures": slot.consecutive_failures,
                    "last_error": slot.last_error,
                }
            )
        return results

    async def close(self) -> None:
        await _SharedClient.close()  # pyright: ignore[reportAttributeAccessIssue]


engine = AIEngine()
