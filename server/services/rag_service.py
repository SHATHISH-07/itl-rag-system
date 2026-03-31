import logging
import os
from concurrent.futures import ThreadPoolExecutor

from db.qdrant_db import qdrant_client
from core.embeddings import model
from sentence_transformers import CrossEncoder
from rank_bm25 import BM25Okapi

logger = logging.getLogger(__name__)

RERANKING_CROSS_ENCODER = os.getenv("RERANKING_CROSS_ENCODER")

reranker = CrossEncoder(
    RERANKING_CROSS_ENCODER or "cross-encoder/ms-marco-MiniLM-L-6-v2",
    max_length=256,
    device="cpu"
)


def format_score(score):
    percentage = round(score * 100)
    if score >= 0.85:
        return f"{percentage}% - Highly Relevant"
    elif score >= 0.60:
        return f"{percentage}% - Relevant & Accurate"
    elif score >= 0.35:
        return f"{percentage}% - Partially Relevant"
    else:
        return f"{percentage}% - Low Relevance"


def retrieve(query: str, filter_keyword: str = None, limit: int = 5, offset: int = 0):
    logger.info(f"Starting hybrid retrieval for: '{query}'")

    # Embed Query
    query_vector = model.encode([query])[0]
    all_results = []

    # Fetch Collections
    try:
        collections_response = qdrant_client.get_collections()
        collections = collections_response.collections
    except Exception as e:
        logger.error(f"Error connecting to Qdrant: {e}")
        return [], 0

    # Parallel Query Qdrant
    def query_collection(col):
        try:
            results = qdrant_client.query_points(
                collection_name=col.name,
                query=query_vector.tolist(),
                limit=20   # reduced from 50
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

    if not all_results:
        return [], 0

    # Initial Ranking (Vector)
    all_results = sorted(all_results, key=lambda x: x["vector_score"], reverse=True)

    # Take top 50 for hybrid scoring
    candidate_pool = all_results[:50]

    corpus_texts = [r.get("text", "") for r in candidate_pool]

    # BM25 Scoring
    tokenized_corpus = [doc.lower().split() for doc in corpus_texts]
    tokenized_query = query.lower().split()

    bm25 = BM25Okapi(tokenized_corpus)
    raw_bm25_scores = bm25.get_scores(tokenized_query)

    # Normalize BM25
    min_bm = min(raw_bm25_scores)
    max_bm = max(raw_bm25_scores)
    bm_range = max_bm - min_bm + 1e-6
    norm_bm25 = [(s - min_bm) / bm_range for s in raw_bm25_scores]

    # Select Top 20 for Reranking (IMPORTANT SPEED FIX)
    rerank_indices = list(range(min(20, len(candidate_pool))))
    rerank_texts = [corpus_texts[i] for i in rerank_indices]

    sentence_pairs = [[query, txt] for txt in rerank_texts]
    raw_ce_scores = reranker.predict(sentence_pairs)

    # Normalize CrossEncoder scores
    min_ce = min(raw_ce_scores)
    max_ce = max(raw_ce_scores)
    ce_range = max_ce - min_ce + 1e-6
    norm_ce_scores_partial = [(s - min_ce) / ce_range for s in raw_ce_scores]

    # Fill CE scores for all (default 0 for non-reranked)
    norm_ce_scores = [0.0] * len(candidate_pool)
    for idx, score in zip(rerank_indices, norm_ce_scores_partial):
        norm_ce_scores[idx] = score

    # Normalize Vector Scores
    vector_scores = [r["vector_score"] for r in candidate_pool]
    min_vec = min(vector_scores)
    max_vec = max(vector_scores)
    vec_range = max_vec - min_vec + 1e-6
    norm_vector_scores = [(v - min_vec) / vec_range for v in vector_scores]

    # Final Hybrid Scoring
    for i in range(len(candidate_pool)):
        ce_score = norm_ce_scores[i]
        bm_score = norm_bm25[i]
        vector_score = norm_vector_scores[i]

        if len(query.split()) < 4:
            bm_weight = 0.15
        else:
            bm_weight = 0.25

        final_score = (
            (ce_score * 0.6) +
            (bm_score * bm_weight) +
            (vector_score * 0.15)
        )

        text_len = len(corpus_texts[i].split())
        length_penalty = min(1.0, text_len / 50)
        final_score *= length_penalty

        candidate_pool[i]["score"] = final_score
        candidate_pool[i]["relevance_label"] = format_score(final_score)
        candidate_pool[i]["bm25_score"] = bm_score
        candidate_pool[i]["ce_score"] = ce_score
        candidate_pool[i]["vector_score_norm"] = vector_score

    # Final Sort
    candidate_pool = sorted(candidate_pool, key=lambda x: x["score"], reverse=True)

    total_count = len(candidate_pool)
    paginated_results = candidate_pool[offset: offset + limit]

    logger.info(
        f"Retrieval complete. Best Hybrid Score: "
        f"{paginated_results[0]['score'] if paginated_results else 0:.4f}"
    )

    return paginated_results, total_count