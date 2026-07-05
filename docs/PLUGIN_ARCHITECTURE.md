# Lumina AI OS — Plugin Architecture

## Overview
Plugins extend Lumina's capabilities. Every plugin is a self-contained directory with a manifest and entry point.

## Structure
```
plugins/my-plugin/
├── manifest.json
├── main.py
├── requirements.txt (optional)
└── assets/ (optional)
```

## Manifest (manifest.json)
```json
{
  "name": "my-plugin",
  "version": "1.0.0",
  "description": "Description",
  "author": "Author",
  "dependencies": ["core-plugin"],
  "min_core_version": "1.0.0",
  "entry_point": "main",
  "permissions": ["filesystem", "network"],
  "metadata": {}
}
```

## Entry Point
```python
class MyPlugin:
    __plugin__ = True
    
    def on_load(self):
        pass
    
    def on_unload(self):
        pass
    
    def on_event(self, event_name, data):
        pass
```

## Plugin Lifecycle
1. **Discovery** — PluginLoader scans plugin directory for manifest.json files
2. **Validation** — Dependencies checked, core version verified
3. **Load** — Module imported, plugin class instantiated
4. **Init** — on_load() called
5. **Runtime** — Plugin receives events and can use kernel services
6. **Unload** — on_unload() called, module removed from sys.modules
7. **Reload** — Unload + Load cycle

## Plugin Interface
```python
class PluginInterface(ABC):
    def on_load(self) -> None
    def on_unload(self) -> None
    def on_event(self, event_name: str, data: Dict) -> None
```

## Service Access
Plugins access kernel services through the ServiceRegistry:
```python
service = kernel.service_registry.get_instance("service_name")
```
