from __future__ import annotations

import time
from typing import Any

from core.memory.engine import MemoryEngine
from core.memory.store import memory as _store


def build_tree(memory: MemoryEngine | None = None) -> dict[str, Any]:
    eng = memory or _get_default_engine()
    layers = []

    def _layer(name: str, icon: str, items: list[dict]) -> dict:
        return {"name": name, "icon": icon, "count": len(items), "items": items}

    stm = eng.short_term if hasattr(eng, 'short_term') and eng.short_term else None
    stm_items = []
    if stm:
        for i, entry in enumerate(getattr(stm, 'entries', getattr(stm, 'buffer', []))):
            stm_items.append({
                "id": f"stm_{i}", "title": getattr(entry, 'content', str(entry))[:120],
                "role": getattr(entry, 'role', 'unknown'), "type": "short_term",
            })
    layers.append(_layer("Short-Term Memory", "MessageSquare", stm_items))

    ltm = eng.long_term if hasattr(eng, 'long_term') and eng.long_term else None
    ltm_items = []
    if ltm:
        store = getattr(ltm, 'store', {})
        if isinstance(store, dict):
            for ns, vals in store.items():
                if isinstance(vals, dict):
                    for key in list(vals.keys())[:20]:
                        ltm_items.append({
                            "id": f"ltm_{ns}_{key}", "title": key,
                            "namespace": ns, "type": "long_term",
                        })
                elif isinstance(vals, list):
                    ltm_items.append({
                        "id": f"ltm_{ns}", "title": f"namespace:{ns}",
                        "count": len(vals), "type": "long_term",
                    })
    layers.append(_layer("Long-Term Memory", "Database", ltm_items))

    ep = eng.episodic if hasattr(eng, 'episodic') and eng.episodic else None
    ep_items = []
    if ep:
        episodes = getattr(ep, 'episodes', getattr(ep, '_episodes', []))
        for i, e in enumerate(episodes[:30]):
            task = getattr(e, 'task', getattr(e, 'description', ''))
            ep_items.append({
                "id": f"ep_{i}", "title": str(task)[:120],
                "success": getattr(e, 'success', True),
                "type": "episodic",
            })
    layers.append(_layer("Episodic Memory", "Clock", ep_items))

    sem = eng.semantic if hasattr(eng, 'semantic') and eng.semantic else None
    sem_items = []
    if sem:
        facts = getattr(sem, 'facts', getattr(sem, '_facts', []))
        for i, f in enumerate(facts[:30]):
            subject = getattr(f, 'subject', getattr(f, 'topic', ''))
            sem_items.append({
                "id": f"sem_{i}", "title": str(subject)[:120] if subject else str(getattr(f, 'predicate', ''))[:120],
                "confidence": getattr(f, 'confidence', 0.0),
                "type": "semantic",
            })
    layers.append(_layer("Semantic Memory", "Brain", sem_items))

    vs = eng.vector_store if hasattr(eng, 'vector_store') and eng.vector_store else None
    vs_items = []
    if vs:
        records = getattr(vs, 'records', getattr(vs, '_records', []))
        for i, rec in enumerate(records[:30]):
            content = getattr(rec, 'content', getattr(rec, 'text', ''))
            vs_items.append({
                "id": f"vs_{i}", "title": str(content)[:120],
                "type": "vector",
            })
    layers.append(_layer("Vector Store", "Layers", vs_items))

    wk = eng.working if hasattr(eng, 'working') and eng.working else None
    wk_items = []
    if wk:
        tasks = getattr(wk, 'tasks', getattr(wk, '_tasks', []))
        for i, t in enumerate(tasks[:20]):
            title = getattr(t, 'title', getattr(t, 'task', str(t)))
            wk_items.append({
                "id": f"wk_{i}", "title": str(title)[:120],
                "type": "working",
            })
    layers.append(_layer("Working Memory", "Cpu", wk_items))

    conv = _store.get_recent_context(50) if hasattr(_store, 'get_recent_context') else ""
    conv_items = []
    if conv:
        lines = [l for l in conv.split("\n") if l.strip()][:30]
        for i, line in enumerate(lines):
            conv_items.append({
                "id": f"conv_{i}", "title": line.strip()[:120],
                "type": "conversation",
            })
    layers.append(_layer("Conversation Log", "MessageSquare", conv_items))

    return {
        "layers": layers,
        "total_items": sum(l["count"] for l in layers),
        "layer_count": len(layers),
    }


def get_branch(layer: str, memory: MemoryEngine | None = None) -> list[dict]:
    tree = build_tree(memory)
    for l in tree["layers"]:
        if l["name"].lower().replace("-", " ").replace("_", " ") == layer.lower().replace("-", " ").replace("_", " "):
            return l["items"]
    return []


def search_memory(query: str, memory: MemoryEngine | None = None) -> list[dict]:
    eng = memory or _get_default_engine()
    results = []
    if eng and hasattr(eng, 'recall'):
        try:
            results = eng.recall(query, limit=20)
        except Exception:
            pass
    return results


def _get_default_engine() -> MemoryEngine | None:
    try:
        from core.memory.engine import MemoryEngine as ME
        from core.memory.store import memory as store
        if hasattr(store, 'get_engine'):
            return store.get_engine()
        return None
    except Exception:
        return None
