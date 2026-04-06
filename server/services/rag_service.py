import logging
import json
import re
from core.redis_client import redis_client
from services.retrieval_service import retrieve
from utils.helpers import make_cache_key, format_score

logger = logging.getLogger(__name__)

def rag_pipeline(query: str, generate_answer_fn, filter_keyword: str = None):
    query_clean = query.strip().lower()

    cache_suffix = f":{filter_keyword}" if filter_keyword else ":global"
    exact_key = make_cache_key("exact", f"{query_clean}{cache_suffix}")
    if redis_client:
        cached = redis_client.get(exact_key)
        if cached: return json.loads(cached)

    chunks, _ = retrieve(query_clean, filter_keyword=filter_keyword)
    if not chunks:
        return {"answer": "I don't know based on the provided context.", "sources": "None"}

    raw_answer = generate_answer_fn(query, chunks)
    
    if "I don't know" in raw_answer:
        return {"answer": raw_answer, "sources": "None"}

    used_indices = set(re.findall(r"Doc (\d+)", raw_answer))
    final_answer = raw_answer
    used_sources_map = {}

    for idx_str in sorted(used_indices, key=int, reverse=True):
        idx = int(idx_str) - 1
        if idx < len(chunks):
            chunk = chunks[idx]
            filename = chunk.get("source", "Unknown")
            score = chunk.get("score", 0)
            
            if filename not in used_sources_map or score > used_sources_map[filename]:
                used_sources_map[filename] = score

            pattern = rf"\(?Source:\s?\[?Doc {idx_str}\]?\)?|\[Doc {idx_str}\]|Doc {idx_str}"
            replacement = f"<b>({filename} | Relevance: {format_score(score)})</b>"
            final_answer = re.sub(pattern, replacement, final_answer)

    for filename in used_sources_map.keys():
        esc_fn = re.escape(filename)
        double_pattern = rf"<b>\({esc_fn}.*?\)</b>(,\s?|/|,\s?and\s?)<b>\({esc_fn}.*?\)</b>"
        final_answer = re.sub(double_pattern, f"<b>({filename} | Relevance: {format_score(used_sources_map[filename])})</b>", final_answer)

    summary_list = [f"{name} ({format_score(score)})" for name, score in used_sources_map.items()]
    sources_str = ", ".join(summary_list) if summary_list else "None"

    response = {
        "answer": final_answer, 
        "sources": sources_str
    }

    if redis_client:
        redis_client.setex(exact_key, 3600, json.dumps(response))
    
    return response