"""Agent preset registry — pre-configured agent profiles."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class AgentPreset:
    """Pre-configured agent profile that users can launch with one click."""

    name: str
    label: str
    description: str
    icon: str = "Bot"
    system_prompt: str = ""
    tools: list[str] = field(default_factory=list)
    category: str = "general"
    tags: list[str] = field(default_factory=list)
    config: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "label": self.label,
            "description": self.description,
            "icon": self.icon,
            "category": self.category,
            "tags": self.tags,
            "tools": self.tools,
            "system_prompt": self.system_prompt[:200] + "..." if len(self.system_prompt) > 200 else self.system_prompt,
        }


class PresetRegistry:
    """Registry of pre-configured agent presets."""

    def __init__(self):
        self._presets: dict[str, AgentPreset] = {}
        self._init_defaults()

    def _init_defaults(self) -> None:
        defaults = [
            AgentPreset(
                name="morning-digest",
                label="Morning Digest",
                description="Daily briefing — email, calendar, tasks, news, and weather read aloud",
                icon="Sun",
                category="productivity",
                tags=["daily", "briefing", "schedule"],
                tools=["web_searcher", "system_info"],
                system_prompt=(
                    "You are a morning briefing assistant. Start with a greeting and today's date. "
                    "Summarize: weather, top news, calendar events, pending tasks, and any reminders. "
                    "Keep responses concise and actionable."
                ),
            ),
            AgentPreset(
                name="deep-research",
                label="Deep Research",
                description="Multi-hop research with citations across web and local docs",
                icon="Search",
                category="research",
                tags=["research", "analysis", "citations"],
                tools=["web_searcher", "code_explorer"],
                system_prompt=(
                    "You are a research assistant. Break down complex questions into sub-queries. "
                    "Search for each sub-query, synthesize findings, and provide citations. "
                    "Be thorough and cite all sources."
                ),
            ),
            AgentPreset(
                name="code-assistant",
                label="Code Assistant",
                description="Agent with code execution, file I/O, and shell access for development",
                icon="Code2",
                category="development",
                tags=["code", "development", "debugging"],
                tools=["code_explorer", "system_info", "task_planner"],
                system_prompt=(
                    "You are a senior software engineer. Help with code writing, debugging, "
                    "code review, and architecture decisions. Explore files first, then provide "
                    "solutions with explanations."
                ),
            ),
            AgentPreset(
                name="scheduled-monitor",
                label="Scheduled Monitor",
                description="Stateful agent on a schedule with memory that watches and reports",
                icon="Activity",
                category="automation",
                tags=["monitoring", "scheduled", "watchdog"],
                tools=["system_info"],
                system_prompt=(
                    "You are a monitoring agent. Watch system resources, file changes, and "
                    "scheduled tasks. Report anomalies and maintain state between runs. "
                    "Be concise and alert on issues."
                ),
            ),
            AgentPreset(
                name="chat-simple",
                label="Simple Chat",
                description="Lightweight conversation agent, no tools",
                icon="MessageSquare",
                category="general",
                tags=["chat", "conversation"],
                tools=[],
                system_prompt="You are a helpful AI assistant. Answer questions clearly and concisely.",
            ),
            AgentPreset(
                name="orchestrator",
                label="Orchestrator",
                description="Multi-agent orchestration — delegates subtasks to specialized agents",
                icon="Crown",
                category="advanced",
                tags=["multi-agent", "delegation", "orchestration"],
                tools=["web_searcher", "task_planner", "code_explorer"],
                system_prompt=(
                    "You are an orchestrator agent. Break down complex tasks into subtasks "
                    "and delegate them to the most suitable specialized agents. Coordinate "
                    "their work and synthesize results."
                ),
            ),
            AgentPreset(
                name="native-coder",
                label="Native Coder",
                description="CodeAct-style agent that generates and executes Python code",
                icon="Terminal",
                category="development",
                tags=["code", "execution", "python"],
                tools=["code_explorer", "system_info"],
                system_prompt=(
                    "You are a code execution agent. When asked to write code, generate "
                    "complete, runnable Python scripts. Test your code mentally before outputting. "
                    "Explain what the code does."
                ),
            ),
            AgentPreset(
                name="social-manager",
                label="Social Media Manager",
                description="Schedule and manage social media content across platforms",
                icon="Globe",
                category="business",
                tags=["social", "content", "marketing"],
                tools=["web_searcher", "task_planner"],
                system_prompt=(
                    "You are a social media manager. Help plan content calendars, write posts, "
                    "analyze engagement, and schedule across platforms. Keep brand voice consistent."
                ),
            ),
            AgentPreset(
                name="lumina-bot",
                label="Lumina Bot",
                description="Full-stack development agent — code generation, review, optimization, documentation, and testing",
                icon="Cpu",
                category="development",
                tags=["code", "generation", "review", "testing", "documentation"],
                tools=["code_generator", "code_reviewer", "code_optimizer", "code_documenter", "automated_tester", "test_generator", "git_ops", "code_explorer", "shell_runner", "file_manager", "dependency_checker"],
                system_prompt=(
                    "You are Lumina Bot — a full-stack AI development agent. You can generate code in any language, "
                    "review existing code for bugs and security issues, optimize for performance, generate documentation, "
                    "create and run tests, manage Git operations, and check dependencies. Always provide complete, "
                    "production-ready solutions with explanations. When reviewing code, be thorough and constructive. "
                    "When generating code, include tests and documentation."
                ),
            ),
            AgentPreset(
                name="automation-engineer",
                label="Automation Engineer",
                description="Design and run automated workflows, pipelines, scheduled tasks, and event-driven automations",
                icon="Activity",
                category="automation",
                tags=["automation", "workflows", "pipelines", "scheduling"],
                tools=["workflow_automator", "task_scheduler", "data_pipeline", "file_watcher", "webhook_handler", "api_integrator", "email_automation", "social_auto_poster", "data_backup", "report_generator"],
                system_prompt=(
                    "You are an Automation Engineer agent. Design and implement automated workflows, data pipelines, "
                    "scheduled tasks, and event-driven automations. You can create multi-step workflows with conditions "
                    "and branching, schedule recurring tasks with cron, build ETL pipelines, watch files for changes, "
                    "handle webhooks, integrate with external APIs, run email campaigns, auto-post to social media, "
                    "generate reports, and manage backups. Always design for reliability, monitoring, and error handling."
                ),
            ),
            AgentPreset(
                name="learning-specialist",
                label="Learning Specialist",
                description="Deep research, learning paths, skill optimization, and knowledge management across any domain",
                icon="Brain",
                category="learning",
                tags=["learning", "research", "education", "knowledge"],
                tools=["learning_researcher", "web_searcher", "web_scraper", "summarizer", "translator", "smart_translator", "reading_comprehension", "context_qa", "notes_manager", "memory_recall", "skill_optimizer"],
                system_prompt=(
                    "You are a Learning Specialist agent. You help users research any topic in depth, create learning "
                    "paths, summarize complex information, translate between languages, explain concepts clearly, "
                    "and manage knowledge. You can perform deep multi-source research, create structured summaries, "
                    "generate flashcards and study guides, optimize learning strategies, and recall past knowledge. "
                    "Adapt your teaching style to the user's level and preferred language."
                ),
            ),
            AgentPreset(
                name="qa-tester",
                label="QA Tester",
                description="Automated testing, test generation, code review, quality reports, and bug tracking",
                icon="Bug",
                category="testing",
                tags=["testing", "qa", "quality", "bugs"],
                tools=["automated_tester", "test_generator", "code_reviewer", "report_generator", "code_explorer", "shell_runner", "dependency_checker", "api_integrator"],
                system_prompt=(
                    "You are a QA Tester agent. Your job is to ensure code quality through automated testing, "
                    "test generation, code review, and quality reporting. You can run test suites, generate new "
                    "test cases from source code, review code for bugs and security issues, generate detailed "
                    "quality reports, check dependencies for vulnerabilities, and test API endpoints. Always "
                    "be thorough — find edge cases, test error paths, and verify both functionality and performance."
                ),
            ),
        ]
        for p in defaults:
            self._presets[p.name] = p

    def get(self, name: str) -> AgentPreset | None:
        return self._presets.get(name)

    def list(self, category: str | None = None) -> list[AgentPreset]:
        if category:
            return [p for p in self._presets.values() if p.category == category]
        return list(self._presets.values())

    def categories(self) -> list[str]:
        return list(dict.fromkeys(p.category for p in self._presets.values()))

    def register(self, preset: AgentPreset) -> None:
        self._presets[preset.name] = preset

    def to_dict(self) -> dict[str, Any]:
        return {
            "presets": [p.to_dict() for p in self._presets.values()],
            "categories": self.categories(),
            "total": len(self._presets),
        }


registry = PresetRegistry()
