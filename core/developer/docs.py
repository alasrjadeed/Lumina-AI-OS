from __future__ import annotations

import ast
import os
from dataclasses import dataclass, field
from pathlib import Path


@dataclass
class DocFunction:
    name: str
    signature: str = ""
    docstring: str = ""
    returns: str = ""
    params: list[dict] = field(default_factory=list)


@dataclass
class DocClass:
    name: str
    docstring: str = ""
    methods: list[DocFunction] = field(default_factory=list)
    bases: list[str] = field(default_factory=list)


@dataclass
class DocModule:
    name: str
    docstring: str = ""
    classes: list[DocClass] = field(default_factory=list)
    functions: list[DocFunction] = field(default_factory=list)


class DocumentationGenerator:
    """Parse Python modules and generate documentation."""

    def extract_module(self, path: str) -> DocModule:
        with open(path) as f:
            source = f.read()
        tree = ast.parse(source)
        module_name = os.path.splitext(os.path.basename(path))[0]
        module_doc = ast.get_docstring(tree) or ""
        doc = DocModule(name=module_name, docstring=module_doc)
        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef):
                cls = self._extract_class(node)
                doc.classes.append(cls)
            elif isinstance(node, ast.FunctionDef):
                if node.parent and isinstance(node.parent, ast.Module):
                    fn = self._extract_function(node)
                    doc.functions.append(fn)
        return doc

    def extract_directory(self, path: str, package: str = "") -> list[DocModule]:
        modules = []
        for root, _, files in os.walk(path):
            for f in files:
                if f.endswith(".py") and f != "__init__.py":
                    full_path = os.path.join(root, f)
                    try:
                        doc = self.extract_module(full_path)
                        rel = os.path.relpath(full_path, os.path.dirname(path) if package else path)
                        doc.name = rel.replace("/", ".").replace(".py", "")
                        modules.append(doc)
                    except Exception:
                        pass
        return modules

    def generate_markdown(self, module: DocModule) -> str:
        lines = [f"# Module: `{module.name}`\n"]
        if module.docstring:
            lines.append(module.docstring)
            lines.append("")
        if module.classes:
            lines.append("## Classes\n")
            for cls in module.classes:
                bases = f"({', '.join(cls.bases)})" if cls.bases else ""
                lines.append(f"### `class {cls.name}{bases}`\n")
                if cls.docstring:
                    lines.append(cls.docstring + "\n")
                if cls.methods:
                    lines.append("**Methods:**\n")
                    lines.extend(
                        f"- `{m.name}{m.signature}` — {m.docstring[:100]}"
                        for m in cls.methods
                    )
                    lines.append("")
        if module.functions:
            lines.append("## Functions\n")
            for fn in module.functions:
                lines.append(f"### `{fn.name}{fn.signature}`\n")
                if fn.docstring:
                    lines.append(fn.docstring + "\n")
        return "\n".join(lines)

    def generate_api_reference(self, modules: list[DocModule]) -> str:
        lines = ["# API Reference\n"]
        lines.extend(
            f"- [`{mod.name}`](#module-{mod.name.lower().replace('.', '-')})"
            for mod in modules
        )
        lines.append("")
        for mod in modules:
            lines.append(self.generate_markdown(mod))
            lines.append("---\n")
        return "\n".join(lines)

    def generate_readme(self, project_name: str, description: str = "",
                        modules: list[DocModule] | None = None) -> str:
        lines = [
            f"# {project_name}\n",
            description,
            "",
            "## Installation\n",
            "```bash\npip install lumina\n```\n",
            "## Usage\n",
            (
                "```python\n"
                "from core import engine\n"
                "\n"
                "result = await engine.chat([{'role': 'user', 'content': 'Hello'}]\n"
                "print(result)\n"
                "```\n"
            ),
            "## Modules\n",
        ]
        if modules:
            lines.extend(f"- `{mod.name}` — {mod.docstring[:80]}" for mod in modules)
        else:
            lines.append("- Core platform modules")
        lines.extend([
            "",
            "## Documentation",
            "",
            "Full documentation at [docs.lumina.ai](https://docs.lumina.ai)",
            "",
        ])
        return "\n".join(lines)

    def export_markdown(self, module: DocModule, output_path: str) -> str:
        md = self.generate_markdown(module)
        Path(output_path).write_text(md)
        return output_path

    def _extract_class(self, node: ast.ClassDef) -> DocClass:
        bases = [self._node_name(b) for b in node.bases]
        cls = DocClass(name=node.name, docstring=ast.get_docstring(node) or "", bases=bases)
        for item in node.body:
            if isinstance(item, ast.FunctionDef):
                fn = self._extract_function(item)
                fn.name = f"{node.name}.{fn.name}"
                cls.methods.append(fn)
        return cls

    def _extract_function(self, node: ast.FunctionDef) -> DocFunction:
        docstring = ast.get_docstring(node) or ""
        sig = f"({', '.join(self._param_str(a) for a in node.args.args)})"
        if node.returns:
            sig += f" -> {self._node_name(node.returns)}"
        params = [{"name": a.arg} for a in node.args.args]
        return DocFunction(name=node.name, signature=sig, docstring=docstring, params=params)

    def _param_str(self, arg: ast.arg) -> str:
        return arg.arg

    def _node_name(self, node: ast.AST) -> str:
        if isinstance(node, ast.Name):
            return node.id
        elif isinstance(node, ast.Attribute):
            return f"{self._node_name(node.value)}.{node.attr}"
        elif isinstance(node, ast.Subscript):
            return f"{self._node_name(node.value)}[{self._node_name(node.slice)}]"
        return "?"
