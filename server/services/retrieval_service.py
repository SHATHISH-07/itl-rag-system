import logging
import json
import numpy as np
from concurrent.futures import ThreadPoolExecutor
from rank_bm25 import BM25Okapi
from core.redis_client import redis_client
from db.qdrant_db import qdrant_client
from core.reranker import reranker
from utils.helpers import make_cache_key, get_collection_name
from core.embeddings import model
from core.llm_client import client, LLM_MODEL

logger = logging.getLogger(__name__)

FINAL_THRESHOLD_GLOBAL = 0.35   # ✅ FIXED (was too high)

def safe_normalize(scores):
    if len(scores) == 0:
        return np.array([])
    s_min, s_max = np.min(scores), np.max(scores)
    if s_max == s_min:
        return np.ones_like(scores)
    return (scores - s_min) / (s_max - s_min)

def expand_query(query: str):
    try:
        prompt = f'Generate 4 alternative search queries for "{query}". Return JSON list.'
        res = client.chat.completions.create(
            model=LLM_MODEL,
            messages=[{"role": "user", "content": prompt}],
            temperature=0
        )
        return list(set(json.loads(res.choices[0].message.content)))
    except:
        return [query]

def retrieve(query: str, filter_keyword: str = None, limit: int = 7, offset: int = 0):
    query_clean = query.strip().lower()

    cache_key = make_cache_key("v_res", f"{query_clean}:{filter_keyword or 'global'}")

    if redis_client:
        cached = redis_client.get(cache_key)
        if cached:
            data = json.loads(cached)
            return data["results"][:limit], data["total"]

    queries = expand_query(query_clean)

    all_results = []

    try:
        collections = [{"name": get_collection_name(filter_keyword)}] if filter_keyword else \
            [col for col in qdrant_client.get_collections().collections
             if col.name not in ["file_metadata", "semantic_cache"]]

        def search(q):
            vec = model.encode([q])[0].tolist()
            temp = []
            for col in collections:
                col_name = col.name if hasattr(col, 'name') else col['name']
                try:
                    res = qdrant_client.query_points(
                        collection_name=col_name,
                        query=vec,
                        limit=80
                    )
                    temp.extend([
                        {**dict(r.payload), "vector_score": float(r.score)}
                        for r in res.points
                    ])
                except:
                    pass
            return temp

        with ThreadPoolExecutor(max_workers=4) as executor:
            for r in executor.map(search, queries):
                all_results.extend(r)

    except Exception as e:
        logger.error(f"Retrieval error: {e}")
        return [], 0

    if not all_results:
        return [], 0

    seen = set()
    dedup = []
    for r in all_results:
        text = r.get("text", "").strip()
        if text and text not in seen:
            seen.add(text)
            dedup.append(r)

    candidate_pool = sorted(dedup, key=lambda x: x["vector_score"], reverse=True)[:100]
    corpus = [c.get("text", "") for c in candidate_pool]

    v_scores = np.array([c["vector_score"] for c in candidate_pool])
    v_norm = safe_normalize(v_scores)

    bm25 = BM25Okapi([doc.lower().split() for doc in corpus])
    bm_norm = safe_normalize(bm25.get_scores(query_clean.split()))

    hybrid = (v_norm * 0.5) + (bm_norm * 0.5)
    top_idx = np.argsort(hybrid)[::-1][:40]

    ce_inputs = [[query_clean, corpus[i]] for i in top_idx]
    ce_scores = reranker.predict(ce_inputs)
    ce_norm = safe_normalize(ce_scores)

    ce_map = {idx: ce_norm[i] for i, idx in enumerate(top_idx)}

    for i in range(len(candidate_pool)):
        vec = v_norm[i]
        bm = bm_norm[i]
        ce = ce_map.get(i, 0.2)   # ✅ FIX: default CE (not 0)

        final_score = (ce * 0.65) + (bm * 0.20) + (vec * 0.15)
        candidate_pool[i]["score"] = round(float(final_score), 4)

    filtered = sorted(
        [c for c in candidate_pool if c["score"] >= FINAL_THRESHOLD_GLOBAL],
        key=lambda x: x["score"],
        reverse=True
    )

    # ✅ SAFETY: fallback if nothing passes threshold
    if not filtered:
        filtered = sorted(candidate_pool, key=lambda x: x["score"], reverse=True)[:limit]

    if redis_client:
        redis_client.setex(cache_key, 600, json.dumps({"results": filtered, "total": len(filtered)}))

    return filtered[offset: offset + limit], len(filtered)