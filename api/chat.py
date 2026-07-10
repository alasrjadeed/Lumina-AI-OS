import asyncio
import json
import subprocess

from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

from core.agents.runner import ALL_AGENTS
from core.crm.pipeline import crm
from core.desktop.os_automation import desktop
from core.memory.store import memory
from core.orchestrator import ceo
from core.provider import engine
from core.self_heal import self_heal

router = APIRouter(prefix="/chat", tags=["Chat"])


class ChatRequest(BaseModel):
    message: str
    thread_id: str | None = None
    agent: str = "CEO_AI"


class ChatResponse(BaseModel):
    reply: str
    agent: str
    thread_id: str | None = None


SLASH_COMMANDS = {
    "/chat": "chat with the CEO AI",
    "/code": "generate code: /code <description> [-l language]",
    "/agent": "run an agent: /agent <name> <task>",
    "/agents": "list all available agents",
    "/heal": "self-healing loop: /heal <task>",
    "/status": "system health and provider chain",
    "/crm": "CRM: /crm summary | /crm contact <name> | /crm deals",
    "/seo": "analyze page SEO: /seo <html>",
    "/files": "list directory: /files <path>",
    "/read": "read file: /read <path>",
    "/mcp": "start MCP server",
    "/open": "open dashboard in browser",
    "/skills": "show available skills and their descriptions",
    "/help": "show available commands",
}


async def handle_slash_command(message: str) -> str:
    parts = message.strip().split()
    cmd = parts[0].lower()
    args = parts[1:]

    if cmd == "/help":
        lines = ["**Available slash commands:**\n"]
        for c, desc in SLASH_COMMANDS.items():
            lines.append(f"  `{c}` — {desc}")
        return "\n".join(lines)

    if cmd == "/agents":
        names = sorted(ALL_AGENTS.keys())
        return f"**{len(names)} agents available:**\n" + "\n".join(f"  `{n}`" for n in names)

    if cmd == "/status":
        provider_names = [p.name for p in engine.providers]
        return (
            f"**Lumina AI OS**\n"
            f"Status: ok\n"
            f"Primary: {engine.providers[0].name if engine.providers else 'none'}\n"
            f"Chain: {' → '.join(provider_names)}\n"
        )

    if cmd == "/chat":
        msg = " ".join(args) if args else input("Message: ")
        result = await ceo.run(task=msg, context={"agent": "CEO_AI"})
        return result.output if result.status == "success" else f"Error: {result.error}"

    if cmd == "/code":
        desc = " ".join(args)
        lang = "python"
        if "-l" in args:
            idx = args.index("-l")
            lang = args[idx + 1] if idx + 1 < len(args) else "python"
            desc_parts = [
                a
                for a in args
                if a != "-l" and (args.index(a) != idx + 1 or args.index("-l") == args.index(a))
            ]
            desc = " ".join(desc_parts)
        res = await engine.chat(
            [
                {
                    "role": "system",
                    "content": (
                        f"Generate {lang} code. Return only the code block, no extra text."
                    ),
                },
                {"role": "user", "content": desc},
            ]
        )
        code = res.get("message", {}).get("content", "")
        return f"```{lang}\n{code}\n```"

    if cmd == "/agent":
        if len(args) < 2:
            return "Usage: `/agent <name> <task>`"
        name, task = args[0], " ".join(args[1:])
        agent = ALL_AGENTS.get(name)
        if not agent:
            return f"Unknown agent `{name}`. See `/agents` for available agents."
        result = await agent.run(task)
        return result.output if result.status == "success" else f"Error: {result.error}"

    if cmd == "/heal":
        task = " ".join(args) if args else "run diagnostics"
        result = await self_heal.execute(task)
        status = result["status"]
        attempts = result["attempts"]
        detail = result.get("result", "")
        return f"**{status}** ({attempts} attempts)\n\n{detail}"

    if cmd == "/crm":
        if not args:
            return "Usage: `/crm summary` | `/crm contact <name>` | `/crm deals`"
        if args[0] == "summary":
            s = crm.get_sales_summary()
            return (
                f"**CRM Summary**\n"
                f"Contacts: {s['total_contacts']}\n"
                f"Deals: {s['total_deals']}\n"
                f"Pipeline: ${s['pipeline_value']:.2f}\n"
                f"Won: ${s['won_value']:.2f}\n"
                f"Conversion: {s['conversion_rate']}"
            )
        if args[0] == "contact" and len(args) >= 2:
            contact = crm.add_contact(" ".join(args[1:]))
            return f"Contact added: `{contact['name']}` (ID: {contact['id']})"
        if args[0] == "deals":
            deals = crm.list_deals()
            if not deals:
                return "No deals in pipeline."
            return "\n".join(f"[{d['stage']}] {d['title']} — ${d['value']:.2f}" for d in deals)
        return "Unknown CRM command."

    if cmd == "/files":
        path = " ".join(args) if args else "."
        files = await desktop.list_files(path)
        lines = [f"**{path}** — {len(files)} items\n"]
        for f in files:
            size = f" ({f['size']}B)" if f["type"] == "file" else "/"
            lines.append(f"  {f['name']}{size}")
        return "\n".join(lines)

    if cmd == "/read":
        path = " ".join(args) if args else "."
        content = await desktop.read_file(path)
        if content is None:
            return f"File not found: {path}"
        return f"```\n{content[:2000]}\n```" if len(content) > 2000 else f"```\n{content}\n```"

    if cmd == "/skills":
        skills = [
            ("agent", "Run specialized AI agents (19 available)"),
            ("code", "Generate code in any language"),
            ("chat", "Talk to Lumina CEO AI for planning & research"),
            ("heal", "Autonomous self-healing loop"),
            ("crm", "CRM: contacts, deals, pipeline, sales summary"),
            ("files", "Browse and read local files"),
            ("seo", "Analyze page HTML for SEO"),
            ("mcp", "MCP server for AI tool connectivity"),
        ]
        lines = ["**Lumina AI OS Skills:**\n"]
        for name, desc in skills:
            lines.append(f"  `/`**{name}** — {desc}")
        return "\n".join(lines)

    if cmd == "/mcp":
        return "Run `lumina mcp` in terminal to start MCP server."

    if cmd == "/open":
        subprocess.Popen(["xdg-open", "http://localhost:5173"])
        return "Dashboard opened in browser."

    return f"Unknown command `{cmd}`. Type `/help` for available commands."


@router.post("", response_model=ChatResponse)
async def chat(req: ChatRequest):
    msg = req.message.strip()

    if msg.startswith("/"):
        reply = await handle_slash_command(msg)
        memory.add_conversation("user", msg, thread_id=req.thread_id)
        memory.add_conversation("assistant", reply, thread_id=req.thread_id)
        return ChatResponse(reply=reply, agent="slash", thread_id=req.thread_id)

    memory.add_conversation("user", msg, thread_id=req.thread_id)
    context = memory.get_recent_context(5, thread_id=req.thread_id)

    if not engine.providers:
        raise HTTPException(status_code=503, detail="No AI providers available")

    try:
        result = await asyncio.wait_for(
            ceo.run(
                task=f"Context:\n{context}\n\nUser message: {msg}",
                context={"agent": req.agent},
            ),
            timeout=30.0,
        )
    except TimeoutError:
        raise HTTPException(status_code=504, detail="AI provider timed out")

    if result.status == "error":
        raise HTTPException(status_code=500, detail=result.error)

    memory.add_conversation("assistant", result.output, thread_id=req.thread_id)
    return ChatResponse(reply=result.output, agent=req.agent, thread_id=req.thread_id)


@router.post("/stream")
async def chat_stream(req: ChatRequest):
    msg = req.message.strip()

    if msg.startswith("/"):
        reply = await handle_slash_command(msg)
        memory.add_conversation("user", msg, thread_id=req.thread_id)
        memory.add_conversation("assistant", reply, thread_id=req.thread_id)

        async def send():
            yield f"data: {json.dumps({'token': reply, 'done': True})}\n\n"

        return StreamingResponse(send(), media_type="text/event-stream")

    memory.add_conversation("user", msg, thread_id=req.thread_id)
    context = memory.get_recent_context(5, thread_id=req.thread_id)

    messages = [
        {"role": "user", "content": f"Context:\n{context}\n\nUser message: {msg}"},
    ]

    async def stream_tokens():
        full = ""
        try:
            async for token in engine.chat_stream(messages):
                full += token
                yield f"data: {json.dumps({'token': token, 'done': False})}\n\n"
        except Exception as e:
            yield f"data: {json.dumps({'token': f'Error: {e}', 'done': True})}\n\n"
            return
        memory.add_conversation("assistant", full, thread_id=req.thread_id)
        yield f"data: {json.dumps({'token': '', 'done': True})}\n\n"

    return StreamingResponse(stream_tokens(), media_type="text/event-stream")


@router.get("/history")
async def get_history(limit: int = 10, thread_id: str | None = None):
    if thread_id:
        thread = memory.get_thread(thread_id)
        if not thread:
            raise HTTPException(status_code=404, detail="Thread not found")
        return {"conversations": thread["messages"], "total": len(thread["messages"])}
    return {"conversations": memory.get_conversations(limit)}


@router.get("/commands")
async def list_commands():
    return {"commands": SLASH_COMMANDS}


@router.get("/conversations")
async def list_conversations(limit: int = 50):
    return {"conversations": memory.list_threads(limit), "total": len(memory.list_threads(limit))}


@router.post("/conversations")
async def create_conversation(title: str = Query("New Chat")):
    thread = memory.create_thread(title)
    return {"conversation": thread}


@router.get("/conversations/{thread_id}")
async def get_conversation(thread_id: str):
    thread = memory.get_thread(thread_id)
    if not thread:
        raise HTTPException(status_code=404, detail="Conversation not found")
    return {"conversation": thread}


@router.delete("/conversations/{thread_id}")
async def delete_conversation(thread_id: str):
    ok = memory.delete_thread(thread_id)
    if not ok:
        raise HTTPException(status_code=404, detail="Conversation not found")
    return {"deleted": True}


@router.patch("/conversations/{thread_id}")
async def rename_conversation(thread_id: str, title: str = Query(...)):
    ok = memory.rename_thread(thread_id, title)
    if not ok:
        raise HTTPException(status_code=404, detail="Conversation not found")
    return {"updated": True, "title": title}
