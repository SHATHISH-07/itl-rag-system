import logging
import os
import math 
from db.qdrant_db import qdrant_client
from core.embeddings import model
from sentence_transformers import CrossEncoder 
from rank_bm25 import BM25Okapi  

logger = logging.getLogger(__name__)

RERANKING_CROSS_ENCODER = os.getenv("RERANKING_CROSS_ENCODER")
reranker = CrossEncoder(RERANKING_CROSS_ENCODER)

def retrieve(query: str, filter_keyword: str = None, limit: int = 5, offset: int = 0):
    logger.info(f"Starting hybrid retrieval for: '{query}'")
    
    query_vector = model.encode([query])[0]
    all_results = []
    
    try:
        collections_response = qdrant_client.get_collections()
        collections = collections_response.collections
    except Exception as e:
        logger.error(f"Error connecting to Qdrant: {e}")
        return [], 0

    for col in collections:
        try:
            results = qdrant_client.query_points(
                collection_name=col.name,
                query=query_vector.tolist(),
                limit=20 
            )
            for res in results.points:
                if not res.payload: continue
                payload = dict(res.payload)
                payload["vector_score"] = float(res.score)
                payload["source"] = payload.get("source") or col.name
                all_results.append(payload)
        except Exception as e:
            logger.error(f"Error querying collection '{col.name}': {e}")

    if not all_results: 
        return [], 0

    all_results = sorted(all_results, key=lambda x: x["vector_score"], reverse=True)
    candidate_pool = all_results[:40] 
    
    logger.info(f"Pre-filtered to {len(candidate_pool)} top candidates for re-ranking.")

    corpus_texts = [r.get("text", "") for r in candidate_pool]
    tokenized_corpus = [doc.lower().split() for doc in corpus_texts]
    tokenized_query = query.lower().split()
    
    bm25 = BM25Okapi(tokenized_corpus)
    bm25_scores = bm25.get_scores(tokenized_query)
    max_bm = max(bm25_scores) if len(bm25_scores) > 0 else 1

    logger.info(f"Re-ranking top 40 candidates...")
    sentence_pairs = [[query, txt] for txt in corpus_texts]
    raw_rerank_scores = reranker.predict(sentence_pairs)

    for i, score in enumerate(raw_rerank_scores):
        ce_score = 1 / (1 + math.exp(-score))
        
        bm_score = bm25_scores[i] / max_bm if max_bm > 0 else 0
        
        candidate_pool[i]["score"] = (ce_score * 0.7) + (bm_score * 0.3)
        candidate_pool[i]["bm25_score"] = bm_score 
        candidate_pool[i]["ce_score"] = ce_score

    candidate_pool = sorted(candidate_pool, key=lambda x: x["score"], reverse=True)
    
    total_count = len(candidate_pool)
    paginated_results = candidate_pool[offset : offset + limit]
    
    logger.info(f"Retrieval complete. Best Hybrid Score: {paginated_results[0]['score'] if paginated_results else 0}")
    
    return paginated_results, total_count