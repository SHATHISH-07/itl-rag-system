import logging
from fastapi import APIRouter
from pydantic import BaseModel
from typing import Optional
from services.rag_service import rag_pipeline
from services.llm_service import generate_answer

logger = logging.getLogger(__name__)

router = APIRouter()

class QueryRequest(BaseModel):
    query: str
    filter_keyword: Optional[str] = None 

@router.post("/query")
async def query_rag(request: QueryRequest):
    clean_query = request.query.strip() if request.query else ""
    
    if len(clean_query) < 3:
        logger.warning(f"Short query: '{clean_query}'")
        return {"answer": "Please provide a valid question."}

    logger.info(f"Query: '{clean_query}' | Filter: {request.filter_keyword or 'Global'}")

    try:
        response = rag_pipeline(
            query=clean_query,
            filter_keyword=request.filter_keyword,
            generate_answer_fn=lambda q, chunks: generate_answer(q, chunks)
        )

        final_answer = response.get("answer", "")
        sources_list = response.get("sources", "None")

        if sources_list != "None":
            final_answer += f"<br/><br/><p><b>Sources:</b> {sources_list}</p>"

        logger.info(f"Success: '{clean_query}'")

        return {
            "query": request.query,
            "answer": final_answer,
            "metadata": {
                "status": "success",
                "filter_applied": request.filter_keyword or "Global Search"
            }
        }

    except Exception as e:
        logger.error(f"Error: {str(e)}", exc_info=True)
        return {
            "answer": "Internal server error.", 
            "metadata": {"status": "error"}
        }