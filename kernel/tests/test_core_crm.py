from __future__ import annotations

from pathlib import Path

import pytest

from core.crm.pipeline import CRMPipeline, DealStage


@pytest.fixture
def crm(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> CRMPipeline:
    crm_path = str(tmp_path / "crm_data.json")
    monkeypatch.setattr("core.crm.pipeline.CRM_FILE", crm_path)
    return CRMPipeline()


class TestCRMPipeline:
    def test_add_contact(self, crm: CRMPipeline):
        contact = crm.add_contact("Alice", "alice@test.com", "1234567890", "Acme Inc")
        assert contact["name"] == "Alice"
        assert contact["email"] == "alice@test.com"

    def test_add_contact_with_tags(self, crm: CRMPipeline):
        contact = crm.add_contact("Bob", tags=["vip", "partner"])
        assert "vip" in contact["tags"]

    def test_add_contact_with_extra(self, crm: CRMPipeline):
        contact = crm.add_contact("Charlie", source="website", custom_field="yes")
        assert contact["source"] == "website"
        assert contact["custom_field"] == "yes"

    def test_list_contacts_empty(self, crm: CRMPipeline):
        assert crm.list_contacts() == []

    def test_list_contacts_all(self, crm: CRMPipeline):
        crm.add_contact("Alice")
        crm.add_contact("Bob")
        assert len(crm.list_contacts()) == 2

    def test_list_contacts_search_name(self, crm: CRMPipeline):
        crm.add_contact("Alice Smith")
        crm.add_contact("Bob Jones")
        results = crm.list_contacts(search="alice")
        assert len(results) == 1
        assert results[0]["name"] == "Alice Smith"

    def test_list_contacts_search_email(self, crm: CRMPipeline):
        crm.add_contact("Alice", email="alice@test.com")
        crm.add_contact("Bob", email="bob@test.com")
        results = crm.list_contacts(search="alice@")
        assert len(results) == 1

    def test_add_deal(self, crm: CRMPipeline):
        crm.add_contact("Alice")
        deal = crm.add_deal("Big Deal", 50000, "1")
        assert deal["title"] == "Big Deal"
        assert deal["value"] == 50000
        assert deal["stage"] == "lead"

    def test_add_deal_custom_stage(self, crm: CRMPipeline):
        crm.add_contact("Alice")
        deal = crm.add_deal("Proposal Deal", 10000, "1", DealStage.PROPOSAL)
        assert deal["stage"] == "proposal"

    def test_list_deals_empty(self, crm: CRMPipeline):
        assert crm.list_deals() == []

    def test_list_deals_filter_stage(self, crm: CRMPipeline):
        crm.add_contact("Alice")
        crm.add_deal("Won Deal", 5000, "1", DealStage.CLOSED_WON)
        crm.add_deal("Lost Deal", 3000, "1", DealStage.CLOSED_LOST)
        crm.add_deal("Open Deal", 2000, "1", DealStage.QUALIFIED)
        won = crm.list_deals(stage="closed_won")
        assert len(won) == 1
        assert won[0]["title"] == "Won Deal"

    def test_update_deal_stage(self, crm: CRMPipeline):
        crm.add_contact("Alice")
        deal = crm.add_deal("Moving Deal", 5000, "1")
        updated = crm.update_deal_stage(deal["id"], DealStage.QUALIFIED)
        assert updated is not None
        assert updated["stage"] == "qualified"

    def test_update_deal_stage_not_found(self, crm: CRMPipeline):
        assert crm.update_deal_stage("nonexistent", DealStage.CLOSED_WON) is None

    def test_get_sales_summary_empty(self, crm: CRMPipeline):
        summary = crm.get_sales_summary()
        assert summary["total_deals"] == 0
        assert summary["total_value"] == 0
        assert summary["conversion_rate"] == "0.0%"

    def test_get_sales_summary_with_data(self, crm: CRMPipeline):
        crm.add_contact("Alice")
        crm.add_deal("Won", 10000, "1", DealStage.CLOSED_WON)
        crm.add_deal("Lost", 5000, "1", DealStage.CLOSED_LOST)
        crm.add_deal("Pipeline", 3000, "1", DealStage.PROPOSAL)
        summary = crm.get_sales_summary()
        assert summary["total_deals"] == 3
        assert summary["total_value"] == 18000
        assert summary["won_value"] == 10000
        assert summary["lost_value"] == 5000
        assert summary["pipeline_value"] == 3000

    def test_add_activity(self, crm: CRMPipeline):
        crm.add_contact("Alice")
        activity = crm.add_activity("1", "call", "Discussed terms")
        assert activity["type"] == "call"
        assert activity["description"] == "Discussed terms"


class TestDealStage:
    def test_enum_values(self):
        assert DealStage.LEAD.value == "lead"
        assert DealStage.CLOSED_WON.value == "closed_won"
        assert DealStage.CLOSED_LOST.value == "closed_lost"
