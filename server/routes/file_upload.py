import asyncio
import uuid
import os
import logging
import aiofiles
from fastapi import APIRouter, UploadFile, File
from db.qdrant_db import qdrant_client
from services.ingestion_service import ingest_file
from fastapi import HTTPException, status

logger = logging.getLogger("file_uploader")
router = APIRouter()

TEMP_UPLOAD_DIR = "uploads"
os.makedirs(TEMP_UPLOAD_DIR, exist_ok=True)


async def process_single_file(uploaded_file: UploadFile, semaphore: asyncio.Semaphore):
    async with semaphore:
        unique_id = str(uuid.uuid4())[:8]
        safe_filename = f"{unique_id}_{uploaded_file.filename}"
        temp_file_path = os.path.join(TEMP_UPLOAD_DIR, safe_filename)

        try:
            async with aiofiles.open(temp_file_path, "wb") as buffer:
                content = await uploaded_file.read()
                await buffer.write(content)

            loop = asyncio.get_event_loop()
            result = await loop.run_in_executor(
                None, ingest_file, temp_file_path, uploaded_file.filename
            )

            return result

        except Exception as e:
            logger.error(f"Error processing {uploaded_file.filename}: {str(e)}")
            return {"file": uploaded_file.filename, "status": f"Error: {str(e)}"}

        finally:
            if os.path.exists(temp_file_path):
                os.remove(temp_file_path)


@router.post("/upload-files")
async def upload_files(files: list[UploadFile] = File(...)):

    if not files:
        raise HTTPException(status_code=400, detail="No files were uploaded.")

    logger.info(f"Parallel Upload Started: {len(files)} files")

    semaphore = asyncio.Semaphore(3)  # control concurrency
    tasks = [process_single_file(f, semaphore) for f in files]

    responses = await asyncio.gather(*tasks)

    logger.info("Upload Completed")
    return {"results": responses}


@router.get("/list-files")
async def list_files():
    try:
        results = qdrant_client.scroll(
            collection_name="file_metadata",
            limit=100,
            with_payload=True
        )
        filenames = [point.payload["filename"] for point in results[0]]
        return {"files": sorted(filenames)}
    except Exception as e:
        return {"files": [], "error": str(e)}