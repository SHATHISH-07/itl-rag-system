import logging
import json
from concurrent.futures import ThreadPoolExecutor

from rank_bm25 import BM25Okapi
from core.redis_client import redis_client
from db.qdrant_db import qdrant_client
from core.reranker import reranker
from utils.helpers import make_cache_key, format_score, get_collection_name
from core.embeddings import model

logger = logging.getLogger(__name__)

VECTOR_THRESHOLD_FILE = 0.30
VECTOR_THRESHOLD_GLOBAL = 0.25

FINAL_THRESHOLD_FILE = 0.25
FINAL_THRESHOLD_GLOBAL = 0.30

def retrieve(query: str, filter_keyword: str = None, limit: int = 8, offset: int = 0):
    query_clean = query.strip().lower()

    embedding_key = make_cache_key("embedding", query_clean)
    query_vector = None

    if redis_client:
        cached = redis_client.get(embedding_key)
        if cached:
            query_vector = json.loads(cached)

    if not query_vector:
        query_vector = model.encode([query_clean])[0].tolist()
        if redis_client:
            redis_client.setex(embedding_key, 3600, json.dumps(query_vector))

    cache_key = make_cache_key("vector", f"{query_clean}:{filter_keyword or 'global'}")
    all_results = []

    if redis_client:
        cached = redis_client.get(cache_key)
        if cached:
            all_results = json.loads(cached)

    if not all_results:
        try:
            if filter_keyword:
                collection_name = get_collection_name(filter_keyword)

                results = qdrant_client.query_points(
                    collection_name=collection_name,
                    query=query_vector,
                    limit=25
                )

                threshold = VECTOR_THRESHOLD_FILE

                all_results = [
                    {
                        **dict(r.payload),
                        "vector_score": float(r.score),
                        "source": r.payload.get("source")
                    }
                    for r in results.points
                    if r.payload and float(r.score) >= threshold
                ]

            else:
                collections = [
                    col for col in qdrant_client.get_collections().collections
                    if col.name not in ["file_metadata", "semantic_cache"]
                ]

                threshold = VECTOR_THRESHOLD_GLOBAL

                def query_collection(col):
                    try:
                        res = qdrant_client.query_points(
                            collection_name=col.name,
                            query=query_vector,
                            limit=25
                        )

                        return [
                            {
                                **dict(r.payload),
                                "vector_score": float(r.score),
                                "source": r.payload.get("source")
                            }
                            for r in res.points
                            if r.payload and float(r.score) >= threshold
                        ]
                    except:
                        return []

                with ThreadPoolExecutor(max_workers=5) as executor:
                    for r in executor.map(query_collection, collections):
                        all_results.extend(r)

        except:
            return [], 0

        if redis_client and all_results:
            redis_client.setex(cache_key, 600, json.dumps(all_results))

    if not all_results:
        return [], 0

    all_results = sorted(all_results, key=lambda x: x["vector_score"], reverse=True)
    candidate_pool = all_results[:50]

    corpus = [r.get("text", "") for r in candidate_pool]
    if not corpus:
        return [], 0

    bm25 = BM25Okapi([doc.lower().split() for doc in corpus])
    bm_scores = bm25.get_scores(query_clean.split())
    bm_max = max(bm_scores) if bm_scores.any() else 1
    bm_scores = [s / bm_max if bm_max != 0 else 0 for s in bm_scores]

    rerank_limit = min(12, len(candidate_pool))
    ce_scores = reranker.predict([[query_clean, corpus[i]] for i in range(rerank_limit)])
    ce_max = max(ce_scores) if len(ce_scores) > 0 else 1
    ce_scores = [s / ce_max if ce_max != 0 else 0 for s in ce_scores]

    for i in range(len(candidate_pool)):
        bm = bm_scores[i]
        ce = ce_scores[i] if i < rerank_limit else 0
        vec = candidate_pool[i]["vector_score"]

        score = (ce * 0.6) + (bm * 0.25) + (vec * 0.15)
        score = min(score, 1.0)

        candidate_pool[i]["score"] = round(score, 4)
        candidate_pool[i]["relevance_label"] = format_score(score)

    candidate_pool = sorted(candidate_pool, key=lambda x: x["score"], reverse=True)

    final_threshold = FINAL_THRESHOLD_FILE if filter_keyword else FINAL_THRESHOLD_GLOBAL

    filtered = [
        c for c in candidate_pool
        if c.get("score", 0) >= final_threshold
    ]

    if not filtered:
        return [], 0

    return filtered[offset: offset + limit], len(filtered)