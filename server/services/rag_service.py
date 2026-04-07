import logging
from services.retrieval_service import retrieve

logger = logging.getLogger(__name__)

def rag_pipeline(query: str, generate_answer_fn, filter_keyword: str = None, top_k: int = 7):
    chunks, _ = retrieve(query, filter_keyword=filter_keyword, limit=top_k)
    
    if not chunks:
        return {
            "query": query,
            "responses": [{"title": "Not Found", "content": "No data in database.", "source": "N/A", "score": "0%"}],
            "sources": "None"
        }

    llm_sections = generate_answer_fn(query, chunks)

    if not llm_sections or (len(llm_sections) == 1 and llm_sections[0].get("doc_id") == 0):
        return {
            "query": query,
            "responses": [{"title": "Not Found", "content": "Information not in context.", "source": "N/A", "score": "0%"}],
            "sources": "None"
        }

    final_answer_list = []
    source_tracker = {}

    for section in llm_sections:
        try:
            idx = int(section.get("doc_id", 0)) - 1
            if 0 <= idx < len(chunks):
                chunk = chunks[idx]
                name = chunk.get("source", "Unknown")
                score = chunk.get("score", 0)

                final_answer_list.append({
                    "title": section.get("title"),
                    "content": section.get("content"),
                    "source": name,
                    "score": f"{int(score * 100)}%"
                })
                source_tracker[name] = max(score, source_tracker.get(name, 0))
        except:
            continue

    if not final_answer_list:
        return {"query": query, "responses": [{"title": "Error", "content": "Processing failed.", "source": "N/A", "score": "0%"}], "sources": "None"}

    return {
        "query": query,
        "responses": final_answer_list,
        "sources": ", ".join([f"{k} ({int(v*100)}%)" for k, v in source_tracker.items()])
    }