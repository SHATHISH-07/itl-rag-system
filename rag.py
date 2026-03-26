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

    results = qdrant_client.query_points(
        collection_name="test_collection",
        query=query_vector.tolist(),
        limit=k
    )

    output = []
    for res in results.points:
        score = res.score 
        if score < 0.5:   
            continue

        payload = res.payload.copy()  if res.payload else {}
        payload["score"] = float(score)
        output.append(payload)

    output = sorted(output, key=lambda x: x["score"], reverse=True)

    return output
