from fastapi import APIRouter, Query
from pydantic import BaseModel
from services.rag_service import retrieve
from services.answer_service import generate_answer

router = APIRouter()

class QueryRequest(BaseModel):
    query: str
    filter_keyword: str = None 

@router.post("/query")
def query_rag(
    request: QueryRequest, 
    limit: int = Query(5, ge=1, le=20), 
    offset: int = Query(0, ge=0)
):
    filter_kw = request.filter_keyword if request.filter_keyword and request.filter_keyword.strip() else None

    results, total_count = retrieve(
        request.query, 
        filter_keyword=filter_kw,
        limit=limit,
        offset=offset
    )

    if not results:
        return {
            "query": request.query, 
            "answer": "I don't know based on the provided context.", 
            "total_matches": 0,
            "metadata": {"limit": limit, "offset": offset, "sources": []}
        }

    answer = generate_answer(request.query, results)
    
    sources = list(set([r.get("source", "Unknown") for r in results]))

    return {
        "query": request.query,
        "answer": answer,
        "total_matches": total_count,
        "metadata": {
            "limit": limit,
            "offset": offset,
            "sources": sources,
            "has_more": total_count > (offset + limit)
        }
    }