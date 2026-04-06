import logging
from qdrant_client.http import models
from core.redis_client import redis_client
from services.retrieval_service import retrieve
from db.qdrant_db import qdrant_client, SEMANTIC_COLLECTION
from utils.helpers import make_cache_key, format_score

logger = logging.getLogger(__name__)

def rag_pipeline(query: str, generate_answer_fn, filter_keyword: str = None):
    query_clean = query.strip().lower()
    
    chunks, _ = retrieve(query_clean, filter_keyword=filter_keyword, limit=7)
    if not chunks:
        return {"answer": [], "sources": "None"}

    raw_sections = generate_answer_fn(query, chunks)
    
    final_answer_list = []
    source_tracker = {}

    for section in raw_sections:
        try:
            doc_id_val = section.get("doc_id")
            if doc_id_val is None: continue
            
            idx = int(doc_id_val) - 1
            if 0 <= idx < len(chunks):
                original_chunk = chunks[idx]
                fname = original_chunk.get("source", "Unknown")
                fscore = original_chunk.get("score", 0)

                # Format for the Frontend
                final_answer_list.append({
                    "title": section.get("title"),
                    "content": section.get("content"),
                    "source": fname,
                    "score": format_score(fscore)
                })

                source_tracker[fname] = max(fscore, source_tracker.get(fname, 0))
        except Exception as e:
            logger.warning(f"Mapping failed for a section: {e}")

    sources_str = ", ".join([f"{k} ({format_score(v)})" for k, v in source_tracker.items()])

    return {
        "answer": final_answer_list, 
        "sources": sources_str
    }