import logging
from fastapi import APIRouter, Query
from pydantic import BaseModel
from services.rag_service import retrieve
from services.llm_service import generate_answer

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
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
    logger.info(f"Received query request: '{request.query}' (filter: {request.filter_keyword})")
    
    filter_kw = request.filter_keyword if request.filter_keyword and request.filter_keyword.strip() else None

    try:
        logger.info(f"Retrieving documents with limit={limit}, offset={offset}")
        results, total_count = retrieve(
            request.query, 
            filter_keyword=filter_kw,
            limit=limit,
            offset=offset
        )
        
        logger.info(f"Retrieved {len(results)} documents out of {total_count} total matches")

        if not results:
            logger.warning(f"No documents found for query: '{request.query}'")
            return {
                "query": request.query, 
                "answer": "I don't know based on the provided context.", 
                "total_matches": 0,
                "metadata": {"limit": limit, "offset": offset, "sources": []}
            }

        logger.info("Generating answer from LLM...")
        answer = generate_answer(request.query, results)
        
        sources = list(set([r.get("source", "Unknown") for r in results]))
        logger.info(f"Successfully generated answer. Sources used: {sources}")

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

    except Exception as e:
        logger.error(f"Error during RAG process for query '{request.query}': {str(e)}", exc_info=True)
        return {
            "query": request.query,
            "answer": "An internal error occurred while processing your request.",
            "total_matches": 0,
            "metadata": {"error": str(e)}
        }