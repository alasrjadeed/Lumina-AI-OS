# Volume 5: Plugin SDK Guide

## Overview

The Plugin SDK allows developers to build, test, and package plugins for Lumina. Plugins follow a standard protocol and can add any functionality — from business tools to integrations.

## Plugin Protocol

Every plugin needs:

```python
# plugins/my_plugin/__init__.py
"""My plugin description."""

from core.desktop.plugin_manager import PluginMetadata

metadata = PluginMetadata(
    name="My Plugin",
    version="1.0.0",
    description="What my plugin does",
    author="Your Name",
    hooks=["my_hook"],  # Optional event hooks
)

def on_load():
    """Called when plugin is loaded."""
    pass

def on_unload():
    """Called when plugin is unloaded."""
    pass

def on_enable():
    """Called when plugin is enabled."""
    pass

def on_disable():
    """Called when plugin is disabled."""
    pass
```

## Scaffolding a Plugin

Use the PluginSDK to generate the boilerplate:

```bash
python3 -c "
from core.developer.sdk import PluginSDK
sdk = PluginSDK()
files = sdk.scaffold(
    name='my_plugin',
    description='A custom integration',
    author='Developer',
    version='1.0.0',
    output_dir='.'
)
print(f'Created {len(files)} files')
"
```

This creates:
```
plugins/my_plugin/
├── __init__.py    # Plugin with metadata + lifecycle stubs
└── README.md      # Documentation placeholder
```

## Validating a Plugin

```bash
python3 -c "
from core.developer.sdk import PluginSDK
sdk = PluginSDK()
issues = sdk.validate('plugins/my_plugin')
if issues:
    print('Issues found:')
    for i in issues:
        print(f'  - {i}')
else:
    print('Plugin validated successfully')
"
```

## Building a Plugin Package

Package your plugin as a `.lumina` archive for distribution:

```bash
python3 -c "
from core.developer.sdk import PluginSDK
sdk = PluginSDK()
path = sdk.build('plugins/my_plugin', 'my_plugin.lumina')
print(f'Package created: {path}')
"
```

## Plugin Hooks

Plugins can register hooks that trigger on platform events:

```python
metadata = PluginMetadata(
    name="Notification Plugin",
    hooks=["message_sent", "deal_created"],
)

def on_message_sent(data):
    """Called when a message is sent via WhatsApp."""
    print(f"Message sent to {data['to']}")
```

Hooks are registered automatically from `metadata.hooks`.

## Accessing Core Services

Plugins can import and use any core module:

```python
from core.log import log
from core.crm.pipeline import crm

def add_contact_from_plugin():
    contact = crm.add_contact("John", "john@test.com")
    log.info(f"Contact added via plugin: {contact['id']}")
    return contact
```

## Installing Plugins

### Via Package Manager
```bash
python3 -c "
from core.developer.package_manager import PackageManager
pm = PackageManager()
pm.install('path/to/my_plugin.lumina')
"
```

### Via PluginManager
```bash
python3 -c "
from core.desktop.plugin_manager import PluginManager
pm = PluginManager()
pm.load('my_plugin')
pm.enable('my_plugin')
"
```

## Example: Weather Plugin

```python
"""Weather plugin — fetches current weather."""
from core.desktop.plugin_manager import PluginMetadata
import httpx

metadata = PluginMetadata(
    name="Weather",
    version="1.0.0",
    description="Get current weather for any city",
    author="Developer",
)

def on_load():
    print("Weather plugin loaded")

async def get_weather(city: str) -> str:
    """Fetch weather for a city."""
    async with httpx.AsyncClient() as client:
        resp = await client.get(
            f"https://wttr.in/{city}?format=%C+%t"
        )
        return resp.text
```

## Publishing

1. Build your `.lumina` package
2. Share via any distribution method
3. Users install via `PackageManager.install()`

## Best Practices

1. **Use the SDK** — Always scaffold with `PluginSDK.scaffold()`
2. **Validate** — Run `sdk.validate()` before packaging
3. **Log** — Use `core.log.log` for all logging
4. **Error handling** — Wrap external calls in try/except
5. **Stateless** — Store state in files or core memory, not in memory
6. **Version** — Increment version for each release
7. **Document** — Include README.md with usage instructions
