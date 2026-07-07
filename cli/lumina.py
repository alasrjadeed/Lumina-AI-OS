#!/usr/bin/env python3
"""Lumina AI OS — CLI Interface

Usage:
  lumina chat <message>          Talk to Lumina CEO AI
  lumina code <description>      Generate code (default: python)
  lumina code -l js <desc>       Generate code in specific language
  lumina agent <name> <task>     Run a specialized agent
  lumina agents                  List all agents
  lumina heal <task>             Self-healing loop
  lumina status                  Check system health & provider chain
  lumina crm summary             CRM sales summary
  lumina crm contact <name>      Add CRM contact
  lumina seo analyze <html>      Analyze HTML for SEO
  lumina files <path>            List files
  lumina read <path>             Read a file
  lumina mcp                     Start MCP server
  lumina open                    Open dashboard in browser
  lumina help                    Show this help
"""

import argparse
import json
import os
import subprocess
import sys
import textwrap

import httpx

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))

BASE = "http://localhost:8000"


def eprint(*a, **kw):
    print(*a, file=sys.stderr, **kw)


def api_get(path):
    try:
        r = httpx.get(f"{BASE}{path}", timeout=30)
        r.raise_for_status()
        return r.json()
    except httpx.ConnectError:
        eprint(" Error: Lumina backend is not running.")
        eprint(
            " Start it with:  source venv/bin/activate"
            " && uvicorn main:app --host 0.0.0.0 --port 8000"
        )
        sys.exit(1)
    except Exception as e:
        eprint(f" Error: {e}")
        sys.exit(1)


def api_post(path, data):
    try:
        r = httpx.post(f"{BASE}{path}", json=data, timeout=120)
        r.raise_for_status()
        return r.json()
    except httpx.ConnectError:
        eprint(" Error: Lumina backend is not running.")
        sys.exit(1)
    except Exception as e:
        eprint(f" Error: {e}")
        sys.exit(1)


def cmd_chat(args):
    message = " ".join(args.message) if args.message else input("You: ")
    print(" Lumina thinking...", end="", flush=True)
    res = api_post("/chat", {"message": message})
    print("\r" + " " * 40 + "\r", end="")
    print(res.get("reply", ""))


def cmd_code(args):
    desc = " ".join(args.description)
    lang = args.language or "python"
    print(f" Generating {lang} code...", end="", flush=True)
    res = api_post("/code/generate", {"description": desc, "language": lang})
    print("\r" + " " * 40 + "\r", end="")
    print()
    print(f"```{lang}")
    print(res.get("code", ""))
    print("```")
    if res.get("explanation"):
        print()
        print(res["explanation"])


def cmd_agent(args):
    name = args.agent_name
    task = " ".join(args.task)
    print(f" Running {name}...", end="", flush=True)
    res = api_post("/agents/run", {"agent": name, "task": task})
    print("\r" + " " * 40 + "\r", end="")
    if res.get("status") == "error":
        print(f" Error: {res.get('error', 'Unknown')}")
    else:
        print(res.get("output", ""))


def cmd_agents(args):
    res = api_get("/agents")
    print(" Available Agents:")
    for a in res.get("agents", []):
        print(f"   {a}")


def cmd_heal(args):
    task = " ".join(args.task)
    print(f" Self-healing: {task}")
    print(" (plan → execute → verify → fix → retry)")
    res = api_post("/automation/heal", {"task": task})
    print(f" Status: {res.get('status')} ({res.get('attempts')} attempt(s))")
    print()
    print(res.get("result", ""))


def cmd_status(args):
    h = api_get("/system/health")
    c = api_get("/system/config")
    print(f" Lumina AI OS — v{h.get('version', '?')}")
    print(f" Status: {h.get('status', '?')}")
    print(f" Primary: {h.get('primary_provider', '?')}")
    print()
    print(" Provider Chain (auto-fallback):")
    for i, p in enumerate(c.get("provider_priority", []), 1):
        print(f"   {i}. {p}")
    print()
    print(f" Agent count: {len(api_get('/agents').get('agents', []))}")


def cmd_crm(args):
    if args.crm_action == "summary":
        res = api_get("/crm/summary")
        print(json.dumps(res, indent=2))
    elif args.crm_action == "contact":
        name = " ".join(args.crm_value) if args.crm_value else input("Name: ")
        res = api_post("/crm/contacts", {"name": name})
        print(f" Contact added: {res.get('id', '?')}")
    elif args.crm_action == "deals":
        res = api_get("/crm/deals")
        for d in res.get("deals", []):
            print(f"  [{d['stage']}] {d['title']} — ${d['value']:.2f}")
    else:
        print("Subcommands: summary, contact <name>, deals")


def cmd_seo(args):
    html = " ".join(args.html) if args.html else input("HTML: ")
    print(" Analyzing...", end="", flush=True)
    res = api_post("/seo/analyze", {"html": html})
    print("\r" + " " * 40 + "\r", end="")
    print(json.dumps(res, indent=2))


def cmd_files(args):
    path = " ".join(args.path) if args.path else "."
    res = api_get(f"/desktop/files?path={path}")
    for f in res.get("files", []):
        icon = "" if f["type"] == "dir" else " "
        size = f" ({f['size']}B)" if f["type"] == "file" else "/"
        print(f"  {icon} {f['name']}{size}")


def cmd_read(args):
    path = " ".join(args.path) if args.path else "."
    res = api_get(f"/desktop/files/read?path={path}")
    if "error" in res:
        print(f" Error: {res['error']}")
    else:
        print(res.get("content", ""))


def cmd_mcp(args):
    print(" Starting MCP server...")
    base = os.path.dirname(os.path.abspath(__file__))
    venv = os.path.join(os.path.dirname(base), "venv", "bin", "python3")
    server = os.path.join(base, "..", "mcp_server", "server.py")
    os.execv(venv, [venv, server])


def cmd_open(args):
    subprocess.Popen(["xdg-open", "http://localhost:5173"])
    print(" Dashboard opened in browser.")


def main():
    parser = argparse.ArgumentParser(
        description="Lumina AI OS — CLI Interface",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=textwrap.dedent("""\
            Examples:
              lumina chat "What is the capital of France?"
              lumina code "function to sort a list" -l python
              lumina agent documentation "write README for project"
              lumina heal "find and fix bugs in app.py"
              lumina status
              lumina files /home
              lumina crm summary
        """),
    )
    sub = parser.add_subparsers(dest="command")

    p_chat = sub.add_parser("chat", help="Talk to Lumina CEO AI")
    p_chat.add_argument("message", nargs="*", help="Your message")

    p_code = sub.add_parser("code", help="Generate code")
    p_code.add_argument("description", nargs="*", help="What to generate")
    p_code.add_argument(
        "-l", "--language", default="python",
        help="Language (python, js, ts, java, kotlin, go, rust, sql, dart, ...)",
    )

    p_agent = sub.add_parser("agent", help="Run a specialized agent")
    p_agent.add_argument("agent_name", help="Agent name (software_engineer, lead_gen, etc.)")
    p_agent.add_argument("task", nargs="*", help="Task description")

    sub.add_parser("agents", help="List all agents")

    p_heal = sub.add_parser("heal", help="Self-healing loop")
    p_heal.add_argument("task", nargs="*", help="Task to self-heal")

    sub.add_parser("status", help="System health")

    p_crm = sub.add_parser("crm", help="CRM operations")
    p_crm.add_argument("crm_action", choices=["summary", "contact", "deals"], help="CRM subcommand")
    p_crm.add_argument("crm_value", nargs="*", help="Value (e.g. contact name)")

    p_seo = sub.add_parser("seo", help="SEO analysis")
    p_seo.add_argument("html", nargs="*", help="HTML content")

    p_files = sub.add_parser("files", help="List files")
    p_files.add_argument("path", nargs="*", help="Directory path")

    p_read = sub.add_parser("read", help="Read a file")
    p_read.add_argument("path", nargs="*", help="File path")

    sub.add_parser("mcp", help="Start MCP server")
    sub.add_parser("open", help="Open dashboard in browser")
    sub.add_parser("help", help="Show this help")

    args = parser.parse_args()

    if not args.command or args.command == "help":
        parser.print_help()
        return

    handlers = {
        "chat": cmd_chat,
        "code": cmd_code,
        "agent": cmd_agent,
        "agents": cmd_agents,
        "heal": cmd_heal,
        "status": cmd_status,
        "crm": cmd_crm,
        "seo": cmd_seo,
        "files": cmd_files,
        "read": cmd_read,
        "mcp": cmd_mcp,
        "open": cmd_open,
    }

    handler = handlers.get(args.command)
    if handler:
        handler(args)


if __name__ == "__main__":
    main()
