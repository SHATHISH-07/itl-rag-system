import re
import logging
from fastapi import APIRouter, Query
from pydantic import BaseModel
from typing import Optional

from services.rag_service import rag_pipeline
from services.llm_service import generate_answer

logger = logging.getLogger("rag_query")
router = APIRouter()

class QueryRequest(BaseModel):
    query: str
    filter_keyword: Optional[str] = None 

@router.post("/query")
async def query_rag(
    request: QueryRequest,
    limit: int = Query(5, ge=1, le=20),
    offset: int = Query(0, ge=0)
):
    clean_query = request.query.strip() if request.query else ""
    is_noise = not bool(re.search(r'[a-zA-Z0-9]', clean_query))

    if not clean_query or len(clean_query) < 3 or is_noise:
        return {"answer": "Please provide a valid question."}

    try:
        response = rag_pipeline(
            query=clean_query,
            filter_keyword=request.filter_keyword,
            generate_answer_fn=lambda q, chunks: generate_answer(q, chunks)
        )

        return {
            "query": request.query,
            "answer": response.get("answer", ""),
            "sources": response.get("sources", "None"),
            "metadata": {
                "status": "success",
                "filter_applied": request.filter_keyword or "Global Search"
            }
        }

    except Exception as e:
        logger.error(f"RAG Error: {str(e)}", exc_info=True)
        return {"answer": "Internal server error.", "metadata": {"error": str(e)}}