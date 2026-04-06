import logging
import json
import re
import uuid
from qdrant_client.http import models
from core.redis_client import redis_client
from services.retrieval_service import retrieve
from db.qdrant_db import qdrant_client, SEMANTIC_COLLECTION
from utils.helpers import make_cache_key, format_score, enforce_section_citations
from core.embeddings import model as embedding_model

logger = logging.getLogger(__name__)

SIMILARITY_THRESHOLD = 0.90

def rag_pipeline(query: str, generate_answer_fn, filter_keyword: str = None):
    query_clean = query.strip().lower()
    cache_suffix = f":{filter_keyword}" if filter_keyword else ":global"

    exact_key = make_cache_key("exact_response", f"{query_clean}{cache_suffix}")

    if redis_client:
        cached = redis_client.get(exact_key)
        if cached:
            return json.loads(cached)

    query_vector = embedding_model.encode(query_clean).tolist()

    try:
        hits = qdrant_client.query_points(
            collection_name=SEMANTIC_COLLECTION,
            query=query_vector,
            limit=1
        ).points

        if hits and hits[0].score >= SIMILARITY_THRESHOLD:
            payload = hits[0].payload
            return {
                "answer": payload.get("answer"),
                "sources": payload.get("sources"),
                "cached": True
            }
    except Exception as e:
        logger.error(f"Semantic cache error: {e}")

    chunks, _ = retrieve(query_clean, filter_keyword=filter_keyword)

    if not chunks:
        return {
            "answer": "I don't know based on the provided context.",
            "sources": "None"
        }

    llm_answer = generate_answer_fn(query, chunks)

    llm_answer = enforce_section_citations(llm_answer)

    if "I don't know" in llm_answer:
        return {"answer": llm_answer, "sources": "None"}

    doc_ids = [
        int(d) for d in re.findall(r"Doc (\d+)", llm_answer)
        if int(d) <= len(chunks)
    ]

    source_map = {}
    final_text = llm_answer

    for doc_id in sorted(set(doc_ids), reverse=True):
        idx = doc_id - 1
        chunk = chunks[idx]

        fname = chunk.get("source", "Unknown")
        score = chunk.get("score", 0)

        source_map[fname] = max(score, source_map.get(fname, 0))

        replacement = f"<b>({fname} | {format_score(score)})</b>"

        final_text = re.sub(rf"\[Doc {doc_id}\]", replacement, final_text)

    sources_str = ", ".join(
        f"{fname} ({format_score(score)})"
        for fname, score in source_map.items()
    ) if source_map else "None"

    response = {
        "answer": final_text,
        "sources": sources_str
    }

    if redis_client:
        redis_client.setex(exact_key, 3600, json.dumps(response))

    try:
        qdrant_client.upsert(
            collection_name=SEMANTIC_COLLECTION,
            points=[
                models.PointStruct(
                    id=str(uuid.uuid4()),
                    vector=query_vector,
                    payload={
                        "query": query_clean,
                        "answer": final_text,
                        "sources": sources_str
                    }
                )
            ]
        )
    except Exception as e:
        logger.error(f"Semantic cache insert error: {e}")

    return response