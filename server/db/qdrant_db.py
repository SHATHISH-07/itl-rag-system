import os
from dotenv import load_dotenv
from qdrant_client import QdrantClient

load_dotenv()

# Loading Qdrant Env Variables
QDRANT_URL = os.getenv("QDRANT_URL")
QDRANT_API_KEY = os.getenv("QDRANT_API_KEY")

# Qdrant Client Initialization
qdrant_client = QdrantClient(
    url=QDRANT_URL,
    api_key=QDRANT_API_KEY,
)
