import logging
import os
import math # Added for score normalization
from db.qdrant_db import qdrant_client
from core.embeddings import model
from sentence_transformers import CrossEncoder # Ensure you pip install sentence-transformers

logger = logging.getLogger(__name__)

RERANKING_CROSS_ENCODER = os.getenv("RERANKING_CROSS_ENCODER")
reranker = CrossEncoder(RERANKING_CROSS_ENCODER)

def retrieve(query: str, filter_keyword: str = None, limit: int = 5, offset: int = 0):
    logger.info(f"Starting retrieval for query: '{query}'")
    
    query_vector = model.encode([query])[0]
    all_results = []
    
    try:
        collections_response = qdrant_client.get_collections()
        collections = collections_response.collections
    except Exception as e:
        logger.error(f"Error connecting to Qdrant: {e}", exc_info=True)
        return [], 0

    filter_list = []
    if filter_keyword and filter_keyword.strip() and filter_keyword.lower() != "none":
        filter_list = [
            kw.strip().lower().replace(".txt", "") 
            for kw in filter_keyword.split(",") 
            if kw.strip()
        ]

    for col in collections:
        if filter_list and not any(kw in col.name.lower() for kw in filter_list):
            continue

        try:
            results = qdrant_client.query_points(
                collection_name=col.name,
                query=query_vector.tolist(),
                limit=30  
            )

            for res in results.points:
                if not res.payload:
                    continue
                
                payload = dict(res.payload)
                payload["initial_score"] = float(res.score) # Store original vector score
                payload["source"] = payload.get("source") or col.name
                all_results.append(payload)

        except Exception as e:
            logger.error(f"Error querying collection '{col.name}': {e}")
            continue

    if not all_results:
        return [], 0

    logger.info(f"Re-ranking {len(all_results)} candidates for higher precision...")
    
    sentence_pairs = [[query, r.get("text", "")] for r in all_results]
    
    raw_rerank_scores = reranker.predict(sentence_pairs)
    
    for i, score in enumerate(raw_rerank_scores):
        normalized_score = 1 / (1 + math.exp(-score)) 
        all_results[i]["score"] = normalized_score

    all_results = sorted(all_results, key=lambda x: x["score"], reverse=True)

    total_count = len(all_results)
    paginated_results = all_results[offset : offset + limit]
    
    logger.info(f"Re-ranking complete. Top score: {paginated_results[0]['score'] if paginated_results else 0}")
    
    return paginated_results, total_count