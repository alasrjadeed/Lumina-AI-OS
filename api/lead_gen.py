from __future__ import annotations

import csv
import io
from dataclasses import asdict
from typing import Any

from fastapi import APIRouter, File, HTTPException, Query, UploadFile
from pydantic import BaseModel, Field

from core.lead_generation import (
    ApifyClient,
    LeadPersistenceService,
    LeadScraperService,
    PlatformRegistry,
    ScraperHealthCheck,
)
from core.lead_generation.ai_services import LeadScoringService, OutreachService
from core.lead_generation.models import LeadCategory, LeadRecord
from core.log import log

router = APIRouter(prefix="/lead-gen", tags=["Lead Generation"])

_persistence = LeadPersistenceService()
_platform_registry = PlatformRegistry()
_apify_client = ApifyClient()
_scraper = LeadScraperService(
    apify_client=_apify_client,
    persistence=_persistence,
    registry=_platform_registry,
)
_health = ScraperHealthCheck(_persistence)
_scoring = LeadScoringService()
_outreach = OutreachService()


class GenerateRequest(BaseModel):
    keyword: str = Field(..., min_length=1, max_length=200)
    location: str = Field(default="Bahrain", max_length=100)
    platforms: list[str] | None = None
    limit: int = Field(default=10, ge=1, le=100)
    category_name: str = ""


class BulkGenerateRequest(BaseModel):
    keyword: str = Field(..., min_length=1, max_length=200)
    location: str = Field(default="Bahrain", max_length=100)
    category_name: str = ""
    limit: int = Field(default=10, ge=1, le=100)


class CategoryGenerateRequest(BaseModel):
    category_id: str | None = None
    keyword: str = ""
    location: str = ""
    platforms: list[str] | None = None
    limit: int = Field(default=10, ge=1, le=100)


class OutreachRequest(BaseModel):
    lead_ids: list[str]
    channel: str = "email"
    subject: str = ""
    message: str = ""


def get_scraper() -> LeadScraperService:
    from config.settings import settings
    token = settings.apify_api_token
    if token:
        _apify_client.set_tokens([t.strip() for t in token.split(",") if t.strip()])
    return _scraper


@router.get("/dashboard")
async def dashboard():
    persistence = get_persistence()
    analytics = persistence.get_analytics()
    health = _health.get_summary()
    categories = persistence.get_categories()
    return {
        "analytics": analytics,
        "scraper_health": health,
        "categories": categories[:10],
        "total_leads": persistence.count(),
    }


@router.post("/generate")
async def generate_leads(req: GenerateRequest):
    scraper = get_scraper()
    result = await scraper.generate_leads(
        keyword=req.keyword,
        location=req.location,
        platforms=req.platforms,
        limit=req.limit,
        category_name=req.category_name,
    )
    return result


@router.post("/quick-generate")
async def quick_generate(req: GenerateRequest):
    return await generate_leads(req)


@router.post("/bulk-generate")
async def bulk_generate(req: BulkGenerateRequest):
    scraper = get_scraper()
    result = await scraper.generate_bulk(
        keyword=req.keyword,
        location=req.location,
        category_name=req.category_name,
        limit=req.limit,
    )
    return result


@router.post("/generate-category")
async def generate_category(req: CategoryGenerateRequest):
    scraper = get_scraper()
    persistence = get_persistence()

    if req.category_id:
        categories = persistence.get_categories()
        category = next((c for c in categories if c.id == req.category_id), None)
        if not category:
            raise HTTPException(404, f"Category not found: {req.category_id}")
    else:
        category = LeadCategory(
            name=req.keyword or "custom",
            keywords=[req.keyword] if req.keyword else ["general"],
            platforms=req.platforms or [],
            country_code=req.location or "BH",
            lead_limit=req.limit,
        )

    result = await scraper.generate_for_category(category, req.location)
    return result


@router.get("/leads")
async def list_leads(
    status: str = "",
    source: str = "",
    category: str = "",
    country: str = "",
    lead_type: str = "",
    search: str = "",
    limit: int = Query(default=100, le=500),
    offset: int = 0,
):
    persistence = get_persistence()
    has_filters = bool(status or source or category or country or lead_type)
    if search:
        leads = persistence.search_leads(search, limit)
        total = len(leads)
    elif has_filters:
        total = persistence.count_leads(
            status=status, source=source, category=category,
            country=country, lead_type=lead_type,
        )
        leads = persistence.get_leads(
            status=status, source=source, category=category,
            country=country, lead_type=lead_type, limit=limit, offset=offset,
        )
    else:
        leads = persistence.get_leads(limit=limit, offset=offset)
        total = persistence.count()
    return {
        "leads": [lead.to_dict() for lead in leads],
        "total": total,
        "limit": limit,
        "offset": offset,
    }


@router.get("/leads/{lead_id}")
async def get_lead(lead_id: str):
    persistence = get_persistence()
    lead = persistence.get_lead(lead_id)
    if not lead:
        raise HTTPException(404, "Lead not found")
    return asdict(lead)


@router.put("/leads/{lead_id}")
async def update_lead(lead_id: str, updates: dict[str, Any]):
    persistence = get_persistence()
    lead = persistence.update_lead(lead_id, **updates)
    if not lead:
        raise HTTPException(404, "Lead not found")
    return asdict(lead)


@router.delete("/leads/{lead_id}")
async def delete_lead(lead_id: str):
    persistence = get_persistence()
    if not persistence.delete_lead(lead_id):
        raise HTTPException(404, "Lead not found")
    return {"deleted": True}


@router.post("/leads/{lead_id}/enrich")
async def enrich_lead(lead_id: str):
    scraper = get_scraper()
    result = await scraper.enrich_lead(lead_id)
    if not result:
        raise HTTPException(404, "Lead not found")
    return result


@router.post("/leads/{lead_id}/status")
async def update_lead_status(lead_id: str, status: str = Query(...)):
    persistence = get_persistence()
    if not persistence.update_status(lead_id, status):
        raise HTTPException(404, "Lead not found")
    return {"lead_id": lead_id, "status": status}


@router.post("/bulk-update-status")
async def bulk_update_status(lead_ids: list[str], status: str = Query(...)):
    persistence = get_persistence()
    count = persistence.bulk_update_status(lead_ids, status)
    return {"updated": count}


@router.post("/bulk-delete-leads")
async def bulk_delete(lead_ids: list[str]):
    persistence = get_persistence()
    count = persistence.bulk_delete(lead_ids)
    return {"deleted": count}


@router.post("/outreach")
async def send_outreach(req: OutreachRequest):
    persistence = get_persistence()
    results = []
    for lead_id in req.lead_ids:
        lead = persistence.get_lead(lead_id)
        if not lead:
            results.append({"lead_id": lead_id, "status": "not_found"})
            continue
        results.append({"lead_id": lead_id, "status": "sent", "channel": req.channel})
    return {"results": results}


@router.get("/export-csv")
async def export_csv(
    lead_ids: str = "",
    status: str = "",
    source: str = "",
    limit: int = Query(default=500, le=5000),
):
    persistence = get_persistence()
    ids = [i.strip() for i in lead_ids.split(",") if i.strip()] if lead_ids else []

    if ids:
        leads = [persistence.get_lead(lid) for lid in ids]
        leads = [l for l in leads if l]
    else:
        leads = persistence.get_leads(status=status, source=source, limit=limit)

    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["ID", "Business Name", "Email", "Phone", "Website", "Source", "Category", "Country", "Type", "Score", "Status"])
    for lead in leads:
        writer.writerow([
            lead.id, lead.business_name, lead.email, lead.phone, lead.website,
            lead.source, lead.category, lead.country, lead.lead_type, lead.lead_score, lead.status,
        ])

    from fastapi.responses import StreamingResponse
    output.seek(0)
    return StreamingResponse(
        iter([output.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=leads_export.csv"},
    )


@router.get("/export-vcard")
async def export_vcard(lead_ids: str = "", limit: int = Query(default=100, le=500)):
    persistence = get_persistence()
    ids = [i.strip() for i in lead_ids.split(",") if i.strip()] if lead_ids else []

    if ids:
        leads = [persistence.get_lead(lid) for lid in ids]
        leads = [l for l in leads if l]
    else:
        leads = persistence.get_leads(limit=limit)

    vcards = []
    for lead in leads:
        vcard = f"""BEGIN:VCARD
VERSION:3.0
FN:{lead.business_name}
ORG:{lead.business_name}
EMAIL:{lead.email}
TEL:{lead.phone}
URL:{lead.website}
NOTE:Source: {lead.source} | Score: {lead.lead_score}
END:VCARD"""
        vcards.append(vcard)

    from fastapi.responses import PlainTextResponse
    return PlainTextResponse(
        "\n".join(vcards),
        media_type="text/vcard",
        headers={"Content-Disposition": "attachment; filename=leads_export.vcf"},
    )


@router.post("/import-csv")
async def import_csv(file: UploadFile = File(...)):
    persistence = get_persistence()
    content = await file.read()
    text = content.decode("utf-8", errors="ignore")
    reader = csv.DictReader(io.StringIO(text))

    leads = []
    for row in reader:
        leads.append({
            "business_name": row.get("Business Name") or row.get("business_name") or row.get("name", ""),
            "email": row.get("Email") or row.get("email", ""),
            "phone": row.get("Phone") or row.get("phone", ""),
            "website": row.get("Website") or row.get("website", ""),
            "source": "csv_import",
            "category": row.get("Category") or row.get("category", ""),
            "country": row.get("Country") or row.get("country", ""),
        })

    saved = persistence.save_leads(leads, category_name="csv_import")
    return {"imported": len(leads), "saved": saved}


@router.get("/categories")
async def list_categories():
    persistence = get_persistence()
    return {"categories": [asdict(c) for c in persistence.get_categories()]}


@router.post("/categories")
async def create_category(category: LeadCategory):
    persistence = get_persistence()
    saved = persistence.save_category(category)
    return asdict(saved)


@router.put("/categories/{category_id}")
async def update_category(category_id: str, updates: dict[str, Any]):
    persistence = get_persistence()
    cats = persistence.get_categories()
    cat = next((c for c in cats if c.id == category_id), None)
    if not cat:
        raise HTTPException(404, "Category not found")
    for key, value in updates.items():
        if hasattr(cat, key):
            setattr(cat, key, value)
    persistence.save_category(cat)
    return asdict(cat)


@router.delete("/categories/{category_id}")
async def delete_category(category_id: str):
    persistence = get_persistence()
    if not persistence.delete_category(category_id):
        raise HTTPException(404, "Category not found")
    return {"deleted": True}


@router.get("/platforms")
async def list_platforms(category: str = ""):
    if category:
        platforms = _platform_registry.by_category(category)
    else:
        platforms = _platform_registry.all_platforms()
    return {"platforms": [asdict(p) for p in platforms]}


@router.get("/countries")
async def list_countries():
    return {"countries": [asdict(c) for c in _platform_registry.countries()]}


@router.get("/country-platforms")
async def country_platforms(country: str = Query(...)):
    platforms = _platform_registry.for_country(country)
    return {"country": country, "platforms": platforms}


@router.get("/health")
async def scraper_health():
    return _health.get_summary()


@router.get("/errors")
async def scraper_errors(limit: int = 50):
    persistence = get_persistence()
    errors = persistence.get_errors(limit)
    return {"errors": [asdict(e) for e in errors]}


@router.post("/categories/{category_id}/generate")
async def generate_from_category(category_id: str, location: str = ""):
    scraper = get_scraper()
    persistence = get_persistence()
    cats = persistence.get_categories()
    category = next((c for c in cats if c.id == category_id), None)
    if not category:
        raise HTTPException(404, "Category not found")
    return await scraper.generate_for_category(category, location)


# ── AI Operations ──

class ScoreRequest(BaseModel):
    lead_ids: list[str]

class OutreachDraftRequest(BaseModel):
    lead_id: str
    language: str = "en"

class EmailSendRequest(BaseModel):
    lead_id: str
    subject: str
    message: str


@router.post("/leads/{lead_id}/ai-score")
async def ai_score_lead(lead_id: str):
    persistence = get_persistence()
    lead = persistence.get_lead(lead_id)
    if not lead:
        raise HTTPException(404, "Lead not found")
    score = await _scoring.score_lead(lead)
    persistence.update_lead(lead_id, lead_score=score)
    return {"lead_id": lead_id, "lead_score": score, "tier": LeadRecord(**{**asdict(lead), "lead_score": score}).score_tier}


@router.post("/batch-ai-score")
async def batch_ai_score(req: ScoreRequest):
    if not req.lead_ids:
        raise HTTPException(400, "No lead IDs provided")
    persistence = get_persistence()
    leads = [persistence.get_lead(lid) for lid in req.lead_ids]
    leads = [l for l in leads if l]
    result = await _scoring.batch_score(leads)
    for lead in leads:
        persistence.update_lead(lead.id, lead_score=lead.lead_score)
    return result


@router.post("/generate-email-draft")
async def generate_email_draft(req: OutreachDraftRequest):
    persistence = get_persistence()
    lead = persistence.get_lead(req.lead_id)
    if not lead:
        raise HTTPException(404, "Lead not found")
    draft = await _outreach.generate_email(lead, req.language)
    return {"lead_id": req.lead_id, "draft": draft, "language": req.language}


@router.post("/generate-whatsapp-draft")
async def generate_whatsapp_draft(req: OutreachDraftRequest):
    persistence = get_persistence()
    lead = persistence.get_lead(req.lead_id)
    if not lead:
        raise HTTPException(404, "Lead not found")
    draft = await _outreach.generate_whatsapp(lead, req.language)
    return {"lead_id": req.lead_id, "draft": draft, "language": req.language}


# ── Outreach Sending ──

@router.post("/send-outreach-email")
async def send_outreach_email(req: EmailSendRequest):
    persistence = get_persistence()
    lead = persistence.get_lead(req.lead_id)
    if not lead:
        raise HTTPException(404, "Lead not found")
    if not lead.email:
        raise HTTPException(400, "Lead has no email address")

    from core.plugins.email_automation import send_email
    ok = send_email(lead.email, req.subject, req.message, is_html=False)
    if ok:
        log.info("Outreach email sent to: %s (%s)", lead.business_name, lead.email)
        persistence.update_lead(lead.id, outreach_count=lead.outreach_count + 1, last_contacted_at=__import__("time").time())

    return {"sent": ok, "lead_id": req.lead_id, "to": lead.email, "subject": req.subject}


@router.post("/bulk-send-outreach")
async def bulk_send_outreach(req: OutreachRequest):
    persistence = get_persistence()
    from core.plugins.email_automation import send_email
    results = []
    for lead_id in req.lead_ids:
        lead = persistence.get_lead(lead_id)
        if not lead or not lead.email:
            results.append({"lead_id": lead_id, "status": "skipped"})
            continue
        ok = send_email(lead.email, req.subject or f'Partnership Opportunity for {lead.business_name}', req.message)
        if ok:
            log.info("Outreach email sent to: %s (%s)", lead.business_name, lead.email)
            persistence.update_lead(lead.id, outreach_count=lead.outreach_count + 1, last_contacted_at=__import__("time").time())
        results.append({"lead_id": lead_id, "status": "sent" if ok else "failed", "to": lead.email})
    return {"results": results}


@router.post("/send-custom-email")
async def send_custom_email(req: dict[str, Any]):
    to_email = req.get("email", "")
    subject = req.get("subject", "")
    message = req.get("message", "")
    if not to_email or not subject:
        raise HTTPException(400, "email and subject required")
    from core.plugins.email_automation import send_email
    ok = send_email(to_email, subject, message, is_html=req.get("is_html", False))
    return {"sent": ok, "to": to_email}


# ── Import Operations ──

@router.post("/import-vcard")
async def import_vcard(file: UploadFile = File(...)):
    persistence = get_persistence()
    content = await file.read()
    text = content.decode("utf-8", errors="ignore")

    leads = []
    current: dict[str, str] = {}
    for line in text.split("\n"):
        line = line.strip()
        if line.startswith("BEGIN:VCARD"):
            current = {}
        elif line.startswith("END:VCARD"):
            if current.get("business_name") or current.get("name"):
                leads.append({
                    "business_name": current.get("business_name") or current.get("name", ""),
                    "email": current.get("email", ""),
                    "phone": current.get("phone", ""),
                    "website": current.get("website", ""),
                    "source": "vcard_import",
                    "contact_person": current.get("name", ""),
                    "notes": current.get("note", ""),
                })
        elif line.startswith("FN:") or line.startswith("ORG:"):
            val = line.split(":", 1)[1] if ":" in line else ""
            if line.startswith("FN:"):
                current["name"] = val
            else:
                current["business_name"] = val
        elif line.startswith("EMAIL"):
            val = line.split(":", 1)[1] if ":" in line else ""
            current["email"] = val
        elif line.startswith("TEL"):
            val = line.split(":", 1)[1] if ":" in line else ""
            current["phone"] = val
        elif line.startswith("URL:") or line.startswith("URL;"):
            val = line.split(":", 1)[1] if ":" in line else ""
            current["website"] = val
        elif line.startswith("NOTE:"):
            current["note"] = line[5:]

    saved = persistence.save_leads(leads, category_name="vcard_import")
    return {"imported": len(leads), "saved": saved}


@router.post("/import-whatsapp-group")
async def import_whatsapp_group(
    file: UploadFile = File(...),
    group_name: str = "",
):
    persistence = get_persistence()
    content = await file.read()
    text = content.decode("utf-8", errors="ignore")

    leads = []
    reader = csv.reader(io.StringIO(text))
    header = next(reader, None)
    name_idx = 0
    phone_idx = 1
    if header:
        for i, col in enumerate(header):
            col_lower = col.strip().lower()
            if col_lower in ("name", "contact", "contact_name", "nombre"):
                name_idx = i
            elif col_lower in ("phone", "mobile", "number", "phone_number", "telefono"):
                phone_idx = i

    for row in reader:
        if not row or len(row) < 2:
            continue
        name = row[name_idx].strip() if name_idx < len(row) else ""
        phone = row[phone_idx].strip() if phone_idx < len(row) else ""
        if not phone:
            continue
        phone = phone.replace(" ", "").replace("-", "")
        if not phone.startswith("+"):
            phone = f"+{phone}"
        leads.append({
            "business_name": name or f"WhatsApp Contact {phone}",
            "phone": phone,
            "source": "whatsapp_import",
            "contact_person": name,
        })

    saved = persistence.save_leads(leads, category_name=f"whatsapp_{group_name}" if group_name else "whatsapp_import")
    return {
        "imported": len(leads),
        "saved": saved,
        "group_name": group_name,
    }


def get_persistence() -> LeadPersistenceService:
    return _persistence
