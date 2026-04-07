import logging
import json
import numpy as np
import redis
from concurrent.futures import ThreadPoolExecutor
from rank_bm25 import BM25Okapi
from db.qdrant_db import qdrant_client
from core.reranker import reranker
from core.embeddings import model
from utils.helpers import get_collection_name
from core.redis_client import redis_client

logger = logging.getLogger(__name__)

CACHE_EXPIRATION = 3600  # 1 hour

FINAL_THRESHOLD_GLOBAL = 0.38 

def retrieve(query: str, filter_keyword: str = None, limit: int = 7):
    query_clean = query.strip().lower()
    
    cache_key = f"retrieval:{query_clean}:{filter_keyword or 'global'}"
    cached_data = redis_client.get(cache_key)
    if cached_data:
        logger.info(f"Redis Cache Hit for retrieval: {query_clean}")
        return json.loads(cached_data), 0 # Returning cached list

    query_vec = model.encode([query_clean])[0].tolist()
    all_results = []
    
    try:
        all_cols = [get_collection_name(filter_keyword)] if filter_keyword else \
                   [c.name for c in qdrant_client.get_collections().collections if c.name not in ["file_metadata"]]
        
        with ThreadPoolExecutor(max_workers=10) as executor:
            def fetch(col):
                res = qdrant_client.query_points(collection_name=col, query=query_vec, limit=50)
                return [{**dict(r.payload), "vector_score": float(r.score)} for r in res.points]
            
            for results in executor.map(fetch, all_cols):
                all_results.extend(results)
    except Exception as e:
        logger.error(f"Error: {e}")

    if not all_results: return [], 0

    # Deduplication & Scoring logic...
    seen = set()
    dedup = [r for r in all_results if not (r.get("text") in seen or seen.add(r.get("text")))]
    
    corpus = [c.get("text", "").lower() for c in dedup]
    bm25 = BM25Okapi([doc.split() for doc in corpus])
    bm_scores = safe_normalize(bm25.get_scores(query_clean.split()))
    v_scores = safe_normalize(np.array([c.get("vector_score", 0) for c in dedup]))

    top_indices = np.argsort((v_scores * 0.4) + (bm_scores * 0.6))[::-1][:20]
    ce_inputs = [[query_clean, corpus[i]] for i in top_indices]
    
    ce_scores_raw = reranker.predict(ce_inputs)
    ce_scores = safe_normalize(ce_scores_raw)
    
    final_candidates = []
    for i, idx in enumerate(top_indices):
        final_score = (ce_scores[i] * 0.7) + (bm_scores[idx] * 0.2) + (v_scores[idx] * 0.1)
        if ce_scores_raw[i] < -8.0: continue
        if final_score >= FINAL_THRESHOLD_GLOBAL:
            chunk = dedup[idx]
            chunk["score"] = round(float(final_score), 4)
            final_candidates.append(chunk)

    sorted_results = sorted(final_candidates, key=lambda x: x["score"], reverse=True)[:limit]

    redis_client.setex(cache_key, CACHE_EXPIRATION, json.dumps(sorted_results))
    
    return sorted_results, len(final_candidates)

def safe_normalize(scores):
    if len(scores) == 0: return np.array([])
    s_min, s_max = np.min(scores), np.max(scores)
    return (scores - s_min) / (s_max - s_min) if s_max > s_min else np.ones_like(scores)