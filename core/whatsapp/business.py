"""WhatsApp Business Manager — catalog, products, and automation."""

from __future__ import annotations

import csv
import json
import os
import time
from dataclasses import dataclass, field
from typing import Any

from core.log import log


@dataclass
class Product:
    """A WhatsApp Business catalog product."""
    id: str = ""
    name: str = ""
    description: str = ""
    price: float = 0.0
    currency: str = "USD"
    image_url: str = ""
    category: str = ""
    sku: str = ""
    stock: int = 0
    status: str = "draft"


@dataclass
class Catalog:
    """A WhatsApp Business catalog."""
    id: str = ""
    name: str = ""
    products: list[Product] = field(default_factory=list)
    created: float = field(default_factory=time.time)


class WhatsAppBusinessManager:
    """Manage WhatsApp Business catalog, products, and automation."""

    def __init__(self, storage_path: str = "whatsapp_business.json"):
        self.storage_path = storage_path
        self._products: dict[str, Product] = {}
        self._catalogs: dict[str, Catalog] = {}
        self._load()

    def _load(self) -> None:
        if not os.path.exists(self.storage_path):
            return
        try:
            with open(self.storage_path) as f:
                data = json.load(f)
            for p in data.get("products", []):
                self._products[p["id"]] = Product(**p)
            for c in data.get("catalogs", []):
                self._catalogs[c["id"]] = Catalog(**c)
        except Exception as e:
            log.error("Failed to load WhatsApp Business data: %s", e)

    def _save(self) -> None:
        with open(self.storage_path, "w") as f:
            json.dump({
                "products": [p.__dict__ for p in self._products.values()],
                "catalogs": [c.__dict__ for c in self._catalogs.values()],
            }, f, indent=2)

    # ── Products ──

    def add_product(self, name: str, description: str = "", price: float = 0.0,
                    image_url: str = "", category: str = "", sku: str = "",
                    stock: int = 0) -> Product:
        pid = f"prod_{int(time.time())}_{len(self._products)}"
        product = Product(
            id=pid, name=name, description=description, price=price,
            image_url=image_url, category=category, sku=sku, stock=stock,
        )
        self._products[pid] = product
        self._save()
        log.info("Product added: %s ($%.2f)", name, price)
        return product

    def update_product(self, product_id: str, **kwargs: Any) -> Product | None:
        product = self._products.get(product_id)
        if not product:
            return None
        for key, value in kwargs.items():
            if hasattr(product, key):
                setattr(product, key, value)
        self._save()
        return product

    def delete_product(self, product_id: str) -> bool:
        if product_id in self._products:
            del self._products[product_id]
            self._save()
            return True
        return False

    def get_product(self, product_id: str) -> Product | None:
        return self._products.get(product_id)

    def list_products(self, category: str = "", status: str = "") -> list[Product]:
        results = list(self._products.values())
        if category:
            results = [p for p in results if p.category == category]
        if status:
            results = [p for p in results if p.status == status]
        return results

    def product_count(self) -> int:
        return len(self._products)

    # ── Bulk Import ──

    def import_csv(self, path: str) -> int:
        """Import products from a CSV file."""
        count = 0
        with open(path, newline="", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                try:
                    price = float(row.get("price", 0))
                except ValueError:
                    price = 0.0
                self.add_product(
                    name=row.get("name", ""),
                    description=row.get("description", ""),
                    price=price,
                    image_url=row.get("image_url", ""),
                    category=row.get("category", ""),
                    sku=row.get("sku", ""),
                    stock=int(row.get("stock", 0)),
                )
                count += 1
        self._save()
        log.info("Imported %d products from CSV", count)
        return count

    def export_csv(self, path: str = "products_export.csv") -> str:
        """Export all products to CSV."""
        with open(path, "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow(["name", "description", "price", "currency", "image_url",
                            "category", "sku", "stock", "status"])
            for p in self._products.values():
                writer.writerow([p.name, p.description, p.price, p.currency,
                                p.image_url, p.category, p.sku, p.stock, p.status])
        log.info("Exported %d products to CSV", len(self._products))
        return path

    # ── Statistics ──

    def get_stats(self) -> dict:
        products = self._products.values()
        total = len(products)
        total_value = sum(p.price for p in products)
        by_category: dict[str, int] = {}
        for p in products:
            by_category[p.category] = by_category.get(p.category, 0) + 1
        return {
            "total_products": total,
            "total_value": total_value,
            "avg_price": round(total_value / total, 2) if total else 0,
            "by_category": by_category,
            "drafts": sum(1 for p in products if p.status == "draft"),
            "published": sum(1 for p in products if p.status == "published"),
        }

    # ── Automation via Browser Agent ──

    async def auto_upload_products(self, headless: bool = False) -> dict:
        """Use Browser Agent to log into WhatsApp Business and upload products."""
        from core.browser.agent import browser_agent
        if not self._products:
            return {"error": "No products to upload"}

        products = list(self._products.values())[:5]  # Upload first 5
        task = "Go to business.facebook.com, log into WhatsApp Business Manager, navigate to the catalog section, add the following products one by one:\n"
        for p in products:
            task += f"- Product: {p.name}, Price: ${p.price}, Description: {p.description[:100]}\n"
        task += "For each product, click 'Add Product', fill in the name, description, price, upload image if available, and save."

        result = await browser_agent.execute(task, headless=headless)
        for p in products:
            p.status = "published"
        self._save()
        return result


waba = WhatsAppBusinessManager()
