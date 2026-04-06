from fastapi import APIRouter
from pydantic import BaseModel
from typing import Optional, List, Any
from services.rag_service import rag_pipeline
from services.llm_service import generate_answer

router = APIRouter()

class QueryRequest(BaseModel):
    query: str
    filter_keyword: Optional[str] = None

@router.post("/query")
async def query_rag(request: QueryRequest):
    clean_query = (request.query or "").strip()
    if len(clean_query) < 3:
        return {"answer": [], "metadata": {"status": "failed", "msg": "Query too short"}}

    try:

        result = rag_pipeline(
            query=clean_query,
            filter_keyword=request.filter_keyword,
            generate_answer_fn=lambda q, chunks: generate_answer(q, chunks)
        )

        return {
            "query": request.query,
            "answer": result.get("answer", []),  
            "metadata": {
                "status": "success",
                "filter_applied": request.filter_keyword or "Global",
                "cached": result.get("cached", False),
                "global_sources": result.get("sources", "None")
            }
        }
    except Exception as e:
        return {"answer": [], "metadata": {"status": "error", "error": str(e)}}