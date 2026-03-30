import os
import uuid
import logging
from qdrant_client.http.models import VectorParams, Distance, PointStruct
from core.embeddings import model
from utils.helpers import chunk_text, get_collection_name, extract_text_from_file
from db.qdrant_db import qdrant_client

logger = logging.getLogger(__name__)

def ingest_file(file_path: str, filename: str):
    logger.info(f"Starting ingestion for file: {filename}")
    
    try:
        text = extract_text_from_file(file_path, filename)
        if not text.strip():
            logger.warning(f"Skipping {filename}: No text content extracted.")
            return {"file": filename, "status": "empty file, skipped"}

        collection_name = get_collection_name(filename)
        VECTOR_SIZE = 384 

        existing_collections = [c.name for c in qdrant_client.get_collections().collections]
        if collection_name not in existing_collections:
            logger.info(f"Creating new collection: {collection_name}")
            qdrant_client.create_collection(
                collection_name=collection_name,
                vectors_config=VectorParams(size=VECTOR_SIZE, distance=Distance.COSINE)
            )
        else:
            logger.debug(f"Using existing collection: {collection_name}")

        chunks = chunk_text(text)
        logger.info(f"Text split into {len(chunks)} chunks for {filename}")

        logger.info(f"Generating embeddings for {filename}...")
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

        BATCH_SIZE = 100
        logger.info(f"Upserting {len(points)} points in batches of {BATCH_SIZE} to: {collection_name}")
        
        for i in range(0, len(points), BATCH_SIZE):
            batch = points[i : i + BATCH_SIZE]
            qdrant_client.upsert(
                collection_name=collection_name, 
                points=batch,
                wait=True
            )
            logger.debug(f"Successfully upserted batch {i//BATCH_SIZE + 1}")

        logger.info(f"SUCCESS: Ingestion completed for {filename}")
        return {"file": filename, "status": f"ingested {len(chunks)} chunks"}

    except Exception as e:
        logger.error(f"FAILURE: Could not ingest {filename}. Error: {str(e)}", exc_info=True)
        return {"file": filename, "status": f"error: {str(e)}"}