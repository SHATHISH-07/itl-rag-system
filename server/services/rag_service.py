import logging
import json
from uuid import uuid4
from core.redis_client import redis_client
from db.qdrant_db import qdrant_client, SEMANTIC_COLLECTION
from services.retrieval_service import retrieve
from utils.helpers import get_embedding, make_cache_key, EMBEDDING_DIM
from qdrant_client.http import models

logger = logging.getLogger(__name__)
SIM_THRESHOLD = 0.90 

def fix_collection_dim():
    try:
        info = qdrant_client.get_collection(SEMANTIC_COLLECTION)
        if info.config.params.vectors.size != EMBEDDING_DIM:
            qdrant_client.delete_collection(SEMANTIC_COLLECTION)
            raise Exception()
    except Exception:
        qdrant_client.create_collection(
            collection_name=SEMANTIC_COLLECTION,
            vectors_config=models.VectorParams(
                size=EMBEDDING_DIM, 
                distance=models.Distance.COSINE
            )
        )

def rag_pipeline(query: str, generate_answer_fn, filter_keyword: str = None):
    fix_collection_dim()
    
    keyword = filter_keyword.strip() if filter_keyword else None
    query_clean = query.strip().lower()
    
    cache_suffix = f":{keyword}" if keyword else ":global"
    exact_key = make_cache_key("exact", f"{query_clean}{cache_suffix}")
    
    if redis_client:
        cached = redis_client.get(exact_key)
        if cached: 
            return json.loads(cached)

    query_vector = get_embedding(query_clean)

    if not keyword:
        try:
            results = qdrant_client.query_points(
                collection_name=SEMANTIC_COLLECTION, 
                query=query_vector, 
                limit=1
            )
            if results.points and results.points[0].score >= SIM_THRESHOLD:
                return results.points[0].payload["response"]
        except:
            pass

    chunks, _ = retrieve(query_clean, filter_keyword=keyword)
    
    if not chunks:
        return {
            "answer": "I don't know based on the provided context." if keyword else "I couldn't find any relevant information.",
            "sources": "None"
        }

    top_score = chunks[0].get("score", 0)

    if keyword and top_score < 0.55:
        return {
            "answer": "I don't know based on the provided context.",
            "sources": "None"
        }

    if not keyword and top_score < 0.40:
        return {
            "answer": "I couldn't find any relevant information.",
            "sources": "None"
        }

    answer = generate_answer_fn(query, chunks)
    
    unique_sources = sorted(list(set(c.get("source") for c in chunks if c.get("source"))))
    sources_str = ", ".join(unique_sources)

    response = {"answer": answer, "sources": sources_str or "None"}

    if redis_client:
        redis_client.setex(exact_key, 3600, json.dumps(response))
    
    if not keyword:
        try:
            qdrant_client.upsert(
                collection_name=SEMANTIC_COLLECTION,
                points=[models.PointStruct(
                    id=str(uuid4()),
                    vector=query_vector,
                    payload={"query": query_clean, "response": response}
                )]
            )
        except:
            pass

    return response