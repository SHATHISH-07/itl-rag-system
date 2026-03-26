import os
from dotenv import load_dotenv
from sentence_transformers import SentenceTransformer
from utils import chunk_text
from db.qdrant_db import qdrant_client
import uuid

load_dotenv()

DATA_PATH = os.getenv("DATA_PATH")
EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL")


model = SentenceTransformer(EMBEDDING_MODEL)

from db.qdrant_db import qdrant_client
from qdrant_client.http.models import VectorParams, Distance

def get_collection_name(file_name):
    return file_name.replace(".txt", "").lower() + "_collection"

def run_ingestion():
    existing_collections = [c.name for c in qdrant_client.get_collections().collections]

    for file in os.listdir(DATA_PATH):
        if not file.endswith(".txt"):
            continue

        collection_name = get_collection_name(file)

        if collection_name not in existing_collections:
            qdrant_client.create_collection(
                collection_name=collection_name,
                vectors_config=VectorParams(size=384, distance=Distance.COSINE)
            )

        with open(os.path.join(DATA_PATH, file), "r", encoding="utf-8") as f:
            text = f.read()

        chunks = chunk_text(text)
        embeddings = model.encode(chunks)

        points = [
            {
                "id": str(uuid.uuid4()),
                "vector": vec.tolist(),
                "payload": {
                    "text": chunk,
                    "source": file
                }
            }
            for vec, chunk in zip(embeddings, chunks)
        ]

        qdrant_client.upsert(
            collection_name=collection_name,
            points=points
        )

    print("Ingestion Completed")

if __name__ == "__main__":
    run_ingestion()