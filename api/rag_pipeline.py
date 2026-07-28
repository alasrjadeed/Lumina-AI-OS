from fastapi import APIRouter, HTTPException

from core.rag_pipeline import rag

router = APIRouter(prefix="/rag", tags=["RAG Pipeline"])


@router.post("/ingest")
async def ingest_text(title: str, content: str, source: str = "manual"):
    result = rag.ingest_text(title=title, content=content, source=source)
    return {"document": result}


@router.get("/documents")
async def list_documents():
    return {"documents": rag.list_documents()}


@router.get("/documents/{doc_id}")
async def get_document(doc_id: str):
    doc = rag.get_document(doc_id)
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")
    return {"document": doc}


@router.delete("/documents/{doc_id}")
async def delete_document(doc_id: str):
    ok = rag.delete_document(doc_id)
    return {"deleted": ok}


@router.get("/search")
async def search(q: str, top_k: int = 10):
    results = rag.search(q, top_k=top_k)
    return {"query": q, "results": results, "count": len(results)}


@router.get("/stats")
async def get_stats():
    return rag.get_stats()
