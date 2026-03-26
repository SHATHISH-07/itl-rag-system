import os
from dotenv import load_dotenv
from qdrant_client import QdrantClient
from qdrant_client.http.models import VectorParams, Distance

load_dotenv()

QDRANT_URL = os.getenv("QDRANT_URL")
QDRANT_API_KEY = os.getenv("QDRANT_API_KEY")
DB_COLLECTION_NAME= os.getenv("DB_COLLECTION_NAME")

qdrant_client = QdrantClient(
    url = QDRANT_URL, 
    api_key = QDRANT_API_KEY,
)

collections = [col.name for col in qdrant_client.get_collections().collections]
if(DB_COLLECTION_NAME not in collections):
    qdrant_client.create_collection(
        collection_name=DB_COLLECTION_NAME,
        vectors_config=VectorParams(size=384, distance = Distance.COSINE)
    )