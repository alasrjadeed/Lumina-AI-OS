import json
import os
from datetime import datetime
from enum import Enum

from core.log import log


class DealStage(Enum):
    LEAD = "lead"
    QUALIFIED = "qualified"
    PROPOSAL = "proposal"
    NEGOTIATION = "negotiation"
    CLOSED_WON = "closed_won"
    CLOSED_LOST = "closed_lost"


_BASE = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
CRM_FILE = os.path.join(_BASE, "crm_data.json")


class CRMPipeline:
    def __init__(self):
        self._data = self._load()

    def _load(self) -> dict:
        if os.path.exists(CRM_FILE):
            with open(CRM_FILE) as f:
                return json.load(f)
        return {"contacts": [], "deals": [], "activities": [], "notes": []}

    def _save(self):
        with open(CRM_FILE, "w") as f:
            json.dump(self._data, f, indent=2)

    def add_contact(
        self, name: str, email: str = "", phone: str = "", company: str = "", **extra
    ) -> dict:
        contact = {
            "id": str(len(self._data["contacts"]) + 1),
            "name": name,
            "email": email,
            "phone": phone,
            "company": company,
            "source": extra.get("source", "manual"),
            "created_at": datetime.now().isoformat(),
            "tags": extra.get("tags", []),
            **extra,
        }
        self._data["contacts"].append(contact)
        self._save()
        log.info("CRM contact added: %s", name)
        return contact

    def list_contacts(self, search: str = "") -> list[dict]:
        contacts = self._data["contacts"]
        if search:
            s = search.lower()
            contacts = [
                c for c in contacts
                if s in c["name"].lower() or s in c.get("email", "").lower()
            ]
        return contacts

    def add_deal(
        self, title: str, value: float, contact_id: str, stage: DealStage = DealStage.LEAD
    ) -> dict:
        deal = {
            "id": str(len(self._data["deals"]) + 1),
            "title": title,
            "value": value,
            "contact_id": contact_id,
            "stage": stage.value,
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat(),
        }
        self._data["deals"].append(deal)
        self._save()
        log.info("CRM deal added: %s ($%.2f)", title, value)
        return deal

    def list_deals(self, stage: str | None = None) -> list[dict]:
        deals = self._data["deals"]
        if stage:
            deals = [d for d in deals if d["stage"] == stage]
        return deals

    def update_deal_stage(self, deal_id: str, stage: DealStage):
        for deal in self._data["deals"]:
            if deal["id"] == deal_id:
                deal["stage"] = stage.value
                deal["updated_at"] = datetime.now().isoformat()
                self._save()
                log.info("Deal %s moved to %s", deal_id, stage.value)
                return deal
        return None

    def get_sales_summary(self) -> dict:
        deals = self._data["deals"]
        total = sum(d["value"] for d in deals)
        won = sum(d["value"] for d in deals if d["stage"] == DealStage.CLOSED_WON.value)
        lost = sum(d["value"] for d in deals if d["stage"] == DealStage.CLOSED_LOST.value)
        pipeline = sum(
            d["value"] for d in deals
            if d["stage"] not in (DealStage.CLOSED_WON.value, DealStage.CLOSED_LOST.value)
        )
        return {
            "total_deals": len(deals),
            "total_contacts": len(self._data["contacts"]),
            "total_value": total,
            "won_value": won,
            "lost_value": lost,
            "pipeline_value": pipeline,
            "conversion_rate": f"{(won / total * 100) if total > 0 else 0:.1f}%",
        }

    def add_activity(self, contact_id: str, activity_type: str, description: str) -> dict:
        activity = {
            "id": str(len(self._data["activities"]) + 1),
            "contact_id": contact_id,
            "type": activity_type,
            "description": description,
            "timestamp": datetime.now().isoformat(),
        }
        self._data["activities"].append(activity)
        self._save()
        return activity


crm = CRMPipeline()
