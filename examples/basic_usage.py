"""Lumina AI OS — Basic Usage Examples.

Run: python examples/basic_usage.py
Requires: lumina backend running on localhost:8000
Start with: uvicorn main:app --reload
"""

import json

import httpx

BASE = "http://localhost:8000"


def demo_chat():
    """Send a chat message and get a reply."""
    resp = httpx.post(f"{BASE}/chat", json={"message": "What is 2+2?"})
    data = resp.json()
    print(f"Chat reply: {data['reply'][:100]}...")
    return data


def demo_code_generation():
    """Generate code from a description."""
    resp = httpx.post(
        f"{BASE}/code/generate",
        json={
            "description": "a function to calculate fibonacci numbers",
            "language": "python",
        },
    )
    data = resp.json()
    print(f"Generated code ({data['language']}):")
    print(data["code"][:300])
    return data


def demo_system_health():
    """Check system health."""
    resp = httpx.get(f"{BASE}/system/health")
    data = resp.json()
    print(f"System: {data['status']} | Version: {data['version']}")
    print(f"Primary provider: {data.get('primary_provider')}")
    return data


def demo_list_agents():
    """List all available agents."""
    resp = httpx.get(f"{BASE}/agents")
    data = resp.json()
    print(f"Available agents ({len(data['agents'])}):")
    for agent in data["agents"]:
        print(f"  - {agent}")
    return data


def demo_crm():
    """CRM operations."""
    # Add a contact
    resp = httpx.post(
        f"{BASE}/crm/contacts",
        json={
            "name": "Alice Smith",
            "email": "alice@example.com",
            "phone": "+1234567890",
        },
    )
    print(f"Added contact: {resp.json()}")

    # Get summary
    resp = httpx.get(f"{BASE}/crm/summary")
    print(f"CRM summary: {json.dumps(resp.json(), indent=2)}")


def demo_seo():
    """SEO site management."""
    resp = httpx.post(
        f"{BASE}/seo/sites",
        json={
            "url": "https://example.com",
            "name": "Example Site",
        },
    )
    print(f"Added site: {resp.json()}")

    resp = httpx.get(f"{BASE}/seo/sites")
    print(f"Sites: {json.dumps(resp.json(), indent=2)}")


def demo_desktop():
    """Desktop automation info."""
    resp = httpx.get(f"{BASE}/desktop/info")
    print(f"System info: {json.dumps(resp.json(), indent=2)}")


if __name__ == "__main__":
    print("=" * 60)
    print("Lumina AI OS — Basic Usage Examples")
    print("=" * 60)

    print("\n1. System Health")
    print("-" * 40)
    try:
        demo_system_health()
    except Exception as e:
        print(f"  (skip: {e})")

    print("\n2. Available Agents")
    print("-" * 40)
    try:
        demo_list_agents()
    except Exception as e:
        print(f"  (skip: {e})")

    print("\n3. Chat")
    print("-" * 40)
    try:
        demo_chat()
    except Exception as e:
        print(f"  (skip: {e})")

    print("\n4. Code Generation")
    print("-" * 40)
    try:
        demo_code_generation()
    except Exception as e:
        print(f"  (skip: {e})")

    print("\n5. CRM")
    print("-" * 40)
    try:
        demo_crm()
    except Exception as e:
        print(f"  (skip: {e})")

    print("\n6. SEO")
    print("-" * 40)
    try:
        demo_seo()
    except Exception as e:
        print(f"  (skip: {e})")

    print("\n7. Desktop")
    print("-" * 40)
    try:
        demo_desktop()
    except Exception as e:
        print(f"  (skip: {e})")

    print("\n" + "=" * 60)
    print("Examples complete. Start the backend with:")
    print("  uvicorn main:app --reload")
    print("=" * 60)
