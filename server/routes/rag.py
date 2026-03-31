import re
import logging
from fastapi import APIRouter, Query, HTTPException
from pydantic import BaseModel
from services.rag_service import retrieve
from services.llm_service import generate_answer

logger = logging.getLogger("rag_query")
router = APIRouter()

class QueryRequest(BaseModel):
    query: str
    filter_keyword: str = None 

@router.post("/query")
async def query_rag(
    request: QueryRequest, 
    limit: int = Query(5, ge=1, le=20), 
    offset: int = Query(0, ge=0)
):
    #  INPUT VALIDATION & NOISE FILTER
    clean_query = request.query.strip() if request.query else ""
  
    is_noise = not bool(re.search(r'[a-zA-Z0-9]', clean_query))

    if not clean_query or len(clean_query) < 3 or is_noise:
        logger.warning(f"Blocked invalid/noise query: '{clean_query}'")
        return {
            "query": request.query,
            "answer": "Please provide a valid question to get started.",
            "total_matches": 0,
            "metadata": {"sources": [], "status": "invalid_input"}
        }

    try:
        # RETRIEVAL
        filter_kw = request.filter_keyword.strip() if request.filter_keyword and request.filter_keyword.strip() else None
        results, total_count = retrieve(clean_query, filter_keyword=filter_kw, limit=limit, offset=offset)

        if not results:
            return {
                "query": request.query, 
                "answer": "I don't know based on the provided context.", 
                "total_matches": 0,
                "metadata": {"sources": []}
            }

        # GENERATE ANSWER
        answer = generate_answer(clean_query, results)

        # SOURCE ATTRIBUTION CLEANUP
        no_info_phrases = ["don't know", "not mentioned", "no information", "does not mention"]
        found_no_info = any(phrase in answer.lower() for phrase in no_info_phrases)

        if found_no_info:
            final_sources = []
            status_msg = "No relevant context found"
        else:
            final_sources = list(set([r.get("source", "Unknown") for r in results if r.get("score", 0) > 0.40]))
            status_msg = "Success"

        return {
            "query": request.query,
            "answer": answer,
            "total_matches": total_count,
            "metadata": {
                "limit": limit,
                "offset": offset,
                "sources": final_sources,
                "status": status_msg
            }
        }

    except Exception as e:
        logger.error(f"RAG Error: {str(e)}", exc_info=True)
        return {"query": request.query, "answer": "Internal server error.", "metadata": {"error": str(e)}}