"""Personal Data Vault — centralized personal & business information storage."""

from __future__ import annotations

import json
import os
from dataclasses import dataclass, field
from typing import Any

from core.log import log


@dataclass
class VaultEntry:
    """A single piece of information in the vault."""
    key: str
    value: str
    category: str = "personal"
    label: str = ""
    tags: list[str] = field(default_factory=list)


@dataclass
class VaultProfile:
    """A complete profile (personal or business)."""
    name: str = ""
    email: str = ""
    phone: str = ""
    business_name: str = ""
    address: str = ""
    website: str = ""
    facebook: str = ""
    instagram: str = ""
    linkedin: str = ""
    twitter: str = ""
    youtube: str = ""
    tiktok: str = ""
    logo_url: str = ""
    gst_vat: str = ""
    description: str = ""
    products: str = ""
    categories: str = ""
    tags: list[str] = field(default_factory=list)


DEFAULT_KEYS = [
    "name", "email", "phone",
    "business_name", "address", "website",
    "facebook", "instagram", "linkedin", "twitter", "youtube", "tiktok",
    "logo_url", "gst_vat", "description", "products", "categories",
]


class DataVault:
    """Store personal & business data once. AI auto-fills when needed."""

    def __init__(self, path: str = "lumina_vault.json"):
        self.path = path
        self._data: dict[str, str] = {}
        self._load()

    def _load(self) -> None:
        if os.path.exists(self.path):
            try:
                with open(self.path) as f:
                    self._data = json.load(f)
            except Exception:
                self._data = {}

    def _save(self) -> None:
        with open(self.path, "w") as f:
            json.dump(self._data, f, indent=2)

    def get(self, key: str, default: str = "") -> str:
        return self._data.get(key, default)

    def set(self, key: str, value: str) -> None:
        self._data[key] = value
        self._save()

    def set_many(self, items: dict[str, str]) -> None:
        self._data.update(items)
        self._save()

    def delete(self, key: str) -> bool:
        if key in self._data:
            del self._data[key]
            self._save()
            return True
        return False

    def all(self) -> dict[str, str]:
        return dict(self._data)

    def get_profile(self) -> VaultProfile:
        return VaultProfile(
            name=self._data.get("name", ""),
            email=self._data.get("email", ""),
            phone=self._data.get("phone", ""),
            business_name=self._data.get("business_name", ""),
            address=self._data.get("address", ""),
            website=self._data.get("website", ""),
            facebook=self._data.get("facebook", ""),
            instagram=self._data.get("instagram", ""),
            linkedin=self._data.get("linkedin", ""),
            twitter=self._data.get("twitter", ""),
            youtube=self._data.get("youtube", ""),
            tiktok=self._data.get("tiktok", ""),
            logo_url=self._data.get("logo_url", ""),
            gst_vat=self._data.get("gst_vat", ""),
            description=self._data.get("description", ""),
            products=self._data.get("products", ""),
            categories=self._data.get("categories", ""),
        )

    def set_profile(self, profile: VaultProfile) -> None:
        self._data["name"] = profile.name
        self._data["email"] = profile.email
        self._data["phone"] = profile.phone
        self._data["business_name"] = profile.business_name
        self._data["address"] = profile.address
        self._data["website"] = profile.website
        self._data["facebook"] = profile.facebook
        self._data["instagram"] = profile.instagram
        self._data["linkedin"] = profile.linkedin
        self._data["twitter"] = profile.twitter
        self._data["youtube"] = profile.youtube
        self._data["tiktok"] = profile.tiktok
        self._data["logo_url"] = profile.logo_url
        self._data["gst_vat"] = profile.gst_vat
        self._data["description"] = profile.description
        self._data["products"] = profile.products
        self._data["categories"] = profile.categories
        self._save()

    def to_context_prompt(self) -> str:
        """Generate a prompt snippet for AI to use this data."""
        filled = {k: v for k, v in self._data.items() if v}
        if not filled:
            return ""
        parts = ["## Available User Information"]
        for key, value in filled.items():
            label = key.replace("_", " ").title()
            parts.append(f"- {label}: {value}")
        return "\n".join(parts)

    def fill_template(self, text: str) -> str:
        """Replace {{key}} placeholders with vault data."""
        for key, value in self._data.items():
            text = text.replace("{{" + key + "}}", value)
        return text

    def clear(self) -> None:
        self._data.clear()
        self._save()

    def count(self) -> int:
        return len(self._data)

    def missing_required(self) -> list[str]:
        """Return list of important fields that are empty."""
        return [k for k in ["name", "email", "phone"] if k not in self._data or not self._data[k]]


vault = DataVault()
