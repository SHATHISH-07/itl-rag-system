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
    """Ensures the semantic cache collection exists with correct dimensions."""
    try:
        info = qdrant_client.get_collection(SEMANTIC_COLLECTION)
        if info.config.params.vectors.size != EMBEDDING_DIM:
            logger.warning(f"Dimension mismatch in {SEMANTIC_COLLECTION}. Recreating...")
            qdrant_client.delete_collection(SEMANTIC_COLLECTION)
            raise Exception("Trigger recreation")
    except Exception:
        logger.info(f"Creating collection: {SEMANTIC_COLLECTION}")
        qdrant_client.create_collection(
            collection_name=SEMANTIC_COLLECTION,
            vectors_config=models.VectorParams(
                size=EMBEDDING_DIM, 
                distance=models.Distance.COSINE
            )
        )

def rag_pipeline(query: str, generate_answer_fn, filter_keyword: str = None):
    # Ensure collection exists
    fix_collection_dim()
    
    # Normalize inputs
    keyword = keyword = filter_keyword.strip() if filter_keyword else None
    query_clean = query.strip().lower()
    
    # 1. Exact Match Cache (Redis)
    # Cache key includes the keyword to differentiate between global/filtered results
    cache_suffix = f":{keyword}" if keyword else ":global"
    exact_key = make_cache_key("exact", f"{query_clean}{cache_suffix}")
    
    if redis_client:
        cached = redis_client.get(exact_key)
        if cached: 
            logger.info(f"Exact cache hit for {cache_suffix}")
            return json.loads(cached)

    # 2. Semantic Cache (Qdrant)
    # IMPORTANT: We only use semantic cache for GLOBAL searches.
    # File-specific searches need fresh retrieval.
    query_vector = get_embedding(query_clean)
    if not keyword:
        try:
            results = qdrant_client.query_points(
                collection_name=SEMANTIC_COLLECTION, 
                query=query_vector, 
                limit=1
            )
            if results.points and results.points[0].score >= SIM_THRESHOLD:
                logger.info("Semantic cache hit")
                return results.points[0].payload["response"]
        except Exception as e: 
            logger.error(f"Semantic cache query error: {e}")

    # 3. Retrieval & Generation
    chunks, _ = retrieve(query_clean, filter_keyword=keyword)
    
    if not chunks:
        # Fallback response if nothing is found
        return {
            "answer": f"I couldn't find any information regarding that in <b>{keyword}</b>." if keyword else "I couldn't find any information globally.", 
            "sources": "None"
        }

    # Generate answer using provided LLM function
    answer = generate_answer_fn(query, chunks)
    
    # Unique sorted sources
    unique_sources = sorted(list(set(c.get("source") for c in chunks if c.get("source"))))
    sources_str = ", ".join(unique_sources)

    response = {"answer": answer, "sources": sources_str or "None"}

    # 4. Update Caches
    if redis_client:
        redis_client.setex(exact_key, 3600, json.dumps(response))
    
    # Only save to semantic cache if it was a global query to avoid polluting global cache
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
        except Exception as e:
            logger.error(f"Failed to update semantic cache: {e}")

    return response