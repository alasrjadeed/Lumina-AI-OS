"""Business Memory — stores company data, clients, products, pricing, and auto-injects into AI context."""

from __future__ import annotations

import json
import os
import time
from dataclasses import dataclass, field

from core.log import log

VAULT_DIR = os.path.expanduser("~/.lumina/vault")


@dataclass
class Client:
    id: str = ""
    name: str = ""
    company: str = ""
    email: str = ""
    phone: str = ""
    status: str = "lead"
    source: str = ""
    notes: str = ""
    tags: list[str] = field(default_factory=list)
    projects: list[str] = field(default_factory=list)
    total_value: float = 0.0
    last_contact: float = 0.0
    created_at: float = 0.0

    def to_dict(self) -> dict:
        return {k: v for k, v in self.__dict__.items()}


@dataclass
class Product:
    id: str = ""
    name: str = ""
    description: str = ""
    price: float = 0.0
    currency: str = "USD"
    category: str = ""
    tags: list[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {k: v for k, v in self.__dict__.items()}


@dataclass
class Invoice:
    id: str = ""
    client_id: str = ""
    number: str = ""
    date: str = ""
    due_date: str = ""
    items: list[dict] = field(default_factory=list)
    subtotal: float = 0.0
    tax: float = 0.0
    total: float = 0.0
    status: str = "draft"
    notes: str = ""

    def to_dict(self) -> dict:
        return {k: v for k, v in self.__dict__.items()}


@dataclass
class BrandInfo:
    name: str = ""
    tagline: str = ""
    primary_color: str = "#6366f1"
    secondary_color: str = "#8b5cf6"
    accent_color: str = "#f59e0b"
    font_heading: str = "Inter"
    font_body: str = "Inter"
    logo_url: str = ""
    favicon_url: str = ""
    tone: str = "professional"
    voice: str = "helpful, knowledgeable, warm"

    def to_dict(self) -> dict:
        return {k: v for k, v in self.__dict__.items()}

    def to_css_vars(self) -> str:
        return (
            f"--color-primary: {self.primary_color};\n"
            f"--color-secondary: {self.secondary_color};\n"
            f"--color-accent: {self.accent_color};\n"
            f"--font-heading: '{self.font_heading}', sans-serif;\n"
            f"--font-body: '{self.font_body}', sans-serif;"
        )


class BusinessMemory:
    """Centralized business knowledge — clients, products, pricing, brand, templates.
    Auto-injected into every Core AI request so agents always have context."""

    def __init__(self):
        self._company: dict[str, str] = {}
        self._brand = BrandInfo()
        self._clients: dict[str, Client] = {}
        self._products: dict[str, Product] = {}
        self._invoices: dict[str, Invoice] = {}
        self._templates: dict[str, str] = {}
        self._pricing: dict[str, dict] = {}
        self._social: dict[str, str] = {}
        self._load()

    def _path(self, name: str) -> str:
        os.makedirs(VAULT_DIR, exist_ok=True)
        return os.path.join(VAULT_DIR, f"{name}.json")

    def _load(self):
        for fname, attr in [
            ("company", "_company"), ("brand", "_brand"),
            ("clients", "_clients"), ("products", "_products"),
            ("invoices", "_invoices"), ("templates", "_templates"),
            ("pricing", "_pricing"), ("social", "_social"),
        ]:
            path = self._path(fname)
            if os.path.exists(path):
                try:
                    with open(path) as f:
                        data = json.load(f)
                    if fname == "brand":
                        self._brand = BrandInfo(**data)
                    elif fname == "clients":
                        self._clients = {k: Client(**v) for k, v in data.items()}
                    elif fname == "products":
                        self._products = {k: Product(**v) for k, v in data.items()}
                    elif fname == "invoices":
                        self._invoices = {k: Invoice(**v) for k, v in data.items()}
                    else:
                        setattr(self, attr, data)
                except Exception:
                    pass

    def _save(self, name: str, data):
        with open(self._path(name), "w") as f:
            json.dump(data, f, indent=2, default=str)

    # ── Company ──
    def set_company(self, key: str, value: str):
        self._company[key] = value
        self._save("company", self._company)

    def get_company(self, key: str, default: str = "") -> str:
        return self._company.get(key, default)

    def set_company_bulk(self, data: dict[str, str]):
        self._company.update(data)
        self._save("company", self._company)

    def get_company_all(self) -> dict[str, str]:
        return dict(self._company)

    # ── Brand ──
    def set_brand(self, **kwargs):
        for k, v in kwargs.items():
            if hasattr(self._brand, k):
                setattr(self._brand, k, v)
        self._save("brand", self._brand.to_dict())

    def get_brand(self) -> BrandInfo:
        return self._brand

    def get_brand_css(self) -> str:
        return self._brand.to_css_vars()

    # ── Clients ──
    def add_client(self, name: str, company: str = "", email: str = "",
                   phone: str = "", status: str = "lead",
                   source: str = "", notes: str = "",
                   tags: list[str] | None = None) -> Client:
        import uuid
        cid = uuid.uuid4().hex[:12]
        client = Client(
            id=cid, name=name, company=company, email=email,
            phone=phone, status=status, source=source, notes=notes,
            tags=tags or [], created_at=time.time(),
        )
        self._clients[cid] = client
        self._save("clients", {k: v.to_dict() for k, v in self._clients.items()})
        return client

    def update_client(self, client_id: str, **kwargs) -> Client | None:
        client = self._clients.get(client_id)
        if not client:
            return None
        for k, v in kwargs.items():
            if hasattr(client, k):
                setattr(client, k, v)
        client.last_contact = time.time()
        self._save("clients", {k: v.to_dict() for k, v in self._clients.items()})
        return client

    def get_client(self, client_id: str) -> Client | None:
        return self._clients.get(client_id)

    def list_clients(self, status: str = "", limit: int = 50) -> list[Client]:
        clients = list(self._clients.values())
        if status:
            clients = [c for c in clients if c.status == status]
        return sorted(clients, key=lambda c: c.last_contact or 0, reverse=True)[:limit]

    def search_clients(self, query: str) -> list[Client]:
        q = query.lower()
        return [c for c in self._clients.values()
                if q in c.name.lower() or q in c.company.lower()
                or q in c.email.lower() or any(q in t for t in c.tags)]

    def delete_client(self, client_id: str) -> bool:
        if client_id in self._clients:
            del self._clients[client_id]
            self._save("clients", {k: v.to_dict() for k, v in self._clients.items()})
            return True
        return False

    def client_count(self) -> int:
        return len(self._clients)

    # ── Products ──
    def add_product(self, name: str, price: float, description: str = "",
                    category: str = "", tags: list[str] | None = None) -> Product:
        import uuid
        pid = uuid.uuid4().hex[:12]
        product = Product(id=pid, name=name, price=price,
                          description=description, category=category,
                          tags=tags or [])
        self._products[pid] = product
        self._save("products", {k: v.to_dict() for k, v in self._products.items()})
        return product

    def list_products(self, category: str = "") -> list[Product]:
        prods = list(self._products.values())
        if category:
            prods = [p for p in prods if p.category == category]
        return sorted(prods, key=lambda p: p.name)

    def delete_product(self, product_id: str) -> bool:
        if product_id in self._products:
            del self._products[product_id]
            self._save("products", {k: v.to_dict() for k, v in self._products.items()})
            return True
        return False

    # ── Invoices ──
    def create_invoice(self, client_id: str, items: list[dict],
                       notes: str = "", due_days: int = 30) -> Invoice | None:
        if client_id not in self._clients:
            return None
        import uuid
        iid = uuid.uuid4().hex[:12]
        subtotal = sum(item.get("price", 0) * item.get("quantity", 1)
                       for item in items)
        tax = round(subtotal * 0.1, 2)  # default 10%
        inv = Invoice(
            id=iid, client_id=client_id,
            number=f"INV-{int(time.time())}",
            date=time.strftime("%Y-%m-%d"),
            due_date=time.strftime("%Y-%m-%d",
                                   time.localtime(time.time() + due_days * 86400)),
            items=items, subtotal=subtotal, tax=tax,
            total=subtotal + tax, notes=notes,
        )
        self._invoices[iid] = inv
        self._save("invoices", {k: v.to_dict() for k, v in self._invoices.items()})

        client = self._clients[client_id]
        client.total_value += inv.total
        client.last_contact = time.time()
        self._save("clients", {k: v.to_dict() for k, v in self._clients.items()})

        return inv

    def list_invoices(self, status: str = "", client_id: str = "",
                      limit: int = 50) -> list[Invoice]:
        invs = list(self._invoices.values())
        if status:
            invs = [i for i in invs if i.status == status]
        if client_id:
            invs = [i for i in invs if i.client_id == client_id]
        return sorted(invs, key=lambda i: i.date, reverse=True)[:limit]

    def update_invoice_status(self, invoice_id: str, status: str) -> Invoice | None:
        inv = self._invoices.get(invoice_id)
        if inv:
            inv.status = status
            self._save("invoices", {k: v.to_dict() for k, v in self._invoices.items()})
        return inv

    # ── Templates ──
    def save_template(self, name: str, content: str):
        self._templates[name] = content
        self._save("templates", self._templates)

    def get_template(self, name: str) -> str:
        return self._templates.get(name, "")

    def fill_template(self, name: str, variables: dict[str, str] | None = None) -> str:
        template = self._templates.get(name, "")
        if not template:
            return ""
        all_vars = {**self._company}
        if variables:
            all_vars.update(variables)
        for key, value in all_vars.items():
            template = template.replace("{{" + key + "}}", str(value))
        return template

    def list_templates(self) -> list[str]:
        return sorted(self._templates.keys())

    # ── Social ──
    def set_social(self, platform: str, url: str):
        self._social[platform] = url
        self._save("social", self._social)

    def get_social(self, platform: str = "") -> dict[str, str]:
        if platform:
            return {platform: self._social.get(platform, "")}
        return dict(self._social)

    # ── Pricing ──
    def set_pricing(self, tier: str, price: float, currency: str = "USD",
                    features: list[str] | None = None):
        self._pricing[tier] = {"price": price, "currency": currency,
                               "features": features or []}
        self._save("pricing", self._pricing)

    def get_pricing(self, tier: str = "") -> dict:
        if tier:
            return self._pricing.get(tier, {})
        return dict(self._pricing)

    # ── AI Context Injection ──
    def build_context_prompt(self) -> str:
        """Generate a rich context prompt for the AI with all business knowledge."""
        parts = []

        if self._company:
            parts.append("## Company Information")
            for k, v in self._company.items():
                if v:
                    parts.append(f"- {k.replace('_', ' ').title()}: {v}")

        if self._brand.name:
            parts.append(f"\n## Brand\n"
                         f"- Name: {self._brand.name}\n"
                         f"- Tagline: {self._brand.tagline}\n"
                         f"- Colors: {self._brand.primary_color}, "
                         f"{self._brand.secondary_color}, {self._brand.accent_color}\n"
                         f"- Fonts: {self._brand.font_heading} / {self._brand.font_body}\n"
                         f"- Tone: {self._brand.tone}\n"
                         f"- Voice: {self._brand.voice}")

        if self._products:
            parts.append("\n## Products & Services")
            for p in list(self._products.values())[:10]:
                parts.append(f"- {p.name}: ${p.price:.2f} — {p.description[:100]}")

        if self._pricing:
            parts.append("\n## Pricing Tiers")
            for tier, info in self._pricing.items():
                parts.append(f"- {tier}: ${info['price']}/mo "
                             f"({', '.join(info.get('features', [])[:3])})")

        if self._clients:
            parts.append(f"\n## Client Summary ({len(self._clients)} total)")
            for c in list(self._clients.values())[:5]:
                parts.append(f"- {c.name} ({c.company}): {c.status}, ${c.total_value:.0f}")

        if self._social:
            parts.append("\n## Social Media Links")
            for platform, url in self._social.items():
                parts.append(f"- {platform}: {url}")

        if self._templates:
            parts.append(f"\n## Available Templates: {', '.join(self._templates.keys())}")

        return "\n".join(parts)

    def get_stats(self) -> dict:
        return {
            "company_fields": len(self._company),
            "brand_complete": bool(self._brand.name),
            "clients": len(self._clients),
            "products": len(self._products),
            "invoices": len(self._invoices),
            "templates": len(self._templates),
            "pricing_tiers": len(self._pricing),
            "social_links": len(self._social),
        }


business_memory = BusinessMemory()
