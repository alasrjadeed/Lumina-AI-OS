"""WhatsApp API — messaging, templates, and Business Manager."""

from fastapi import APIRouter
from pydantic import BaseModel

from core.whatsapp.client import whatsapp
from core.whatsapp.business import waba

router = APIRouter(prefix="/whatsapp", tags=["WhatsApp"])


class TextMessage(BaseModel):
    to: str
    text: str


class TemplateMessage(BaseModel):
    to: str
    template_name: str
    params: list[str] = []


class MediaMessage(BaseModel):
    to: str
    url: str
    caption: str = ""


class ProductCreate(BaseModel):
    name: str
    description: str = ""
    price: float = 0.0
    image_url: str = ""
    category: str = ""
    sku: str = ""
    stock: int = 0


@router.get("/status")
async def status():
    return {
        "configured": bool(whatsapp.api_key and whatsapp.phone_number_id),
        "has_api_key": bool(whatsapp.api_key),
        "has_phone_id": bool(whatsapp.phone_number_id),
        "products": waba.product_count(),
    }


@router.post("/send/text")
async def send_text(req: TextMessage):
    return await whatsapp.send_text(req.to, req.text)


@router.post("/send/template")
async def send_template(req: TemplateMessage):
    return await whatsapp.send_template(req.to, req.template_name, req.params)


@router.post("/send/image")
async def send_image(req: MediaMessage):
    return await whatsapp.send_image(req.to, req.url, req.caption)


@router.post("/send/document")
async def send_document(req: MediaMessage):
    return await whatsapp.send_document(req.to, req.url, req.caption)


@router.get("/templates")
async def list_templates():
    return {"templates": await whatsapp.get_templates()}


# ── WhatsApp Business Manager ──


@router.get("/business/stats")
async def business_stats():
    return waba.get_stats()


@router.get("/business/products")
async def list_products(category: str = "", status: str = ""):
    products = waba.list_products(category, status)
    return {
        "products": [
            {"id": p.id, "name": p.name, "description": p.description[:100],
             "price": p.price, "currency": p.currency, "image_url": p.image_url,
             "category": p.category, "status": p.status}
            for p in products
        ],
        "total": len(products),
    }


@router.post("/business/products")
async def create_product(req: ProductCreate):
    p = waba.add_product(req.name, req.description, req.price, req.image_url, req.category, req.sku, req.stock)
    return {"id": p.id, "name": p.name, "price": p.price}


@router.delete("/business/products/{product_id}")
async def delete_product(product_id: str):
    return {"deleted": waba.delete_product(product_id)}


@router.post("/business/import")
async def import_csv(path: str):
    count = waba.import_csv(path)
    return {"imported": count}


@router.get("/business/export")
async def export_csv():
    path = waba.export_csv()
    return {"path": path, "count": waba.product_count()}


@router.post("/business/auto-upload")
async def auto_upload(headless: bool = False):
    result = await waba.auto_upload_products(headless=headless)
    return result
