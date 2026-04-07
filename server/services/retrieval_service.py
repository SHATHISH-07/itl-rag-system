import logging
import json
import numpy as np
from concurrent.futures import ThreadPoolExecutor
from rank_bm25 import BM25Okapi
from core.redis_client import redis_client
from db.qdrant_db import qdrant_client
from core.reranker import reranker
from utils.helpers import make_cache_key, get_collection_name, format_score
from core.embeddings import model

logger = logging.getLogger(__name__)

FINAL_THRESHOLD_GLOBAL = 0.40 

def safe_normalize(scores):
    """Normalizes scores to a 0.0 - 1.0 range safely."""
    if len(scores) == 0:
        return np.array([])
    s_min, s_max = np.min(scores), np.max(scores)
    if s_max == s_min:
        return np.ones_like(scores) 
    return (scores - s_min) / (s_max - s_min)

def retrieve(query: str, filter_keyword: str = None, limit: int = 7, offset: int = 0):
    query_clean = query.strip().lower()
    
    # FIX: Include 'limit' in cache key so k=3 and k=7 don't collide
    cache_id = f"{query_clean}:{filter_keyword or 'global'}:k{limit}"
    result_cache_key = make_cache_key("v_res", cache_id)
    
    if redis_client:
        cached = redis_client.get(result_cache_key)
        if cached:
            data = json.loads(cached)
            # Slice results to strictly respect current limit
            return data["results"][:limit], data["total"]

    # 1. Vector Search
    query_vector = model.encode([query_clean])[0].tolist()
    all_results = []
    
    try:
        if filter_keyword:
            collections = [{"name": get_collection_name(filter_keyword)}]
        else:
            collections = [col for col in qdrant_client.get_collections().collections 
                          if col.name not in ["file_metadata", "semantic_cache"]]

        def search_col(col_obj):
            col_name = col_obj.name if hasattr(col_obj, 'name') else col_obj['name']
            try:
                res = qdrant_client.query_points(
                    collection_name=col_name, 
                    query=query_vector, 
                    limit=25 # Retrieve slightly more for better reranking
                )
                return [{**dict(r.payload), "vector_score": max(0.0, min(1.0, float(r.score)))} for r in res.points]
            except Exception as e: 
                logger.error(f"Search failed in {col_name}: {e}")
                return []

        with ThreadPoolExecutor(max_workers=5) as exec:
            for r in exec.map(search_col, collections):
                all_results.extend(r)
    except Exception as e:
        logger.error(f"Retrieval error: {e}")
        return [], 0

    if not all_results: return [], 0

    # 2. Score Calculation & Hybrid Ranking
    # Filter unique chunks and take top 40 for reranking
    candidate_pool = sorted(all_results, key=lambda x: x["vector_score"], reverse=True)[:40]
    corpus = [c.get("text", "") for c in candidate_pool]
    
    # BM25 Component
    bm25 = BM25Okapi([d.lower().split() for d in corpus])
    bm_scores = bm25.get_scores(query_clean.split())
    bm_norm = safe_normalize(bm_scores)

    # Cross-Encoder Component (Reranker)
    rerank_count = min(15, len(candidate_pool))
    ce_scores = reranker.predict([[query_clean, corpus[i]] for i in range(rerank_count)])
    ce_norm = safe_normalize(ce_scores)

    # Final Hybrid Score Calculation
    for i in range(len(candidate_pool)):
        vec = candidate_pool[i]["vector_score"]
        bm = bm_norm[i]
        ce = ce_norm[i] if i < rerank_count else 0
        
        # Calculation: 50% Reranker, 30% BM25, 20% Vector
        raw_score = (ce * 0.50) + (bm * 0.30) + (vec * 0.20)
        candidate_pool[i]["score"] = round(float(raw_score), 4)

    # 3. Final Filtering & Sorting
    filtered = [c for c in candidate_pool if c.get("score", 0) >= FINAL_THRESHOLD_GLOBAL]
    filtered = sorted(filtered, key=lambda x: x["score"], reverse=True)

    # 4. Cache & Return
    if redis_client and filtered:
        redis_client.setex(result_cache_key, 600, json.dumps({"results": filtered, "total": len(filtered)}))

    return filtered[offset : offset + limit], len(filtered)