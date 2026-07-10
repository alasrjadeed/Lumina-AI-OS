import json
import re

from core.log import log
from core.provider import engine


class FormFiller:
    def __init__(self):
        self.profiles: dict[str, dict] = {}

    def save_profile(self, name: str, data: dict):
        self.profiles[name] = data
        log.info("Saved form profile: %s (%d fields)", name, len(data))

    def get_profile(self, name: str) -> dict | None:
        return self.profiles.get(name)

    def list_profiles(self) -> list[str]:
        return list(self.profiles.keys())

    async def analyze_form(self, html_form: str) -> list[dict]:
        messages = [
            {
                "role": "system",
                "content": (
                    "Analyze this HTML form. Return a JSON array of fields,"
                    " each with 'name', 'type', 'label', 'required', and 'placeholder'."
                ),
            },
            {"role": "user", "content": html_form[:3000]},
        ]
        try:
            resp = await engine.chat(messages)
            text = resp["message"]["content"]
            match = re.search(r"\[.*\]", text, re.DOTALL)
            if match:
                return json.loads(match.group())
        except Exception:
            pass
        return []

    async def suggest_values(self, fields: list[dict], profile_name: str = "default") -> dict:
        profile = self.profiles.get(profile_name, {})
        messages = [
            {
                "role": "system",
                "content": (
                    "Given these form fields and a user profile, suggest"
                    " appropriate values for each field. Return JSON object"
                    f" mapping field names to values. Profile: {profile}"
                ),
            },
            {"role": "user", "content": str(fields)},
        ]
        try:
            resp = await engine.chat(messages)
            text = resp["message"]["content"]
            match = re.search(r"\{.*\}", text, re.DOTALL)
            if match:
                return json.loads(match.group())
        except Exception:
            pass
        return {}


form_filler = FormFiller()
