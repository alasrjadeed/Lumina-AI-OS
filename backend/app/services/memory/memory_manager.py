import json
import logging
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


class MemoryEntry:
    def __init__(self, key: str, value: Any, namespace: str = "default", metadata: Optional[Dict] = None):
        self.key = key
        self.value = value
        self.namespace = namespace
        self.metadata = metadata or {}
        self.created_at = datetime.now(timezone.utc)

    def to_dict(self) -> Dict:
        return {
            "key": self.key,
            "value": self.value,
            "namespace": self.namespace,
            "metadata": self.metadata,
            "created_at": self.created_at.isoformat(),
        }


class MemoryManager:
    def __init__(self, storage_path: Optional[Path] = None):
        self._storage_path = storage_path or Path("./memory_store")
        self._in_memory: Dict[str, Dict[str, MemoryEntry]] = {}
        self._initialized = False

    async def initialize(self):
        self._storage_path.mkdir(parents=True, exist_ok=True)
        self._initialized = True
        logger.info(f"Memory Manager initialized at {self._storage_path}")

    async def shutdown(self):
        self._initialized = False
        logger.info("Memory Manager shutdown")

    async def store(self, key: str, value: Any, namespace: str = "default", metadata: Optional[Dict] = None):
        if namespace not in self._in_memory:
            self._in_memory[namespace] = {}
        entry = MemoryEntry(key=key, value=value, namespace=namespace, metadata=metadata)
        self._in_memory[namespace][key] = entry
        self._persist(namespace)
        return entry

    async def retrieve(self, key: str, namespace: str = "default") -> Optional[Any]:
        ns = self._in_memory.get(namespace, {})
        entry = ns.get(key)
        return entry.value if entry else None

    async def delete(self, key: str, namespace: str = "default") -> bool:
        ns = self._in_memory.get(namespace)
        if ns and key in ns:
            del ns[key]
            self._persist(namespace)
            return True
        return False

    async def list_namespace(self, namespace: str = "default") -> List[Dict]:
        ns = self._in_memory.get(namespace, {})
        return [e.to_dict() for e in ns.values()]

    async def search(self, query: str, namespace: str = "default") -> List[Dict]:
        ns = self._in_memory.get(namespace, {})
        results = []
        q = query.lower()
        for entry in ns.values():
            if q in entry.key.lower() or q in str(entry.value).lower():
                results.append(entry.to_dict())
        return results

    async def store_project_context(self, project_name: str, context: Dict[str, Any]):
        key = f"project:{project_name}"
        existing = await self.retrieve(key, namespace="projects") or {}
        existing.update(context)
        await self.store(key, existing, namespace="projects")

    async def get_project_context(self, project_name: str) -> Optional[Dict]:
        return await self.retrieve(f"project:{project_name}", namespace="projects")

    def _persist(self, namespace: str):
        try:
            path = self._storage_path / f"{namespace}.json"
            ns = self._in_memory.get(namespace, {})
            data = {k: v.to_dict() for k, v in ns.items()}
            path.write_text(json.dumps(data, indent=2, default=str))
        except Exception as e:
            logger.error(f"Memory persist failed: {e}")
