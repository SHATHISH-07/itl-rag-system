import logging
from services.retrieval_service import retrieve
from utils.helpers import format_score

logger = logging.getLogger(__name__)

def rag_pipeline(query: str, generate_answer_fn, filter_keyword: str = None, top_k: int = 7):
    chunks, _ = retrieve(query, filter_keyword=filter_keyword, limit=top_k)
    
    if not chunks:
        return {
            "responses": [], 
            "sources": "None", 
            "message": "No matching information found in the database."
        }

    raw_sections = generate_answer_fn(query, chunks)

    if isinstance(raw_sections, dict) and raw_sections.get("status") == "no_relevant_data":
        return {"responses": [], "sources": "None", "message": raw_sections.get("answer")}

    final_answer_list = []
    source_tracker = {}

    sections = raw_sections if isinstance(raw_sections, list) else [raw_sections]

    for idx, section in enumerate(sections):
        try:
            doc_id = section.get("doc_id")
            chunk_idx = (int(doc_id) - 1) if doc_id is not None else idx
            
            if 0 <= chunk_idx < len(chunks):
                chunk = chunks[chunk_idx]
                fname = chunk.get("source", "Unknown")
                fscore = chunk.get("score", 0)

                final_answer_list.append({
                    "title": section.get("title", "Analysis"),
                    "content": section.get("content", ""),
                    "source": fname,
                    "score": format_score(fscore)
                })
                source_tracker[fname] = max(fscore, source_tracker.get(fname, 0))
        except Exception as e:
            logger.error(f"Mapping error: {e}")

    return {
        "responses": final_answer_list,
        "sources": ", ".join([f"{k} ({format_score(v)})" for k, v in source_tracker.items()])
    }