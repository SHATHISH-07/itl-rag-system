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
