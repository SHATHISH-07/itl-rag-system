import logging
import json
import numpy as np
from concurrent.futures import ThreadPoolExecutor
from rank_bm25 import BM25Okapi
from db.qdrant_db import qdrant_client
from core.reranker import reranker
from core.embeddings import model
from utils.helpers import get_collection_name

logger = logging.getLogger(__name__)

FINAL_THRESHOLD_GLOBAL = 0.38 

def safe_normalize(scores):
    if len(scores) == 0: return np.array([])
    s_min, s_max = np.min(scores), np.max(scores)
    if s_max == s_min: return np.ones_like(scores)
    return (scores - s_min) / (s_max - s_min)

def retrieve(query: str, filter_keyword: str = None, limit: int = 7):
    query_clean = query.strip().lower()
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

    seen = set()
    dedup = []
    for r in all_results:
        text = r.get("text", "").strip()
        if text and text not in seen:
            seen.add(text)
            dedup.append(r)

    corpus = [c.get("text", "").lower() for c in dedup]
    bm25 = BM25Okapi([doc.split() for doc in corpus])
    
    bm_scores = safe_normalize(bm25.get_scores(query_clean.split()))
    v_scores = safe_normalize(np.array([c.get("vector_score", 0) for c in dedup]))

    top_indices = np.argsort((v_scores * 0.4) + (bm_scores * 0.6))[::-1][:25]
    ce_inputs = [[query_clean, corpus[i]] for i in top_indices]
    
    ce_scores_raw = reranker.predict(ce_inputs)
    ce_scores = safe_normalize(ce_scores_raw)
    
    final_candidates = []
    for i, idx in enumerate(top_indices):
        final_score = (ce_scores[i] * 0.7) + (bm_scores[idx] * 0.2) + (v_scores[idx] * 0.1)
        
        if ce_scores_raw[i] < -8.0: 
            continue

        if final_score >= FINAL_THRESHOLD_GLOBAL:
            chunk = dedup[idx]
            chunk["score"] = round(float(final_score), 4)
            final_candidates.append(chunk)

    sorted_results = sorted(final_candidates, key=lambda x: x["score"], reverse=True)
    return sorted_results[:limit], len(sorted_results)