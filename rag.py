import re
import os
import logging
from dotenv import load_dotenv
from sentence_transformers import SentenceTransformer
from db.qdrant_db import qdrant_client

# Configure logging to see what's happening during retrieval
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

load_dotenv()

# Loading the Embedding Model from the Env
EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL")

# Setting up the embedding model
model = SentenceTransformer(EMBEDDING_MODEL)

def extract_k(query):
    """Extracts a numerical value for 'k' from the query string."""
    match = re.search(r'\b(\d+)\b', query)
    if match:
        return int(match.group(1))

    word_to_num = {
        "one": 1, "two": 2, "three": 3, "four": 4, "five": 5,
        "six": 6, "seven": 7, "eight": 8, "nine": 9, "ten": 10
    }

    query_lower = query.lower()
    for word, num in word_to_num.items():
        if word in query_lower:
            return num

    return 3 

def retrieve(query, filter_keyword=None):
    k = extract_k(query)
    query_vector = model.encode([query])[0]

    all_results = []
    
    try:
        collections = qdrant_client.get_collections().collections
    except Exception as e:
        logger.error(f"Error connecting to Qdrant: {e}")
        return []

    if not collections:
        logger.warning("No collections found in Qdrant.")
        return []

    for col in collections:
        results = qdrant_client.query_points(
            collection_name=col.name,
            query=query_vector.tolist(),
            limit=k * 5  
        )

        for res in results.points:
            if not res.payload:
                continue

            payload = dict(res.payload)
            # Ensure we capture the source correctly
            source = payload.get("source") or payload.get("file_name") or col.name
            score = float(res.score)

            if score < 0.25:
                continue

            if filter_keyword:
                clean_filter = filter_keyword.lower().replace(".txt", "").strip()
                clean_source = str(source).lower().strip()
                
                if clean_filter not in clean_source:
                    continue

            payload["source"] = source
            payload["score"] = score
            all_results.append(payload)

    all_results = sorted(all_results, key=lambda x: x["score"], reverse=True)
    
    final_results = all_results[:k]
    logger.info(f"Retrieved {len(final_results)} relevant chunks.")
    return final_results