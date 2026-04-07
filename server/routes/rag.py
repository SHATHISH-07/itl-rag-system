from fastapi import APIRouter
from pydantic import BaseModel, Field
from typing import Optional
from services.rag_service import rag_pipeline
from services.llm_service import generate_answer

router = APIRouter()

class QueryRequest(BaseModel):
    query: str = Field(..., min_length=3)
    filter_keyword: Optional[str] = None
    top_k: int = 7 

@router.post("/query")
async def query_rag(request: QueryRequest):
    try:
        result = rag_pipeline(
            query=request.query,
            generate_answer_fn=generate_answer,
            filter_keyword=request.filter_keyword,
            top_k=request.top_k 
        )

        return {
            "query": request.query,
            "responses": result.get("responses", []),
            "metadata": {
                "status": "success" if result.get("responses") else "no_results",
                "filter_applied": request.filter_keyword or "Global",
                "global_sources": result.get("sources", "None"),
                "top_k_used": request.top_k 
            }
        }
    except Exception as e:
        return {"responses": [], "metadata": {"status": "error", "error": str(e)}}