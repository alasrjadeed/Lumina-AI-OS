"""Developer platform — CLI, SDK, templates, packaging, docs.

Command-line interface, plugin SDK for scaffolding/validation/building,
template system with variable substitution, package manager with
dependency resolution, and AST-based documentation generation.
"""

from core.developer.cli import CLI, CLICommand, cli
from core.developer.docs import DocClass, DocFunction, DocModule, DocumentationGenerator
from core.developer.package_manager import InstalledPackage, PackageManager, PackageMetadata
from core.developer.sdk import PluginSDK, SDKAPIClient
from core.developer.templates import Template, TemplateFile, TemplateManager

__all__ = [
    "CLI",
    "CLICommand",
    "cli",
    "TemplateManager",
    "Template",
    "TemplateFile",
    "PluginSDK",
    "SDKAPIClient",
    "PackageManager",
    "PackageMetadata",
    "InstalledPackage",
    "DocumentationGenerator",
    "DocModule",
    "DocClass",
    "DocFunction",
]
