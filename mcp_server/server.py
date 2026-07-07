import json

import httpx
from mcp.server.fastmcp import FastMCP

BASE = "http://localhost:8000"
mcp = FastMCP(
    "Lumina AI OS",
    instructions="Lumina AI OS — autonomous AI employee platform."
    " Connect to your Lumina backend via these tools.",
)


async def api_get(path: str) -> dict:
    async with httpx.AsyncClient(timeout=30) as c:
        r = await c.get(f"{BASE}{path}")
        r.raise_for_status()
        return r.json()

async def api_post(path: str, body: dict) -> dict:
    async with httpx.AsyncClient(timeout=120) as c:
        r = await c.post(f"{BASE}{path}", json=body)
        r.raise_for_status()
        return r.json()


@mcp.tool()
async def chat(message: str) -> str:
    """Talk to Lumina CEO AI. Ask anything — planning, research, business, coding."""
    res = await api_post("/chat", {"message": message})
    return res.get("reply", "")


@mcp.tool()
async def generate_code(description: str, language: str = "python") -> str:
    """Generate production code. Describe what you want, get code back."""
    res = await api_post("/code/generate", {"description": description, "language": language})
    return f"```{language}\n{res['code']}\n```\n\n**Explanation:** {res['explanation']}"


@mcp.tool()
async def run_agent(agent: str, task: str) -> str:
    """Run a specialized Lumina AI agent: software_engineer, web_developer, lead_gen, etc."""
    res = await api_post("/agents/run", {"agent": agent, "task": task})
    if res.get("status") == "error":
        return f"Error: {res.get('error')}"
    return res.get("output", "")


@mcp.tool()
async def list_agents() -> str:
    """List all available Lumina AI agents with their categories."""
    res = await api_get("/agents/categories")
    lines = []
    for category, agents in res.items():
        lines.append(f"\n**{category.upper()}:**")
        lines.extend(f"  - {a}" for a in agents)
    return "\n".join(lines)


@mcp.tool()
async def self_heal(task: str) -> str:
    """Self-healing loop: plan → execute → verify → fix → retry. Iterates until quality is met."""
    res = await api_post("/automation/heal", {"task": task})
    status = res.get("status", "unknown")
    result = res.get("result", "")
    attempts = res.get("attempts", 0)
    return f"**Status:** {status} ({attempts} attempt{'s' if attempts != 1 else ''})\n\n{result}"


@mcp.tool()
async def desktop_info() -> str:
    """Get system information: OS, CPU, hostname, current directory."""
    res = await api_get("/desktop/info")
    return json.dumps(res, indent=2)


@mcp.tool()
async def list_files(path: str = ".") -> str:
    """List files in a directory on the local machine."""
    res = await api_get(f"/desktop/files?path={path}")
    files = res.get("files", [])
    lines = [f"**{res.get('count', 0)} files** in `{path}`:\n"]
    for f in files:
        icon = "📁" if f["type"] == "dir" else "📄"
        size = f"({f['size']}B)" if f["type"] == "file" else ""
        lines.append(f"  {icon} {f['name']} {size}")
    return "\n".join(lines)


@mcp.tool()
async def read_file(path: str) -> str:
    """Read a file from the local machine."""
    res = await api_get(f"/desktop/files/read?path={path}")
    if "error" in res:
        return f"Error: {res['error']}"
    return res.get("content", "")


@mcp.tool()
async def crm_summary() -> str:
    """Get CRM sales summary: total deals, contacts, pipeline value, conversion rate."""
    res = await api_get("/crm/summary")
    return json.dumps(res, indent=2)


@mcp.tool()
async def crm_add_contact(name: str, email: str = "", phone: str = "", company: str = "") -> str:
    """Add a new contact to the CRM."""
    body = {"name": name, "email": email, "phone": phone, "company": company}
    res = await api_post("/crm/contacts", body)
    return json.dumps(res, indent=2)


@mcp.tool()
async def crm_add_deal(title: str, value: float, contact_id: str) -> str:
    """Add a new sales deal to the CRM pipeline."""
    res = await api_post("/crm/deals", {"title": title, "value": value, "contact_id": contact_id})
    return json.dumps(res, indent=2)


@mcp.tool()
async def seo_analyze_page(html: str, url: str = "") -> str:
    """Analyze a webpage HTML for SEO: title, meta, headings, issues, suggestions."""
    res = await api_post("/seo/analyze", {"html": html, "url": url})
    return json.dumps(res, indent=2)


@mcp.tool()
async def seo_generate_meta(content: str, focus_keyword: str = "") -> str:
    """Generate optimized SEO meta tags (title, description, keywords) from content."""
    res = await api_post("/seo/meta", {"content": content, "focus_keyword": focus_keyword})
    return json.dumps(res, indent=2)


@mcp.tool()
async def system_health() -> str:
    """Check Lumina system health and active providers."""
    res = await api_get("/system/health")
    providers = ", ".join(res.get("providers", []))
    return (
        f"**Status:** {res.get('status')}\n"
        f"**Version:** {res.get('version')}\n"
        f"**Primary:** {res.get('primary_provider')}\n"
        f"**Chain:** {providers}"
    )


@mcp.resource("config://system")
async def system_config() -> str:
    """Lumina AI OS system configuration and provider priority."""
    res = await api_get("/system/config")
    return json.dumps(res, indent=2)


@mcp.resource("agents://list")
async def agents_resource() -> str:
    """All available Lumina AI agents."""
    res = await api_get("/agents")
    return json.dumps(res, indent=2)


def run():
    mcp.run()


if __name__ == "__main__":
    run()
