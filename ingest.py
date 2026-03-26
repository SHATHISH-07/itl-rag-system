import os
from dotenv import load_dotenv
from sentence_transformers import SentenceTransformer
from utils import chunk_text
from db.qdrant_db import qdrant_client
import uuid

load_dotenv()

DATA_PATH = os.getenv("DATA_PATH")
EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL")
DB_COLLECTION_NAME = os.getenv("DB_COLLECTION_NAME")


model = SentenceTransformer(EMBEDDING_MODEL)

def run_ingestion():
    for file in os.listdir(DATA_PATH):
        if file.endswith(".txt"):
            file_path = os.path.join(DATA_PATH, file)

            with open(file_path, "r", encoding="utf-8") as f:
                text = f.read()

            chunks = chunk_text(text)
            embeddings = model.encode(chunks)

            points = [
                {
                    "id": str(uuid.uuid4()),
                    "vector": vec.tolist(),
                    "payload": {"text": chunk, "source": file}
                }
                for vec, chunk in zip(embeddings, chunks)
            ]

            qdrant_client.upsert(
                collection_name=DB_COLLECTION_NAME,
                points=points
            )

    print("Ingestion Completed")

if __name__ == "__main__":
    run_ingestion()