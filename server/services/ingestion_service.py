import os
import uuid
import logging
from qdrant_client.http.models import VectorParams, Distance, PointStruct # Added PointStruct
from core.embeddings import model
from utils.helpers import chunk_text, get_collection_name, extract_text_from_file
from db.qdrant_db import qdrant_client

logger = logging.getLogger(__name__)

def ingest_file(file_path: str, filename: str):
    text = extract_text_from_file(file_path, filename)
    if not text.strip():
        return {"file": filename, "status": "empty file, skipped"}

    collection_name = get_collection_name(filename)

    VECTOR_SIZE = 384 

    try:
        existing_collections = [c.name for c in qdrant_client.get_collections().collections]
        if collection_name not in existing_collections:
            qdrant_client.create_collection(
                collection_name=collection_name,
                vectors_config=VectorParams(size=VECTOR_SIZE, distance=Distance.COSINE)
            )

        chunks = chunk_text(text)
        embeddings = model.encode(chunks)

        points = [
            PointStruct(
                id=str(uuid.uuid4()),
                vector=vec.tolist(),
                payload={
                    "text": chunk,
                    "source": filename,
                    "file_type": os.path.splitext(filename)[1].lower(),
                    "size": len(chunk),
                }
            )
            for vec, chunk in zip(embeddings, chunks)
        ]

        qdrant_client.upsert(collection_name=collection_name, points=points)
        
        return {"file": filename, "status": f"ingested {len(chunks)} chunks"}

    except Exception as e:
        logger.error(f"Failed to ingest {filename}: {e}")
        return {"file": filename, "status": f"error: {str(e)}"}