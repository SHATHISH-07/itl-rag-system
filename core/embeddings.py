import os
from dotenv import load_dotenv
from sentence_transformers import SentenceTransformer

load_dotenv()
EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL")
model = SentenceTransformer(EMBEDDING_MODEL)