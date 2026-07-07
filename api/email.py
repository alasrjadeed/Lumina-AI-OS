"""Email automation API routes."""

from fastapi import APIRouter
from pydantic import BaseModel

from core.plugins.email_automation import (
    configure_smtp,
    create_campaign,
    create_template,
    delete_campaign,
    delete_template,
    get_smtp_config,
    import_recipients,
    list_campaigns,
    list_templates,
    run_campaign,
    send_email,
)

router = APIRouter(prefix="/email", tags=["Email"])


class SMTPConfig(BaseModel):
    host: str
    port: int
    username: str
    password: str
    use_tls: bool = True


class TemplateCreate(BaseModel):
    name: str
    subject: str
    body: str
    is_html: bool = False


class CampaignCreate(BaseModel):
    name: str
    template: str
    recipients: list[str]


class SendRequest(BaseModel):
    to: str
    subject: str
    body: str
    is_html: bool = False


@router.get("/smtp")
async def get_config():
    return get_smtp_config()


@router.post("/smtp")
async def set_config(req: SMTPConfig):
    configure_smtp(req.host, req.port, req.username, req.password, req.use_tls)
    return {"status": "ok"}


@router.get("/templates")
async def templates():
    return {"templates": [{"name": t.name, "subject": t.subject, "is_html": t.is_html,
                           "variables": t.variables} for t in list_templates()]}


@router.post("/templates")
async def create_template_route(req: TemplateCreate):
    t = create_template(req.name, req.subject, req.body, req.is_html)
    return {"name": t.name, "subject": t.subject, "variables": t.variables}


@router.delete("/templates/{name}")
async def delete_template_route(name: str):
    return {"deleted": delete_template(name)}


@router.get("/campaigns")
async def campaigns():
    return {"campaigns": [{"name": c.name, "template": c.template,
                           "recipients_count": len(c.recipients),
                           "sent": c.sent, "failed": c.failed, "status": c.status}
                          for c in list_campaigns()]}


@router.post("/campaigns")
async def create_campaign_route(req: CampaignCreate):
    c = create_campaign(req.name, req.template, req.recipients)
    return {"name": c.name, "recipients": len(c.recipients), "status": c.status}


@router.delete("/campaigns/{name}")
async def delete_campaign_route(name: str):
    return {"deleted": delete_campaign(name)}


@router.post("/campaigns/{name}/run")
async def run_campaign_route(name: str):
    result = await run_campaign(name)
    return result


@router.post("/send")
async def send(req: SendRequest):
    ok = send_email(req.to, req.subject, req.body, req.is_html)
    return {"success": ok}


@router.post("/campaigns/{name}/import")
async def import_csv(name: str, csv_path: str, email_column: str = "email"):
    count = import_recipients(name, csv_path, email_column)
    return {"imported": count}
