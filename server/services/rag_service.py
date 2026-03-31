import logging
import os
import json
from uuid import uuid4
from concurrent.futures import ThreadPoolExecutor

from core.redis_client import redis_client
from db.qdrant_db import qdrant_client, SEMANTIC_COLLECTION
from core.embeddings import model
from sentence_transformers import CrossEncoder
from rank_bm25 import BM25Okapi

from utils.helpers import make_cache_key, format_score

logger = logging.getLogger(__name__)

RERANKING_CROSS_ENCODER = os.getenv("RERANKING_CROSS_ENCODER")

reranker = CrossEncoder(
    RERANKING_CROSS_ENCODER or "cross-encoder/ms-marco-MiniLM-L-6-v2",
    max_length=256,
    device="cpu"
)

SIM_THRESHOLD = 0.90


def retrieve(query: str, filter_keyword: str = None, limit: int = 5, offset: int = 0):
    logger.info(f"Starting hybrid retrieval for: '{query}'")

    embedding_key = make_cache_key("embedding", query)

    if redis_client:
        cached_embedding = redis_client.get(embedding_key)
        if cached_embedding:
            query_vector = json.loads(cached_embedding)
            logger.info("Embedding cache hit")
        else:
            query_vector = model.encode([query])[0].tolist()
            redis_client.setex(embedding_key, 3600, json.dumps(query_vector))
            logger.info("Embedding cached")
    else:
        query_vector = model.encode([query])[0].tolist()

    vector_cache_key = make_cache_key("vector", f"{query}:{filter_keyword}")
    all_results = []

    if redis_client:
        cached_results = redis_client.get(vector_cache_key)
        if cached_results:
            logger.info("Vector cache hit")
            all_results = json.loads(cached_results)

    if not all_results:
        try:
            collections = qdrant_client.get_collections().collections
        except Exception as e:
            logger.error(f"Qdrant error: {e}")
            return [], 0

        def query_collection(col):
            try:
                results = qdrant_client.query_points(
                    collection_name=col.name,
                    query=query_vector,
                    limit=20
                )
                temp = []
                for res in results.points:
                    if not res.payload:
                        continue

                    payload = dict(res.payload)
                    payload["vector_score"] = float(res.score)
                    payload["source"] = payload.get("source") or col.name
                    temp.append(payload)

                return temp
            except Exception as e:
                logger.error(f"Error querying {col.name}: {e}")
                return []

        with ThreadPoolExecutor(max_workers=5) as executor:
            results = executor.map(query_collection, collections)

        for r in results:
            all_results.extend(r)

        if redis_client and all_results:
            redis_client.setex(vector_cache_key, 600, json.dumps(all_results))
            logger.info("Vector results cached")

    if not all_results:
        return [], 0

    all_results = sorted(all_results, key=lambda x: x["vector_score"], reverse=True)
    candidate_pool = all_results[:50]

    corpus_texts = [r.get("text", "") for r in candidate_pool]
    tokenized_corpus = [doc.lower().split() for doc in corpus_texts]
    tokenized_query = query.lower().split()

    bm25 = BM25Okapi(tokenized_corpus)
    raw_bm25_scores = bm25.get_scores(tokenized_query)

    min_bm, max_bm = min(raw_bm25_scores), max(raw_bm25_scores)
    bm_range = max_bm - min_bm + 1e-6
    norm_bm25 = [(s - min_bm) / bm_range for s in raw_bm25_scores]

    rerank_indices = list(range(min(10, len(candidate_pool))))
    rerank_texts = [corpus_texts[i] for i in rerank_indices]

    sentence_pairs = [[query, txt] for txt in rerank_texts]
    raw_ce_scores = reranker.predict(sentence_pairs)

    min_ce, max_ce = min(raw_ce_scores), max(raw_ce_scores)
    ce_range = max_ce - min_ce + 1e-6
    norm_ce_scores_partial = [(s - min_ce) / ce_range for s in raw_ce_scores]

    norm_ce_scores = [0.0] * len(candidate_pool)
    for idx, score in zip(rerank_indices, norm_ce_scores_partial):
        norm_ce_scores[idx] = score

    vector_scores = [r["vector_score"] for r in candidate_pool]
    min_vec, max_vec = min(vector_scores), max(vector_scores)
    vec_range = max_vec - min_vec + 1e-6
    norm_vector_scores = [(v - min_vec) / vec_range for v in vector_scores]

    for i in range(len(candidate_pool)):
        bm_weight = 0.15 if len(query.split()) < 4 else 0.25

        final_score = (
            (norm_ce_scores[i] * 0.6) +
            (norm_bm25[i] * bm_weight) +
            (norm_vector_scores[i] * 0.15)
        )

        final_score *= min(1.0, len(corpus_texts[i].split()) / 50)

        candidate_pool[i]["score"] = final_score
        candidate_pool[i]["relevance_label"] = format_score(final_score)

    candidate_pool = sorted(candidate_pool, key=lambda x: x["score"], reverse=True)

    return candidate_pool[offset: offset + limit], len(candidate_pool)


# -------------------- RAG PIPELINE (VECTOR CACHE) --------------------
def rag_pipeline(query: str, generate_answer_fn):
    final_cache_key = make_cache_key("final", query)

    if redis_client:
        cached_response = redis_client.get(final_cache_key)
        if cached_response:
            logger.info("Final response cache hit")
            return json.loads(cached_response)

    embedding_key = make_cache_key("embedding", query)

    if redis_client:
        cached_embedding = redis_client.get(embedding_key)
        if cached_embedding:
            query_vector = json.loads(cached_embedding)
        else:
            query_vector = model.encode([query])[0].tolist()
            redis_client.setex(embedding_key, 3600, json.dumps(query_vector))
    else:
        query_vector = model.encode([query])[0].tolist()

    try:
        results = qdrant_client.search(
            collection_name=SEMANTIC_COLLECTION,
            query_vector=query_vector,
            limit=1
        )

        if results and results[0].score >= SIM_THRESHOLD:
            logger.info(f"Vector cache hit (score={results[0].score:.3f})")
            return results[0].payload["response"]

    except Exception as e:
        logger.warning(f"Vector cache search failed: {e}")

    retrieved_chunks, _ = retrieve(query)

    if not retrieved_chunks:
        return {"answer": "I don't know based on the provided context."}

    answer = generate_answer_fn(query, retrieved_chunks)
    response = {"answer": answer}

    try:
        qdrant_client.upsert(
            collection_name=SEMANTIC_COLLECTION,
            points=[{
                "id": str(uuid4()),
                "vector": query_vector,
                "payload": {
                    "query": query,
                    "response": response
                }
            }]
        )
        logger.info("Stored in vector cache")

    except Exception as e:
        logger.warning(f"Vector cache insert failed: {e}")

    if redis_client:
        redis_client.setex(final_cache_key, 1800, json.dumps(response))

    return response