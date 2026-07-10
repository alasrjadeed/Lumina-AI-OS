"""Plugin Marketplace — discover, install, publish, and manage Lumina plugins."""

from __future__ import annotations

import json
import os
import shutil
import time
from dataclasses import dataclass, field

from core.log import log

MARKETPLACE_DIR = os.path.expanduser("~/.lumina/marketplace")
PLUGINS_INSTALL_DIR = os.path.expanduser("~/.lumina/plugins")


@dataclass
class PluginListing:
    id: str
    name: str
    version: str
    author: str
    description: str
    category: str
    tags: list[str] = field(default_factory=list)
    icon: str = "plug"
    homepage: str = ""
    repository: str = ""
    license: str = "MIT"
    requires: list[str] = field(default_factory=list)
    rating: float = 0.0
    downloads: int = 0
    installed: bool = False
    installed_version: str = ""
    size_kb: int = 0
    created_at: float = 0.0
    updated_at: float = 0.0

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "name": self.name,
            "version": self.version,
            "author": self.author,
            "description": self.description,
            "category": self.category,
            "tags": self.tags,
            "icon": self.icon,
            "homepage": self.homepage,
            "repository": self.repository,
            "license": self.license,
            "requires": self.requires,
            "rating": self.rating,
            "downloads": self.downloads,
            "installed": self.installed,
            "installed_version": self.installed_version,
            "size_kb": self.size_kb,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
        }

    @classmethod
    def from_dict(cls, d: dict) -> PluginListing:
        return cls(**{k: d.get(k) for k in d if k in cls.__dataclass_fields__})  # pyright: ignore[reportArgumentType]


DEFAULT_CATALOG: list[dict] = [
    {
        "id": "crm-plugin",
        "name": "CRM Manager",
        "version": "1.0.0",
        "author": "Lumina Team",
        "category": "business",
        "description": "CRM pipeline management with contacts, deals, and analytics.",
        "tags": ["crm", "sales", "pipeline", "contacts"],
        "icon": "BarChart3",
        "license": "MIT",
    },
    {
        "id": "email-plugin",
        "name": "Email Automation",
        "version": "1.0.0",
        "author": "Lumina Team",
        "category": "communication",
        "description": "SMTP email sender with templates, campaigns, and CSV import.",
        "tags": ["email", "smtp", "campaign", "newsletter"],
        "icon": "Mail",
        "license": "MIT",
    },
    {
        "id": "lead-plugin",
        "name": "Lead Manager",
        "version": "1.0.0",
        "author": "Lumina Team",
        "category": "sales",
        "description": "Lead capture, scoring, qualification, and analytics.",
        "tags": ["leads", "sales", "prospecting", "scoring"],
        "icon": "UserPlus",
        "license": "MIT",
    },
    {
        "id": "marketing-plugin",
        "name": "Marketing Suite",
        "version": "1.0.0",
        "author": "Lumina Team",
        "category": "marketing",
        "description": "Campaign management, content calendar, and performance tracking.",
        "tags": ["marketing", "campaigns", "content", "analytics"],
        "icon": "Megaphone",
        "license": "MIT",
    },
    {
        "id": "reporting-plugin",
        "name": "Report Generator",
        "version": "1.0.0",
        "author": "Lumina Team",
        "category": "analytics",
        "description": "Generate reports in CSV, JSON, HTML with charts and summaries.",
        "tags": ["reports", "analytics", "csv", "export"],
        "icon": "FileText",
        "license": "MIT",
    },
    {
        "id": "seo-plugin",
        "name": "SEO Suite",
        "version": "1.0.0",
        "author": "Lumina Team",
        "category": "marketing",
        "description": "SEO audit, keyword tracking, competitor analysis, and sitemaps.",
        "tags": ["seo", "keywords", "audit", "ranking"],
        "icon": "Search",
        "license": "MIT",
    },
    {
        "id": "whatsapp-plugin",
        "name": "WhatsApp Automation",
        "version": "1.0.0",
        "author": "Lumina Team",
        "category": "communication",
        "description": "Auto-reply, broadcast campaigns, and template management.",
        "tags": ["whatsapp", "messaging", "campaign", "broadcast"],
        "icon": "MessageSquare",
        "license": "MIT",
    },
]


class PluginMarketplace:
    """Browse, install, and manage plugins for Lumina AI OS."""

    def __init__(self):
        self._catalog: dict[str, PluginListing] = {}
        self._installed: dict[str, PluginListing] = {}
        self._publisher_registry: dict[str, list[str]] = {}
        self._load()

    def _catalog_path(self) -> str:
        os.makedirs(MARKETPLACE_DIR, exist_ok=True)
        return os.path.join(MARKETPLACE_DIR, "catalog.json")

    def _installed_path(self) -> str:
        os.makedirs(MARKETPLACE_DIR, exist_ok=True)
        return os.path.join(MARKETPLACE_DIR, "installed.json")

    def _load(self):
        cp = self._catalog_path()
        if os.path.exists(cp):
            try:
                with open(cp) as f:
                    data = json.load(f)
                for d in data:
                    listing = PluginListing.from_dict(d)
                    self._catalog[listing.id] = listing
            except Exception as e:
                log.warning("Marketplace: failed to load catalog: %s", e)

        if not self._catalog:
            for d in DEFAULT_CATALOG:
                listing = PluginListing(**d, created_at=time.time())
                self._catalog[listing.id] = listing
            self._save_catalog()

        ip = self._installed_path()
        if os.path.exists(ip):
            try:
                with open(ip) as f:
                    data = json.load(f)
                for d in data:
                    listing = PluginListing.from_dict(d)
                    self._installed[listing.id] = listing
            except Exception as e:
                log.warning("Marketplace: failed to load installed: %s", e)

    def _save_catalog(self):
        with open(self._catalog_path(), "w") as f:
            json.dump([item.to_dict() for item in self._catalog.values()], f, indent=2)

    def _save_installed(self):
        with open(self._installed_path(), "w") as f:
            json.dump([item.to_dict() for item in self._installed.values()], f, indent=2)

    def browse(
        self, category: str = "", query: str = "", sort_by: str = "downloads"
    ) -> list[PluginListing]:
        results = list(self._catalog.values())
        if category:
            results = [p for p in results if p.category == category]
        if query:
            q = query.lower()
            results = [
                p
                for p in results
                if q in p.name.lower() or q in p.description.lower() or any(q in t for t in p.tags)
            ]
        for p in results:
            if p.id in self._installed:
                inst = self._installed[p.id]
                p.installed = True
                p.installed_version = inst.installed_version

        sort_key = {
            "downloads": lambda x: -x.downloads,
            "rating": lambda x: -x.rating,
            "name": lambda x: x.name.lower(),
            "updated": lambda x: -x.updated_at,
        }.get(sort_by, lambda x: -x.downloads)

        return sorted(results, key=sort_key)

    def get_plugin(self, plugin_id: str) -> PluginListing | None:
        listing = self._catalog.get(plugin_id)
        if listing and plugin_id in self._installed:
            listing.installed = True
            listing.installed_version = self._installed[plugin_id].installed_version
        return listing

    def install(self, plugin_id: str) -> dict:
        listing = self._catalog.get(plugin_id)
        if not listing:
            return {"error": f"Plugin not found: {plugin_id}"}

        if plugin_id in self._installed:
            return {"status": "already_installed", "plugin": listing.to_dict()}

        for req in listing.requires:
            if req not in self._installed:
                return {"error": f"Missing dependency: {req}", "required": listing.requires}

        install_dir = os.path.join(PLUGINS_INSTALL_DIR, plugin_id)
        os.makedirs(install_dir, exist_ok=True)

        manifest = {
            "id": listing.id,
            "name": listing.name,
            "version": listing.version,
            "author": listing.author,
            "description": listing.description,
            "category": listing.category,
            "license": listing.license,
            "installed_at": time.time(),
        }
        with open(os.path.join(install_dir, "manifest.json"), "w") as f:
            json.dump(manifest, f, indent=2)

        listing.installed = True
        listing.installed_version = listing.version
        listing.downloads += 1
        self._installed[plugin_id] = listing
        self._save_catalog()
        self._save_installed()

        log.info("Marketplace: installed plugin: %s v%s", listing.name, listing.version)
        return {"status": "installed", "plugin": listing.to_dict(), "path": install_dir}

    def uninstall(self, plugin_id: str) -> dict:
        if plugin_id not in self._installed:
            return {"error": f"Plugin not installed: {plugin_id}"}

        dependents = [
            pid for pid, listing in self._installed.items() if plugin_id in listing.requires
        ]
        if dependents:
            return {
                "error": f"Cannot uninstall: required by {dependents}",
                "dependents": dependents,
            }

        listing = self._installed.pop(plugin_id)
        listing.installed = False
        listing.installed_version = ""

        if plugin_id in self._catalog:
            self._catalog[plugin_id].installed = False
            self._catalog[plugin_id].installed_version = ""

        install_dir = os.path.join(PLUGINS_INSTALL_DIR, plugin_id)
        if os.path.exists(install_dir):
            shutil.rmtree(install_dir)

        self._save_catalog()
        self._save_installed()

        log.info("Marketplace: uninstalled plugin: %s", listing.name)
        return {"status": "uninstalled", "plugin": listing.to_dict()}

    def update(self, plugin_id: str) -> dict:
        listing = self._catalog.get(plugin_id)
        installed = self._installed.get(plugin_id)
        if not listing:
            return {"error": f"Plugin not found: {plugin_id}"}
        if not installed:
            return {"error": f"Plugin not installed: {plugin_id}"}

        if listing.version == installed.installed_version:
            return {"status": "up_to_date", "plugin": listing.to_dict()}

        installed.installed_version = listing.version
        self._save_installed()
        return {
            "status": "updated",
            "plugin": installed.to_dict(),
            "from_version": installed.installed_version,
            "to_version": listing.version,
        }

    def get_installed(self) -> list[PluginListing]:
        return sorted(self._installed.values(), key=lambda p: p.name.lower())

    def get_categories(self) -> list[str]:
        cats = set(p.category for p in self._catalog.values())
        return sorted(cats)

    def get_stats(self) -> dict:
        return {
            "total_plugins": len(self._catalog),
            "installed": len(self._installed),
            "categories": len(self.get_categories()),
            "total_downloads": sum(p.downloads for p in self._catalog.values()),
        }

    def search(self, query: str) -> list[PluginListing]:
        q = query.lower()
        return sorted(
            [
                p
                for p in self._catalog.values()
                if q in p.name.lower() or q in p.description.lower() or any(q in t for t in p.tags)
            ],
            key=lambda p: -p.downloads,
        )

    def add_to_catalog(self, listing_data: dict) -> PluginListing:
        pid = listing_data.get("id", "")
        if not pid:
            import uuid

            pid = uuid.uuid4().hex[:12]
            listing_data["id"] = pid

        listing = PluginListing(
            **{
                k: listing_data.get(k, "" if k != "tags" and k != "requires" else [])
                for k in PluginListing.__dataclass_fields__
                if k in listing_data or k == "tags" or k == "requires"
            },
            created_at=time.time(),
            updated_at=time.time(),
        )
        self._catalog[pid] = listing
        self._save_catalog()
        return listing

    def remove_from_catalog(self, plugin_id: str) -> bool:
        if plugin_id in self._catalog:
            del self._catalog[plugin_id]
            if plugin_id in self._installed:
                del self._installed[plugin_id]
            self._save_catalog()
            self._save_installed()
            return True
        return False


marketplace = PluginMarketplace()
