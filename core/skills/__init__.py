"""Skills catalog — agent-discoverable capabilities following the agentskills.io standard.

Skills teach agents how to better use tools and improve their reasoning.
Every skill wraps one or more tools — agents discover them from the catalog
and invoke them on demand.
"""

from core.skills.catalog import Skill, SkillCatalog, SkillSource

__all__ = ["Skill", "SkillCatalog", "SkillSource"]
