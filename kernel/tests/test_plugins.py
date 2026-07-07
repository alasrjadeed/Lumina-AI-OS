from __future__ import annotations

from pathlib import Path

import core.plugins.crm as crm_plugin
import core.plugins.email_automation as email_plugin
import core.plugins.lead_management as lead_plugin
import core.plugins.marketing as marketing_plugin
import core.plugins.reporting as reporting_plugin
import core.plugins.seo_suite as seo_plugin
import core.plugins.whatsapp_automation as wa_plugin
from core.desktop.plugin_manager import PluginManager


class TestPluginDiscovery:
    def test_discover_seo_suite(self):
        pm = PluginManager()
        found = pm.discover()
        paths = [p for p in found if "seo_suite" in p]
        assert len(paths) >= 1

    def test_discover_crm(self):
        pm = PluginManager()
        found = pm.discover()
        assert any("crm" in p and "seo" not in p for p in found)

    def test_discover_all_plugins(self):
        pm = PluginManager()
        found = pm.discover()
        names = [p.split("/")[-1].replace(".py", "") for p in found]
        expected = {"seo_suite", "crm", "whatsapp_automation",
                    "email_automation", "lead_management",
                    "marketing", "reporting"}
        assert expected.issubset(set(names))


class TestSEOSuitePlugin:
    def test_load(self):
        pm = PluginManager()
        assert pm.load("seo_suite")
        info = pm.get_plugin("seo_suite")
        assert info is not None
        assert info.metadata.name == "SEO Suite"
        pm.unload("seo_suite")

    def test_module_functions(self):
        seo_plugin.add_site("https://example.com", "Example")
        sites = seo_plugin.list_sites()
        assert any(s["url"] == "https://example.com" for s in sites)

    def test_keyword_tracking(self):
        seo_plugin.track_keyword("test keyword", "https://example.com")
        kws = seo_plugin.list_keywords()
        assert any("test" in k.get("keyword", "") for k in kws)

    def test_audit_result_dataclass(self):
        ar = seo_plugin.AuditResult(url="https://test.com", score=85.0,
                                    issues=[{"type": "test", "severity": "low"}],
                                    suggestions=["fix it"])
        assert ar.score == 85.0
        assert len(ar.issues) == 1
        d = ar.to_dict()
        assert d["url"] == "https://test.com"

    def test_analyze_competitor(self):
        result = seo_plugin.analyze_competitor("https://competitor.com", ["competitor", "seo"])
        assert "competitor" in result["keywords_found"]

    def test_generate_report(self):
        report = seo_plugin.generate_report()
        assert "sites" in report
        assert "keywords" in report


class TestCRMPlugin:
    def test_load(self):
        pm = PluginManager()
        assert pm.load("crm")
        info = pm.get_plugin("crm")
        assert info.metadata.name == "CRM"
        pm.unload("crm")

    def test_contact_crud(self):
        crm_plugin.add_contact("John Doe", "john@example.com", phone="+123", company="Acme")
        contacts = crm_plugin.list_contacts()
        assert any(c["name"] == "John Doe" for c in contacts)
        results = crm_plugin.search_contacts("john")
        assert len(results) >= 1

    def test_deal_management(self):
        deal = crm_plugin.add_deal("Big Deal", 50000, stage="lead")
        assert deal["title"] == "Big Deal"
        crm_plugin.update_deal_stage(deal["id"], "qualified")
        deals = crm_plugin.list_deals("qualified")
        assert any(d["id"] == deal["id"] for d in deals)

    def test_deal_analytics(self):
        analytics = crm_plugin.get_deal_analytics()
        assert analytics.total_deals >= 1


class TestWhatsAppAutomationPlugin:
    def test_load(self):
        pm = PluginManager()
        assert pm.load("whatsapp_automation")
        pm.unload("whatsapp_automation")

    def test_auto_reply_rules(self):
        wa_plugin.add_auto_reply("hello", "Hi there!", match_type="exact")
        rules = wa_plugin.list_auto_replies()
        assert any(r.keyword == "hello" for r in rules)
        assert wa_plugin.remove_auto_reply("hello")
        assert not wa_plugin.remove_auto_reply("nonexistent")

    def test_get_matched_reply(self):
        wa_plugin.add_auto_reply("help", "How can I assist?", match_type="contains")
        reply = wa_plugin.get_matched_reply("I need help please")
        assert reply == "How can I assist?"

    def test_campaign_creation(self):
        wa_plugin.create_campaign("Test Campaign", "Hello!", ["+1234567890"])
        campaigns = wa_plugin.list_campaigns()
        assert any(c.name == "Test Campaign" for c in campaigns)


class TestEmailAutomationPlugin:
    def test_load(self):
        pm = PluginManager()
        assert pm.load("email_automation")
        pm.unload("email_automation")

    def test_template_crud(self):
        email_plugin.create_template(
            "welcome", "Welcome {name}!",
            "Hello {name}, welcome to our service",
        )
        t = email_plugin.get_template("welcome")
        assert t is not None
        assert t.subject == "Welcome {name}!"
        assert len(email_plugin.list_templates()) >= 1

    def test_render_template(self):
        t = email_plugin.create_template("greet", "Hi {name}", "Hello {name}")
        subject, body = email_plugin.render_template(t, {"name": "Alice"})
        assert subject == "Hi Alice"
        assert body == "Hello Alice"

    def test_campaign_creation(self):
        email_plugin.create_campaign("Newsletter", "welcome", ["a@b.com", "c@d.com"])
        camps = email_plugin.list_campaigns()
        assert any(c.name == "Newsletter" for c in camps)


class TestLeadManagementPlugin:
    def test_load(self):
        pm = PluginManager()
        assert pm.load("lead_management")
        pm.unload("lead_management")

    def test_add_and_get_lead(self):
        lead = lead_plugin.add_lead("Alice", "alice@test.com", source="website")
        fetched = lead_plugin.get_lead(lead.id)
        assert fetched is not None
        assert fetched.name == "Alice"

    def test_update_lead(self):
        lead = lead_plugin.add_lead("Bob", "bob@test.com")
        updated = lead_plugin.update_lead(lead.id, name="Bobby", company="Corp")
        assert updated.name == "Bobby"

    def test_update_status(self):
        lead = lead_plugin.add_lead("Charlie", "charlie@test.com")
        assert lead_plugin.update_status(lead.id, "qualified")
        fetched = lead_plugin.get_lead(lead.id)
        assert fetched.status == "qualified"

    def test_list_leads_filter(self):
        lead_plugin.add_lead("Diana", source="referral")
        lead_plugin.add_lead("Eve", source="website")
        refs = lead_plugin.list_leads(source="referral")
        assert all(lead.source == "referral" for lead in refs)

    def test_search_leads(self):
        lead_plugin.add_lead("Frank", "frank@corp.com")
        results = lead_plugin.search_leads("frank")
        assert len(results) >= 1

    def test_delete_lead(self):
        lead = lead_plugin.add_lead("Grace")
        assert lead_plugin.delete_lead(lead.id)
        assert not lead_plugin.delete_lead("nonexistent")

    def test_score_rule(self):
        lead_plugin.add_score_rule("email", "not_empty", "", points=20)
        lead = lead_plugin.add_lead("Hank", "hank@test.com")
        assert lead.score >= 20

    def test_analytics(self):
        analytics = lead_plugin.get_analytics()
        assert "total_leads" in analytics
        assert "by_source" in analytics


class TestMarketingPlugin:
    def test_load(self):
        pm = PluginManager()
        assert pm.load("marketing")
        pm.unload("marketing")

    def test_campaign_lifecycle(self):
        c = marketing_plugin.create_campaign("Summer Sale", "email", 1000)
        assert c.status == "draft"
        assert marketing_plugin.launch_campaign("Summer Sale")
        assert marketing_plugin.get_campaign("Summer Sale").status == "active"
        assert marketing_plugin.pause_campaign("Summer Sale")
        assert marketing_plugin.complete_campaign("Summer Sale")

    def test_tracking(self):
        marketing_plugin.create_campaign("Track Test", "social", 500)
        marketing_plugin.track_impression("Track Test", 1000)
        marketing_plugin.track_click("Track Test", 50)
        marketing_plugin.track_conversion("Track Test", 5)
        metrics = marketing_plugin.get_campaign_metrics("Track Test")
        assert metrics["impressions"] == 1000
        assert metrics["clicks"] == 50
        assert metrics["conversions"] == 5

    def test_content_calendar(self):
        marketing_plugin.schedule_content("Post 1", "Content body", channel="social")
        assert marketing_plugin.publish_content("Post 1")
        calendar = marketing_plugin.get_content_calendar()
        assert any(c.title == "Post 1" for c in calendar)

    def test_summary(self):
        summary = marketing_plugin.get_summary()
        assert "active_campaigns" in summary


class TestReportingPlugin:
    def test_load(self):
        pm = PluginManager()
        assert pm.load("reporting")
        pm.unload("reporting")

    def test_create_report(self):
        r = reporting_plugin.create_report("Test Report")
        reporting_plugin.add_section("Test Report", "Overview", "metrics")
        reporting_plugin.add_metric("Test Report", "Overview", "Users", 1500, "count", 12.5)
        assert r.title == "Test Report"
        assert len(r.sections) >= 1

    def test_add_table_data(self):
        reporting_plugin.create_report("Data Report")
        reporting_plugin.add_section("Data Report", "Details")
        reporting_plugin.add_table_data(
            "Data Report", "Details",
            [{"name": "A", "value": 1}, {"name": "B", "value": 2}],
        )
        reports = reporting_plugin.list_reports()
        assert len(reports) >= 1

    def test_export_csv(self, tmp_path: Path):
        reporting_plugin.create_report("CSV Test")
        reporting_plugin.add_section("CSV Test", "Metrics", "metrics")
        reporting_plugin.add_metric("CSV Test", "Metrics", "Revenue", 50000, "USD", 15.0)
        path = reporting_plugin.export_csv("CSV Test", "Metrics", str(tmp_path / "test.csv"))
        assert Path(path).exists()
        content = Path(path).read_text()
        assert "Revenue" in content

    def test_export_json(self, tmp_path: Path):
        reporting_plugin.create_report("JSON Test")
        reporting_plugin.add_section("JSON Test", "Stats")
        reporting_plugin.add_metric("JSON Test", "Stats", "Visitors", 1000)
        path = reporting_plugin.export_json("JSON Test", str(tmp_path / "test.json"))
        assert Path(path).exists()

    def test_export_html(self, tmp_path: Path):
        reporting_plugin.create_report("HTML Test")
        reporting_plugin.add_section("HTML Test", "Overview")
        reporting_plugin.add_metric("HTML Test", "Overview", "Users", 500)
        path = reporting_plugin.export_html("HTML Test", str(tmp_path / "test.html"))
        assert Path(path).exists()
        content = Path(path).read_text()
        assert "HTML Test" in content

    def test_generate_summary_report(self):
        report = reporting_plugin.generate_summary_report([
            {"name": "A", "value": 100},
            {"name": "B", "value": 200},
        ])
        assert report.title == "Summary Report"
        assert len(report.sections) >= 2


class TestPluginHookIntegration:
    def test_seo_hooks_registered(self):
        pm = PluginManager()
        pm.load("seo_suite")
        results = pm.trigger_hook("seo_audit", "https://test.com")
        assert isinstance(results, list)
        pm.unload("seo_suite")

    def test_crm_hooks_registered(self):
        pm = PluginManager()
        pm.load("crm")
        results = pm.trigger_hook("deal_created")
        assert isinstance(results, list)
        pm.unload("crm")

    def test_lead_hooks_registered(self):
        pm = PluginManager()
        pm.load("lead_management")
        results = pm.trigger_hook("lead_created")
        assert isinstance(results, list)
        pm.unload("lead_management")

    def test_load_all_plugins(self):
        pm = PluginManager()
        count = pm.load_all()
        assert count >= 7
        names = {p.metadata.name for p in pm.list_plugins()}
        assert "SEO Suite" in names
        assert "CRM" in names
        assert "WhatsApp Automation" in names
        assert "Email Automation" in names
        assert "Lead Management" in names
        assert "Marketing" in names
        assert "Reporting" in names
        pm.unload_all()
