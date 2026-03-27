import logging
from db.qdrant_db import qdrant_client
from core.embeddings import model

logger = logging.getLogger(__name__)

def retrieve(query: str, filter_keyword: str = None, limit: int = 5, offset: int = 0):
    query_vector = model.encode([query])[0]

    all_results = []
    
    try:
        collections_response = qdrant_client.get_collections()
        collections = collections_response.collections
    except Exception as e:
        logger.error(f"Error connecting to Qdrant: {e}")
        return [], 0

    filter_list = []
    if filter_keyword and filter_keyword.strip() and filter_keyword.lower() != "none":
        filter_list = [
            kw.strip().lower().replace(".txt", "") 
            for kw in filter_keyword.split(",") 
            if kw.strip()
        ]

    for col in collections:
        if filter_list:
            if not any(kw in col.name.lower() for kw in filter_list):
                continue

        try:
            results = qdrant_client.query_points(
                collection_name=col.name,
                query=query_vector.tolist(),
                limit=20  
            )

            for res in results.points:
                if not res.payload:
                    continue
                
                score = float(res.score)
                if score < 0.25:
                    continue

                payload = dict(res.payload)
                payload["score"] = score
                payload["source"] = payload.get("source") or col.name
                all_results.append(payload)
                
        except Exception as e:
            logger.error(f"Error querying collection '{col.name}': {e}")
            continue

    all_results = sorted(all_results, key=lambda x: x["score"], reverse=True)
    
    total_count = len(all_results)
    paginated_results = all_results[offset : offset + limit]
    
    logger.info(f"Retrieved {len(paginated_results)} chunks (Total found: {total_count})")
    return paginated_results, total_count