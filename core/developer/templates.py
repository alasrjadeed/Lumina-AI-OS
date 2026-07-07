from __future__ import annotations

import os
import re
from dataclasses import dataclass, field
from pathlib import Path

from core.log import log


@dataclass
class TemplateFile:
    path: str
    content: str
    executable: bool = False


@dataclass
class Template:
    name: str
    description: str = ""
    files: list[TemplateFile] = field(default_factory=list)
    variables: list[str] = field(default_factory=list)


class TemplateManager:
    """File and project scaffolding with variable substitution."""

    def __init__(self):
        self._templates: dict[str, Template] = {}
        self._register_builtins()

    def register(self, template: Template) -> None:
        self._templates[template.name] = template

    def get(self, name: str) -> Template | None:
        return self._templates.get(name)

    def list_templates(self) -> list[Template]:
        return list(self._templates.values())

    def render(
        self, template_name: str, variables: dict[str, str], output_dir: str = "."
    ) -> list[str]:
        template = self._templates.get(template_name)
        if not template:
            raise ValueError(f"Template not found: {template_name}")
        created = []
        for tf in template.files:
            rendered_path = self._substitute(tf.path, variables)
            rendered_content = self._substitute(tf.content, variables)
            out_path = os.path.join(output_dir, rendered_path)
            Path(out_path).parent.mkdir(parents=True, exist_ok=True)
            Path(out_path).write_text(rendered_content)
            if tf.executable:
                os.chmod(out_path, 0o755)
            created.append(out_path)
            log.info("Created: %s", out_path)
        return created

    def create_from_string(self, template_name: str, content: str, output_path: str,
                           variables: dict[str, str] | None = None) -> str:
        rendered = self._substitute(content, variables or {})
        Path(output_path).parent.mkdir(parents=True, exist_ok=True)
        Path(output_path).write_text(rendered)
        return output_path

    def _substitute(self, text: str, variables: dict[str, str]) -> str:
        def replace(match: re.Match) -> str:
            key = match.group(1)
            return variables.get(key, match.group(0))
        return re.sub(r"\{\{(\w+)\}\}", replace, text)

    def _register_builtins(self) -> None:
        self.register(Template(
            name="plugin",
            description="A new Lumina plugin",
            variables=["name", "description", "author", "version"],
            files=[
                TemplateFile(
                    path="plugins/{{name}}/__init__.py",
                    content=(
                        '"""{{description}}"""\n'
                        '\n'
                        'from core.desktop.plugin_manager import PluginMetadata\n'
                        '\n'
                        '\n'
                        'metadata = PluginMetadata(\n'
                        '    name="{{name}}",\n'
                        '    version="{{version}}",\n'
                        '    description="{{description}}",\n'
                        '    author="{{author}}",\n'
                        ')\n'
                        '\n'
                        '\n'
                        'def on_load():\n'
                        '    pass\n'
                        '\n'
                        '\n'
                        'def on_unload():\n'
                        '    pass\n'
                        '\n'
                        '\n'
                        'def on_enable():\n'
                        '    pass\n'
                        '\n'
                        '\n'
                        'def on_disable():\n'
                        '    pass\n'
                    ),
                ),
                TemplateFile(
                    path="plugins/{{name}}/README.md",
                    content="# {{name}}\n\n{{description}}\n",
                ),
            ],
        ))
        self.register(Template(
            name="module",
            description="A new core module",
            variables=["name", "description"],
            files=[
                TemplateFile(path="core/{{name}}/__init__.py", content=""),
                TemplateFile(
                    path="core/{{name}}/main.py",
                    content='"""{{description}}"""\n\n\nclass {{name|capitalize}}:\n    pass\n',
                ),
            ],
        ))
