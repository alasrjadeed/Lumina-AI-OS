from __future__ import annotations

from core.skills.catalog import Skill, SkillCatalog, SkillSource


class TestSkillCatalog:
    def test_builtin_skills_loaded(self):
        assert len(catalog.list_skills()) == 57

    def test_get_skill_by_name(self):
        skill = catalog.get_skill("code-explorer")
        assert skill is not None
        assert skill.name == "code-explorer"
        assert "code" in skill.tags

    def test_list_skills_by_tag(self):
        code_skills = catalog.list_skills(tag="code")
        assert len(code_skills) >= 1
        assert all("code" in s.tags for s in code_skills)

    def test_install_from_url(self):
        source = catalog.install_from_url("test-source", "https://example.com/skills")
        assert source.name == "test-source"
        assert catalog.get_source("test-source") is not None


catalog = SkillCatalog()
