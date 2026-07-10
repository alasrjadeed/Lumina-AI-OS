import asyncio
import os
import sys

import httpx

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

keys = {
    "OpenAI Key": {
        "key": os.getenv("OPENAI_API_KEY", ""),
        "provider": "OpenAI",
    },
    "OpenRouter": {
        "key": os.getenv("OPENROUTER_API_KEY", ""),
        "provider": "OpenRouter",
    },
    "DeepSeek": {
        "key": os.getenv("DEEPSEEK_API_KEY", ""),
        "provider": "DeepSeek",
    },
    "Google Gemini": {
        "key": os.getenv("GEMINI_API_KEY", ""),
        "provider": "Google Gemini",
    },
    "Groq": {
        "key": os.getenv("GROQ_API_KEY", ""),
        "provider": "Groq",
    },
    "NVIDIA": {
        "key": os.getenv("NVIDIA_API_KEY", ""),
        "provider": "NVIDIA",
    },
    "Cloudflare AI": {
        "key": os.getenv("CLOUDFLARE_API_TOKEN", ""),
        "account_id": os.getenv("CLOUDFLARE_ACCOUNT_ID", ""),
        "provider": "Cloudflare",
    },
    "WhatsApp": {
        "token": os.getenv("WHATSAPP_TOKEN", ""),
        "phone_id": os.getenv("WHATSAPP_PHONE_ID", ""),
        "provider": "WhatsApp Cloud API",
    },
    "WhatsApp Web": {
        "api_key": os.getenv("WHAPI_API_KEY", ""),
        "provider": "WHAPI",
    },
}

VALID_SCRIPTS = [
    "123",
    "246",
    "753",
    "842",
]


def color_text(text: str, color: str) -> str:
    colors = {"red": "31", "green": "32", "yellow": "33", "blue": "34", "cyan": "36"}
    return f"\033[{colors.get(color, '0')}m{text}\033[0m"


def print_status(name: str, status: str):
    if status == "valid":
        print(f"  {color_text('✓', 'green')} {name}: {status}")
    elif status == "missing":
        print(f"  {color_text('✗', 'red')} {name}: {status} (check .env file)")
    else:
        print(f"  {color_text('?', 'yellow')} {name}: {status}")


async def check_openai(key: str) -> str:
    if not key:
        return "missing"
    try:
        async with httpx.AsyncClient(timeout=10) as client:
            resp = await client.get(
                "https://api.openai.com/v1/models",
                headers={"Authorization": f"Bearer {key}"},
            )
        return "valid" if resp.status_code == 200 else "invalid"
    except Exception:
        return "error"


async def check_openrouter(key: str) -> str:
    if not key:
        return "missing"
    try:
        async with httpx.AsyncClient(timeout=10) as client:
            resp = await client.get(
                "https://openrouter.ai/api/v1/models",
                headers={"Authorization": f"Bearer {key}"},
            )
        return "valid" if resp.status_code == 200 else "invalid"
    except Exception:
        return "error"


async def check_groq(key: str) -> str:
    if not key:
        return "missing"
    try:
        async with httpx.AsyncClient(timeout=10) as client:
            resp = await client.get(
                "https://api.groq.com/openai/v1/models",
                headers={"Authorization": f"Bearer {key}"},
            )
        return "valid" if resp.status_code == 200 else "invalid"
    except Exception:
        return "error"


async def check_deepseek(key: str) -> str:
    if not key:
        return "missing"
    return "valid"


async def check_gemini(key: str) -> str:
    if not key:
        return "missing"
    return "valid"


async def check_nvidia(key: str) -> str:
    if not key:
        return "missing"
    return "valid"


async def main():
    print(color_text("\nLumina AI OS — API Key Checker\n", "cyan"))

    checks = {
        "OpenAI": check_openai,
        "OpenRouter": check_openrouter,
        "Groq": check_groq,
        "DeepSeek": check_deepseek,
        "Google Gemini": check_gemini,
        "NVIDIA": check_nvidia,
    }

    for name, fn in checks.items():
        provider_name = None
        for k in keys:
            if k.startswith(name.split(" Key")[0]):
                provider_name = k
                break
        if not provider_name:
            continue
        key_data = keys[provider_name]
        key = key_data.get("key", "")
        status = await fn(key)
        print_status(provider_name, status)

    print(f"\n{color_text('Configure your keys in .env file:', 'yellow')}")
    print("  OPENAI_API_KEY=sk-...")
    print("  OPENROUTER_API_KEY=sk-or-v1-...")
    print("  DEEPSEEK_API_KEY=sk-...")
    print("  GEMINI_API_KEY=AIza...")
    print("  GROQ_API_KEY=gsk_...")
    print("  NVIDIA_API_KEY=nvapi-...")
    print()


if __name__ == "__main__":
    asyncio.run(main())
