#!/usr/bin/env python3
"""Seed Lumina AI OS with demo data."""
import httpx
import sys
import time

BASE = "http://127.0.0.1:8000"
c = httpx.Client(base_url=BASE, timeout=10)


def log(label, resp):
    status = "✅" if resp.status_code in (200, 201) else "❌"
    print(f"  {status} {label} → {resp.status_code}")
    return resp


def main():
    print("\n🌱 Seeding Lumina AI OS with demo data...\n")

    # Wait for server
    for _ in range(10):
        try:
            r = c.get("/health")
            if r.status_code == 200:
                break
        except Exception:
            pass
        time.sleep(0.5)

    # 1. Create admin user
    log("Register admin", c.post("/api/auth/register", json={
        "username": "admin", "email": "admin@lumina.io",
        "password": "admin123", "full_name": "Lumina Admin",
    }))
    login = c.post("/api/auth/login", json={"username": "admin", "password": "admin123"})
    token = login.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    log("Login admin", login)

    # 2. Create demo leads
    leads = [
        {"company_name": "Al Noor Restaurant", "email": "info@alnoor.bh", "phone": "+97317123456", "industry": "Restaurant", "notes": "Needs website + online ordering"},
        {"company_name": "Bahrain Tech Solutions", "email": "ceo@bts.com", "phone": "+97317234567", "industry": "Technology", "notes": "Interested in CRM platform"},
        {"company_name": "Golden Pearl Hotel", "email": "gm@goldenpearl.com", "phone": "+97317345678", "industry": "Hospitality", "notes": "Wants SEO + booking system"},
        {"company_name": "Green Leaf Organic", "email": "owner@greenleaf.com", "phone": "+97317456789", "industry": "Retail", "notes": "Needs e-commerce platform"},
    ]
    for lead in leads:
        r = log(f"Lead: {lead['company_name']}", c.post("/api/crm/leads", json=lead, headers=headers))
        if r.status_code == 200:
            lead_id = r.json()["id"]
            c.put(f"/api/crm/pipeline/{lead_id}/move?to_stage=qualified", headers=headers)

    # 3. Create calendar events
    events = [
        {"title": "Client Meeting - Al Noor", "start": "2026-07-06T10:00:00", "end": "2026-07-06T11:00:00", "event_type": "meeting", "description": "Discuss website project"},
        {"title": "Proposal Review", "start": "2026-07-07T14:00:00", "end": "2026-07-07T15:00:00", "event_type": "internal", "description": "Review BTS proposal"},
        {"title": "Follow-up Call - Green Leaf", "start": "2026-07-08T09:00:00", "end": "2026-07-08T09:30:00", "event_type": "call", "description": "Quote follow-up"},
    ]
    for ev in events:
        log(f"Event: {ev['title']}", c.post("/api/crm/calendar", json=ev))

    # 4. Schedule follow-ups
    followups = [
        {"lead_id": "lead_1", "days": 3, "note": "Send proposal"},
        {"lead_id": "lead_2", "days": 5, "note": "Check on decision"},
        {"lead_id": "lead_3", "days": 7, "note": "Call back about SEO"},
    ]
    for fup in followups:
        log(f"Follow-up: {fup['note']}", c.post("/api/crm/followups", json=fup))

    # 5. Create proposals
    log("Proposal: Al Noor", c.post("/api/crm/proposals", json={
        "client": "Al Noor Restaurant",
        "scope": "Full website with online ordering system, SEO optimization, and mobile-responsive design",
        "pricing": "BHD 2,500",
        "timeline": "4 weeks",
    }))

    # 6. Create quotations
    log("Quotation: Green Leaf", c.post("/api/crm/quotations", json={
        "client": "Green Leaf Organic",
        "items": [
            {"description": "E-commerce Website Design", "qty": 1, "price": 1500},
            {"description": "Product Catalog Setup (50 items)", "qty": 1, "price": 500},
            {"description": "Payment Gateway Integration", "qty": 1, "price": 300},
            {"description": "Monthly SEO Maintenance", "qty": 3, "price": 200},
        ],
        "tax": 0.10,
        "discount": 0.05,
    }))

    # 7. Create client workspace
    log("Workspace: Al Noor", c.post("/api/crm/workspaces/Al%20Noor%20Restaurant", json={
        "name": "Ahmed Ali", "email": "ahmed@alnoor.bh", "phone": "+97317123456",
    }, headers=headers))
    log("Workspace note", c.post("/api/crm/workspaces/Al%20Noor%20Restaurant/notes", json={"company": "Al Noor Restaurant", "note": "Client prefers modern design with green theme"}, headers=headers))
    log("Workspace task", c.post("/api/crm/workspaces/Al%20Noor%20Restaurant/tasks", json={"company": "Al Noor Restaurant", "task": "Send wireframes by Friday"}, headers=headers))

    # 8. WhatsApp demo messages
    log("WhatsApp: Send demo", c.post("/api/whatsapp/send", json={"to": "+97317123456", "message": "Hi Ahmed, your website proposal is ready for review!"}, headers=headers))

    # 9. Email demo
    log("Email: Send demo", c.post("/api/email/send", json={"to": "ahmed@alnoor.bh", "subject": "Website Proposal - Al Noor Restaurant", "body": "Dear Ahmed,\n\nWe are pleased to submit our proposal for your new website...\n\nBest regards,\nLumina AI"}, headers=headers))

    # 10. Create a task
    log("Create task", c.post("/api/tasks/", json={
        "title": "Build Al Noor Restaurant website",
        "description": "Full website with online ordering",
        "priority": "high",
    }, headers=headers))

    print("\n✅ Seeding complete!\n")
    print(f"  Dashboard: {BASE}")
    print(f"  Login as:  admin / admin123")


if __name__ == "__main__":
    main()
