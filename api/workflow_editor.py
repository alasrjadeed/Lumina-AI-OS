from fastapi import APIRouter, HTTPException, Body, Query

from core.workflow_editor import WorkflowEdge, WorkflowNode, workflow_store

router = APIRouter(prefix="/workflows", tags=["Workflow Editor"])


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
async def update_workflow(workflow_id: str, name: str | None = None, description: str | None = None, category: str | None = None):
    kwargs = {}
    if name is not None:
        kwargs["name"] = name
    if description is not None:
        kwargs["description"] = description
    if category is not None:
        kwargs["category"] = category
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


@router.post("/{workflow_id}/nodes")
async def add_node(workflow_id: str, node_type: str, label: str, config: str = "{}", x: float = 0, y: float = 0):
    wf = workflow_store.get(workflow_id)
    if not wf:
        raise HTTPException(status_code=404, detail="Workflow not found")
    import json as _json
    try:
        cfg = _json.loads(config)
    except Exception:
        cfg = {}
    node = WorkflowNode(node_type=node_type, label=label, config=cfg, position={"x": x, "y": y})
    node_id = wf.add_node(node)
    workflow_store._save()
    return {"node_id": node_id, "node": node.to_dict()}


@router.patch("/{workflow_id}/nodes/{node_id}")
async def update_node(workflow_id: str, node_id: str, label: str | None = None, config: str | None = None, x: float | None = None, y: float | None = None):
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
        pos = {"x": x or 0, "y": y or 0}
        kwargs["position"] = pos
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


@router.post("/{workflow_id}/edges")
async def add_edge(workflow_id: str, source: str, target: str, label: str = ""):
    wf = workflow_store.get(workflow_id)
    if not wf:
        raise HTTPException(status_code=404, detail="Workflow not found")
    edge = WorkflowEdge(source=source, target=target, label=label)
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
async def list_n8n_templates(category: str | None = None, query: str = ""):
    return {"templates": workflow_store.get_n8n_templates(category=category, query=query)}


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


@router.delete("/n8n/templates/{template_id}")
async def delete_custom_template(template_id: str):
    ok = workflow_store.delete_custom_template(template_id)
    if not ok:
        raise HTTPException(status_code=404, detail="Template not found")
    return {"deleted": True}


@router.post("/{workflow_id}/execute")
async def execute_workflow(workflow_id: str, payload: dict = Body({})):
    result = workflow_store.execute_workflow(workflow_id, payload=payload)
    return result


# ── Deprecated n8n endpoints (return messages) ──


@router.post("/n8n/install")
async def install_n8n():
    return {"success": False, "error": "n8n is not bundled — install separately with: npm install -g n8n"}


@router.post("/{workflow_id}/push-n8n")
async def push_to_n8n(workflow_id: str):
    return {"success": False, "error": "Live push not available — export as JSON and import manually into n8n"}


@router.post("/{workflow_id}/execute-n8n")
async def execute_on_n8n(workflow_id: str):
    return {"success": False, "error": "Live execution not available — use /execute to run locally"}


@router.get("/n8n/workflows")
async def list_n8n_workflows():
    return {"success": False, "error": "Remote n8n workflows not available — use templates and import/export instead"}
