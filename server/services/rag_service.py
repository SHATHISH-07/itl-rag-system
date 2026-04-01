import logging
import json
from uuid import uuid4
from core.redis_client import redis_client
from db.qdrant_db import qdrant_client, SEMANTIC_COLLECTION
from services.retrieval_service import retrieve
from utils.helpers import get_embedding, make_cache_key, EMBEDDING_DIM

logger = logging.getLogger(__name__)
SIM_THRESHOLD = 0.90 

def fix_collection_dim():
    try:
        from qdrant_client.http import models
        info = qdrant_client.get_collection(SEMANTIC_COLLECTION)
        if info.config.params.vectors.size != EMBEDDING_DIM:
            logger.warning("Dimension mismatch detected. Recreating semantic_cache...")
            qdrant_client.delete_collection(SEMANTIC_COLLECTION)
            qdrant_client.create_collection(
                collection_name=SEMANTIC_COLLECTION,
                vectors_config=models.VectorParams(size=EMBEDDING_DIM, distance=models.Distance.COSINE)
            )
    except:
        from qdrant_client.http import models
        qdrant_client.create_collection(
            collection_name=SEMANTIC_COLLECTION,
            vectors_config=models.VectorParams(size=EMBEDDING_DIM, distance=models.Distance.COSINE)
        )

def rag_pipeline(query: str, generate_answer_fn):
    fix_collection_dim()
    query_clean = query.strip().lower()
    
    exact_key = make_cache_key("exact", query_clean)
    if redis_client:
        cached = redis_client.get(exact_key)
        if cached:
            logger.info("Exact Hit")
            return json.loads(cached)

    query_vector = get_embedding(query_clean)

    try:
        results = qdrant_client.query_points(
            collection_name=SEMANTIC_COLLECTION,
            query=query_vector,
            limit=1
        )
        if results.points and results.points[0].score >= SIM_THRESHOLD:
            logger.info(f"Semantic Hit: {results.points[0].score:.3f}")
            res = results.points[0].payload["response"]
            if redis_client: redis_client.setex(exact_key, 3600, json.dumps(res))
            return res
    except Exception as e:
        logger.error(f"Cache lookup failed: {e}")

    chunks, _ = retrieve(query_clean, query_vector)
    if not chunks:
        return {"answer": "No relevant information found."}

    answer = generate_answer_fn(query, chunks)
    response = {"answer": answer}

    if redis_client:
        redis_client.setex(exact_key, 3600, json.dumps(response))

    try:
        qdrant_client.upsert(
            collection_name=SEMANTIC_COLLECTION,
            points=[{
                "id": str(uuid4()),
                "vector": query_vector,
                "payload": {"query": query, "response": response}
            }]
        )
    except Exception as e:
        logger.error(f"Cache store failed: {e}")

    return response