"""Visual Agent Flows — drag-and-drop multi-agent workflow builder."""

from __future__ import annotations

import json
import os
import time
from dataclasses import dataclass, field

from core.log import log

FLOWS_DIR = os.path.expanduser("~/.lumina/flows")


@dataclass
class FlowNode:
    id: str
    type: str
    label: str
    x: float = 0
    y: float = 0
    config: dict = field(default_factory=dict)

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "type": self.type,
            "label": self.label,
            "x": self.x,
            "y": self.y,
            "config": self.config,
        }

    @classmethod
    def from_dict(cls, d: dict) -> FlowNode:
        return cls(
            id=d["id"],
            type=d["type"],
            label=d.get("label", d["type"]),
            x=d.get("x", 0),
            y=d.get("y", 0),
            config=d.get("config", {}),
        )


@dataclass
class FlowEdge:
    id: str
    source: str
    target: str
    label: str = ""
    condition: str = ""

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "source": self.source,
            "target": self.target,
            "label": self.label,
            "condition": self.condition,
        }

    @classmethod
    def from_dict(cls, d: dict) -> FlowEdge:
        return cls(
            id=d["id"],
            source=d["source"],
            target=d["target"],
            label=d.get("label", ""),
            condition=d.get("condition", ""),
        )


@dataclass
class VisualFlow:
    id: str
    name: str
    description: str = ""
    nodes: list[FlowNode] = field(default_factory=list)
    edges: list[FlowEdge] = field(default_factory=list)
    created_at: float = 0.0
    updated_at: float = 0.0
    run_count: int = 0
    last_run: float = 0.0

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "nodes": [n.to_dict() for n in self.nodes],
            "edges": [e.to_dict() for e in self.edges],
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "run_count": self.run_count,
            "last_run": self.last_run,
        }

    @classmethod
    def from_dict(cls, d: dict) -> VisualFlow:
        return cls(
            id=d["id"],
            name=d["name"],
            description=d.get("description", ""),
            nodes=[FlowNode.from_dict(n) for n in d.get("nodes", [])],
            edges=[FlowEdge.from_dict(e) for e in d.get("edges", [])],
            created_at=d.get("created_at", 0),
            updated_at=d.get("updated_at", 0),
            run_count=d.get("run_count", 0),
            last_run=d.get("last_run", 0),
        )


AGENT_PALETTE = [
    {
        "type": "input",
        "label": "User Input",
        "color": "#6366f1",
        "description": "Starting point — user's request",
    },
    {
        "type": "ceo",
        "label": "CEO AI",
        "color": "#f59e0b",
        "description": "Orchestrator — plans and assigns tasks",
    },
    {
        "type": "planner",
        "label": "Planner",
        "color": "#8b5cf6",
        "description": "Task decomposition and milestones",
    },
    {
        "type": "programmer",
        "label": "Programmer",
        "color": "#22c55e",
        "description": "Full-stack code generation",
    },
    {
        "type": "tester",
        "label": "Tester",
        "color": "#ef4444",
        "description": "QA, unit/integration tests",
    },
    {
        "type": "debugger",
        "label": "Debugger",
        "color": "#f97316",
        "description": "Root cause analysis and fixes",
    },
    {
        "type": "designer",
        "label": "Designer",
        "color": "#ec4899",
        "description": "UI/UX and visual design",
    },
    {
        "type": "database_engineer",
        "label": "Database Engineer",
        "color": "#06b6d4",
        "description": "Schema, queries, migrations",
    },
    {
        "type": "devops_engineer",
        "label": "DevOps Engineer",
        "color": "#14b8a6",
        "description": "CI/CD, Docker, K8s",
    },
    {
        "type": "security_auditor",
        "label": "Security Auditor",
        "color": "#dc2626",
        "description": "Vulnerability assessment",
    },
    {
        "type": "marketing_agent",
        "label": "Marketing Agent",
        "color": "#a855f7",
        "description": "Campaigns, SEO, content",
    },
    {
        "type": "documentation_writer",
        "label": "Documentation Writer",
        "color": "#64748b",
        "description": "API docs, guides, ADRs",
    },
    {
        "type": "output",
        "label": "Output / Report",
        "color": "#3b82f6",
        "description": "Final output — synthesized result",
    },
]


class FlowManager:
    """CRUD and execution for visual agent flows."""

    def __init__(self):
        self._flows: dict[str, VisualFlow] = {}
        os.makedirs(FLOWS_DIR, exist_ok=True)
        self._load()

    def _path(self) -> str:
        return os.path.join(FLOWS_DIR, "flows.json")

    def _load(self):
        path = self._path()
        if os.path.exists(path):
            try:
                with open(path) as f:
                    data = json.load(f)
                for d in data:
                    flow = VisualFlow.from_dict(d)
                    self._flows[flow.id] = flow
            except Exception:
                pass

    def _save(self):
        with open(self._path(), "w") as f:
            json.dump([f.to_dict() for f in self._flows.values()], f, indent=2)

    def list(self) -> list[VisualFlow]:
        return sorted(self._flows.values(), key=lambda f: f.updated_at, reverse=True)

    def get(self, flow_id: str) -> VisualFlow | None:
        return self._flows.get(flow_id)

    def create(
        self,
        name: str,
        description: str = "",
        nodes: list[dict] | None = None,
        edges: list[dict] | None = None,
    ) -> VisualFlow:
        import uuid

        fid = uuid.uuid4().hex[:12]
        now = time.time()
        flow = VisualFlow(
            id=fid,
            name=name,
            description=description,
            nodes=[FlowNode.from_dict(n) for n in (nodes or [])],
            edges=[FlowEdge.from_dict(e) for e in (edges or [])],
            created_at=now,
            updated_at=now,
        )
        self._flows[fid] = flow
        self._save()
        log.info("Flow: created '%s' with %d nodes", name, len(flow.nodes))
        return flow

    def update(self, flow_id: str, **kwargs) -> VisualFlow | None:
        flow = self._flows.get(flow_id)
        if not flow:
            return None
        for k, v in kwargs.items():
            if k == "nodes" and isinstance(v, list):
                flow.nodes = [FlowNode.from_dict(n) for n in v]
            elif k == "edges" and isinstance(v, list):
                flow.edges = [FlowEdge.from_dict(e) for e in v]
            elif hasattr(flow, k):
                setattr(flow, k, v)
        flow.updated_at = time.time()
        self._save()
        return flow

    def delete(self, flow_id: str) -> bool:
        if flow_id in self._flows:
            del self._flows[flow_id]
            self._save()
            return True
        return False

    async def execute(self, flow_id: str, input_text: str = "") -> dict:
        """Execute a visual flow by walking nodes and edges sequentially."""
        flow = self._flows.get(flow_id)
        if not flow:
            return {"error": "Flow not found"}

        if not flow.nodes:
            return {"error": "Flow has no nodes"}

        input_nodes = [n for n in flow.nodes if n.type == "input"]
        start_text = (
            input_text or input_nodes[0].config.get("text", "") if input_nodes else input_text
        )

        if not start_text:
            return {"error": "No input text provided"}

        {n.id: n for n in flow.nodes}
        execution_order = self._topological_sort(flow.nodes, flow.edges)
        results: dict[str, dict] = {}

        flow.run_count += 1
        flow.last_run = time.time()
        flow.updated_at = time.time()
        self._save()

        current_input = start_text

        for node in execution_order:
            if node.type in ("input",):
                results[node.id] = {"status": "input", "output": current_input}
                continue

            if node.type == "output":
                results[node.id] = {"status": "collected", "output": current_input}
                continue

            task = node.config.get("task", current_input)

            try:
                from core.agents.runner import runner

                agent_id = self._map_to_agent(node.type)
                run = await runner.run(agent_id, task, {"flow_id": flow_id})
                results[node.id] = {
                    "status": run.status,
                    "output": run.output[:2000],
                    "error": run.error,
                    "agent": agent_id,
                }
                if run.status == "success":
                    current_input = run.output[:2000]
            except Exception as e:
                results[node.id] = {"status": "error", "output": "", "error": str(e)}

        output_nodes = [n for n in flow.nodes if n.type == "output"]
        final_output = (
            results.get(output_nodes[0].id, {}).get("output", "") if output_nodes else current_input
        )

        return {
            "flow_id": flow_id,
            "flow_name": flow.name,
            "input": start_text,
            "output": final_output,
            "node_results": results,
            "nodes_executed": len(execution_order),
        }

    def _topological_sort(self, nodes: list[FlowNode], edges: list[FlowEdge]) -> list[FlowNode]:
        node_map = {n.id: n for n in nodes}
        in_degree: dict[str, int] = {n.id: 0 for n in nodes}
        adj: dict[str, list[str]] = {n.id: [] for n in nodes}

        for edge in edges:
            if edge.source in adj and edge.target in in_degree:
                adj[edge.source].append(edge.target)
                in_degree[edge.target] += 1

        queue = [nid for nid, deg in in_degree.items() if deg == 0]
        result = []

        while queue:
            nid = queue.pop(0)
            if nid in node_map:
                result.append(node_map[nid])
            for neighbor in adj.get(nid, []):
                in_degree[neighbor] -= 1
                if in_degree[neighbor] == 0:
                    queue.append(neighbor)

        for n in nodes:
            if n not in result:
                result.append(n)

        return result

    def _map_to_agent(self, nodetype: str) -> str:
        mapping = {
            "ceo": "ceo",
            "planner": "planner",
            "programmer": "programmer",
            "tester": "tester",
            "debugger": "debugger",
            "designer": "designer",
            "database_engineer": "database_engineer",
            "devops_engineer": "devops_engineer",
            "security_auditor": "security_auditor",
            "marketing_agent": "marketing_agent",
            "documentation_writer": "documentation_writer",
        }
        return mapping.get(nodetype, "planner")

    def get_palette(self) -> list[dict]:
        return AGENT_PALETTE

    def stats(self) -> dict:
        return {
            "total_flows": len(self._flows),
            "total_runs": sum(f.run_count for f in self._flows.values()),
            "nodes_total": sum(len(f.nodes) for f in self._flows.values()),
        }


flow_manager = FlowManager()
