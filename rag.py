import re
import os
from dotenv import load_dotenv
from sentence_transformers import SentenceTransformer
from db.qdrant_db import qdrant_client

load_dotenv()

EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL")

model = SentenceTransformer(EMBEDDING_MODEL)

# Extracting the K value from the user query
def extract_k(query):
   
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

def retrieve(query):
    k = extract_k(query)
    query_vector = model.encode([query])[0]

    all_results = []

    collections = qdrant_client.get_collections().collections

    if not collections:
        return []

    for col in collections:
        results = qdrant_client.query_points(
            collection_name=col.name,
            query=query_vector.tolist(),
            limit=k * 3  
        )

        for res in results.points:
            if not res.payload:
                continue

            payload = dict(res.payload)

            source = payload.get("source") or col.name
            score = float(res.score)

            if score < 0.3:
                continue

            payload["source"] = source
            payload["score"] = score

            all_results.append(payload)

    all_results = sorted(all_results, key=lambda x: x["score"], reverse=True)

    return all_results[:k]