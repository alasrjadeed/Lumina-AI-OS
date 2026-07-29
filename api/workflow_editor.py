from fastapi import APIRouter, HTTPException, Body, Query

from core.workflow_editor import (
    WorkflowEdge, WorkflowNode, Workflow,
    workflow_store, credential_store,
    NODE_REGISTRY, NODE_CATEGORIES, NODE_TYPE_MAP, REVERSE_NODE_MAP,
    WORKFLOW_CATEGORIES,
)

router = APIRouter(prefix="/workflows", tags=["Workflow Editor"])


# ── Node Types ──


@router.get("/node-types")
async def list_node_types(category: str | None = None):
    types = list(NODE_REGISTRY.values())
    if category:
        types = [t for t in types if t["category"] == category]
    return {"nodeTypes": types, "categories": NODE_CATEGORIES}


@router.get("/node-types/{node_type}")
async def get_node_type(node_type: str):
    nt = NODE_REGISTRY.get(node_type)
    if not nt:
        raise HTTPException(status_code=404, detail="Node type not found")
    return {"nodeType": nt}


# ── Workflow CRUD ──


@router.get("")
async def list_workflows(category: str | None = None):
    return {"workflows": [w.to_dict() for w in workflow_store.list(category)]}


@router.post("")
async def create_workflow(name: str, description: str = "", category: str = "custom"):
    wf = workflow_store.create(name=name, description=description, category=category)
    return {"workflow": wf.to_dict()}


@router.get("/{workflow_id}")
async def get_workflow(workflow_id: str):
    wf = workflow_store.get(workflow_id)
    if not wf:
        raise HTTPException(status_code=404, detail="Workflow not found")
    return {"workflow": wf.to_dict()}


@router.patch("/{workflow_id}")
async def update_workflow(
    workflow_id: str,
    name: str | None = None,
    description: str | None = None,
    category: str | None = None,
    tags: str | None = None,
    settings: str | None = None,
):
    kwargs = {}
    if name is not None:
        kwargs["name"] = name
    if description is not None:
        kwargs["description"] = description
    if category is not None:
        kwargs["category"] = category
    if tags is not None:
        import json as _json
        try:
            kwargs["tags"] = _json.loads(tags)
        except Exception:
            kwargs["tags"] = [t.strip() for t in tags.split(",") if t.strip()]
    if settings is not None:
        import json as _json
        try:
            kwargs["settings"] = _json.loads(settings)
        except Exception:
            pass
    wf = workflow_store.update(workflow_id, **kwargs)
    if not wf:
        raise HTTPException(status_code=404, detail="Workflow not found")
    return {"workflow": wf.to_dict()}


@router.delete("/{workflow_id}")
async def delete_workflow(workflow_id: str):
    ok = workflow_store.delete(workflow_id)
    if not ok:
        raise HTTPException(status_code=404, detail="Workflow not found")
    return {"deleted": True}


# ── Nodes ──


@router.post("/{workflow_id}/nodes")
async def add_node(
    workflow_id: str,
    node_type: str,
    label: str,
    config: str = "{}",
    x: float = 0,
    y: float = 0,
    credentials: str | None = None,
    notes: str = "",
):
    wf = workflow_store.get(workflow_id)
    if not wf:
        raise HTTPException(status_code=404, detail="Workflow not found")
    import json as _json
    try:
        cfg = _json.loads(config)
    except Exception:
        cfg = {}
    node = WorkflowNode(
        node_type=node_type, label=label,
        config=cfg, position={"x": x, "y": y},
        credentials=credentials, notes=notes,
    )
    node_id = wf.add_node(node)
    workflow_store._save()
    return {"node_id": node_id, "node": node.to_dict()}


@router.patch("/{workflow_id}/nodes/{node_id}")
async def update_node(
    workflow_id: str,
    node_id: str,
    label: str | None = None,
    config: str | None = None,
    x: float | None = None,
    y: float | None = None,
    credentials: str | None = None,
    notes: str | None = None,
):
    wf = workflow_store.get(workflow_id)
    if not wf:
        raise HTTPException(status_code=404, detail="Workflow not found")
    kwargs = {}
    if label is not None:
        kwargs["label"] = label
    if config is not None:
        import json as _json
        try:
            kwargs["config"] = _json.loads(config)
        except Exception:
            pass
    if x is not None or y is not None:
        kwargs["position"] = {"x": x or 0, "y": y or 0}
    if credentials is not None:
        kwargs["credentials"] = credentials
    if notes is not None:
        kwargs["notes"] = notes
    node = wf.update_node(node_id, **kwargs)
    if not node:
        raise HTTPException(status_code=404, detail="Node not found")
    workflow_store._save()
    return {"node": node.to_dict()}


@router.delete("/{workflow_id}/nodes/{node_id}")
async def delete_node(workflow_id: str, node_id: str):
    wf = workflow_store.get(workflow_id)
    if not wf:
        raise HTTPException(status_code=404, detail="Workflow not found")
    wf.remove_node(node_id)
    workflow_store._save()
    return {"deleted": True}


# ── Edges ──


@router.post("/{workflow_id}/edges")
async def add_edge(
    workflow_id: str,
    source: str,
    target: str,
    label: str = "",
    sourceHandle: str = "",
    targetHandle: str = "",
):
    wf = workflow_store.get(workflow_id)
    if not wf:
        raise HTTPException(status_code=404, detail="Workflow not found")
    edge = WorkflowEdge(
        source=source, target=target, label=label,
        sourceHandle=sourceHandle, targetHandle=targetHandle,
    )
    edge_id = wf.add_edge(edge)
    workflow_store._save()
    return {"edge_id": edge_id, "edge": edge.to_dict()}


@router.delete("/{workflow_id}/edges/{edge_id}")
async def delete_edge(workflow_id: str, edge_id: str):
    wf = workflow_store.get(workflow_id)
    if not wf:
        raise HTTPException(status_code=404, detail="Workflow not found")
    wf.remove_edge(edge_id)
    workflow_store._save()
    return {"deleted": True}


# ── Credentials ──


@router.get("/credentials")
async def list_credentials():
    return {"credentials": credential_store.list()}


@router.post("/credentials")
async def create_credential(name: str, cred_type: str, data: str = "{}"):
    import json as _json
    try:
        d = _json.loads(data)
    except Exception:
        d = {}
    cred = credential_store.create(name=name, cred_type=cred_type, data=d)
    return {"credential": cred}


@router.get("/credentials/{cred_id}")
async def get_credential(cred_id: str):
    cred = credential_store.get(cred_id)
    if not cred:
        raise HTTPException(status_code=404, detail="Credential not found")
    return {"credential": cred}


@router.patch("/credentials/{cred_id}")
async def update_credential(cred_id: str, data: str = "{}"):
    import json as _json
    try:
        d = _json.loads(data)
    except Exception:
        d = {}
    cred = credential_store.update(cred_id, d)
    if not cred:
        raise HTTPException(status_code=404, detail="Credential not found")
    return {"credential": cred}


@router.delete("/credentials/{cred_id}")
async def delete_credential(cred_id: str):
    ok = credential_store.delete(cred_id)
    if not ok:
        raise HTTPException(status_code=404, detail="Credential not found")
    return {"deleted": True}


# ── Execution ──


@router.post("/{workflow_id}/execute")
async def execute_workflow(workflow_id: str, payload: dict = Body({})):
    result = workflow_store.execute_workflow(workflow_id, payload=payload)
    return result


# ── n8n Integration ──


@router.get("/n8n/status")
async def n8n_status():
    return {"online": False, "note": "Use export/import instead of live connection"}


@router.post("/n8n/import")
async def import_n8n(data: dict = Body(...)):
    try:
        wf = workflow_store.from_n8n_json(data)
        workflow_store._save()
        return {"workflow": wf.to_dict()}
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Import failed: {e}")


@router.get("/{workflow_id}/export/n8n")
async def export_n8n(workflow_id: str):
    result = workflow_store.to_n8n_json(workflow_id)
    if not result:
        raise HTTPException(status_code=404, detail="Workflow not found")
    return result


@router.get("/n8n/templates")
async def list_n8n_templates(
    category: str | None = None,
    query: str = "",
    offset: int = 0,
    limit: int = 50,
):
    return workflow_store.get_n8n_templates(
        category=category, query=query,
        offset=offset, limit=limit,
    )


@router.post("/n8n/templates/{template_id}/import")
async def import_n8n_template(template_id: str):
    wf = workflow_store.import_n8n_template(template_id)
    if not wf:
        raise HTTPException(status_code=404, detail="Template not found")
    return {"workflow": wf.to_dict()}


@router.post("/{workflow_id}/save-template")
async def save_as_template(workflow_id: str, tags: str = ""):
    tag_list = [t.strip() for t in tags.split(",") if t.strip()]
    tmpl = workflow_store.save_as_template(workflow_id, tags=tag_list)
    if not tmpl:
        raise HTTPException(status_code=404, detail="Workflow not found")
    return {"template": tmpl}


@router.post("/n8n/templates")
async def create_custom_template(
    name: str = Body(...), description: str = Body(""),
    category: str = Body("custom"), node_types: list[str] = Body(...),
    tags: list[str] = Body([]),
):
    tmpl = workflow_store.create_custom_template(
        name=name, description=description,
        category=category, node_types=node_types, tags=tags,
    )
    return {"template": tmpl}


@router.delete("/n8n/templates/{template_id}")
async def delete_custom_template(template_id: str):
    ok = workflow_store.delete_custom_template(template_id)
    if not ok:
        raise HTTPException(status_code=404, detail="Template not found")
    return {"deleted": True}
