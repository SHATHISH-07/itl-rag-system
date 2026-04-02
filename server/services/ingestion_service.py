from core.embeddings import model
from db.qdrant_db import qdrant_client
from utils.helpers import chunk_text, extract_text_from_file, get_collection_name
from qdrant_client.models import VectorParams, Distance, PointStruct

import uuid
import logging

logger = logging.getLogger(__name__)

EMBED_BATCH_SIZE = 64
QDRANT_BATCH_SIZE = 256
METADATA_COLLECTION = "file_metadata" # Matches your /list-files route

def record_file_metadata(filename: str):
    """
    Registers the filename in a dedicated collection so the 
    frontend dropdown can list it.
    """
    try:
        collections = [col.name for col in qdrant_client.get_collections().collections]
        
        # Ensure metadata collection exists (no vectors required for simple list)
        if METADATA_COLLECTION not in collections:
            logger.info(f"Creating metadata collection: {METADATA_COLLECTION}")
            qdrant_client.create_collection(
                collection_name=METADATA_COLLECTION,
                vectors_config={} 
            )
        
        # Use a deterministic ID based on filename to prevent duplicate entries
        file_id = str(uuid.uuid5(uuid.NAMESPACE_DNS, filename))
        
        qdrant_client.upsert(
            collection_name=METADATA_COLLECTION,
            points=[PointStruct(
                id=file_id,
                vector={},
                payload={"filename": filename}
            )]
        )
        logger.info(f"Metadata indexed for: {filename}")
    except Exception as e:
        logger.error(f"Failed to record file metadata: {e}")

def ensure_collection(collection_name: str, vector_size: int):
    try:
        collections = qdrant_client.get_collections().collections
        existing_collections = [col.name for col in collections]

        if collection_name not in existing_collections:
            logger.info(f"Creating collection: {collection_name}")
            qdrant_client.create_collection(
                collection_name=collection_name,
                vectors_config=VectorParams(
                    size=vector_size,
                    distance=Distance.COSINE
                )
            )
    except Exception as e:
        logger.error(f"Error ensuring collection: {str(e)}", exc_info=True)
        raise

def ingest_file(file_path: str, filename: str):
    try:
        logger.info(f"Starting ingestion for: {filename}")

        # 1. Extract text
        text = extract_text_from_file(file_path, filename)
        if not text:
            return {"file": filename, "status": "No text extracted"}

        # 2. Chunking
        chunks = chunk_text(text)
        if not chunks:
            return {"file": filename, "status": "No valid chunks"}

        # 3. Batch Embedding
        embeddings = []
        for i in range(0, len(chunks), EMBED_BATCH_SIZE):
            batch = chunks[i:i + EMBED_BATCH_SIZE]
            batch_embeddings = model.encode(batch)
            embeddings.extend(batch_embeddings)

        # 4. Register Filename in Metadata (FOR FRONTEND DROPDOWN)
        record_file_metadata(filename)

        # 5. Setup Vector Collection
        collection_name = get_collection_name(filename)
        vector_size = len(embeddings[0])
        ensure_collection(collection_name, vector_size)

        # 6. Prepare Points with Source Metadata
        points = [
            PointStruct(
                id=str(uuid.uuid4()),
                vector=emb.tolist(),
                payload={
                    "text": chunk,
                    "source": filename # CRITICAL: Used by retrieval filter
                },
            )
            for chunk, emb in zip(chunks, embeddings)
        ]

        # 7. Batch Insert into Qdrant
        for i in range(0, len(points), QDRANT_BATCH_SIZE):
            batch = points[i:i + QDRANT_BATCH_SIZE]
            qdrant_client.upsert(
                collection_name=collection_name,
                points=batch
            )

        logger.info(f"{filename}: {len(points)} points stored successfully")
        return {
            "file": filename,
            "status": "Success",
            "chunks": len(points)
        }

    except Exception as e:
        logger.error(f"Ingestion failed for {filename}: {str(e)}", exc_info=True)
        return {
            "file": filename,
            "status": f"Error: {str(e)}"
        }