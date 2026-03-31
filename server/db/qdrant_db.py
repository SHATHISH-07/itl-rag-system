import os
from dotenv import load_dotenv
from qdrant_client import QdrantClient
from qdrant_client.models import VectorParams, Distance

load_dotenv()

QDRANT_URL = os.getenv("QDRANT_URL")
QDRANT_API_KEY = os.getenv("QDRANT_API_KEY")

qdrant_client = QdrantClient(
    url=QDRANT_URL,
    api_key=QDRANT_API_KEY,
    timeout=60,
)

SEMANTIC_COLLECTION = "semantic_cache"

def init_semantic_cache(vector_size: int):
    try:
        collections = [c.name for c in qdrant_client.get_collections().collections]

        if SEMANTIC_COLLECTION not in collections:
            qdrant_client.create_collection(
                collection_name=SEMANTIC_COLLECTION,
                vectors_config=VectorParams(
                    size=vector_size,
                    distance=Distance.COSINE
                )
            )
            print("Semantic cache collection created")
        else:
            print("Semantic cache already exists")

    except Exception as e:
        print(f"Error initializing semantic cache: {e}")