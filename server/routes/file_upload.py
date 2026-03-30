import asyncio
import uuid
import os
import shutil
import logging
from fastapi import APIRouter, UploadFile, File
from services.ingestion_service import ingest_file

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
            with open(temp_file_path, "wb") as buffer:
                shutil.copyfileobj(uploaded_file.file, buffer)
            
            loop = asyncio.get_event_loop()
            result = await loop.run_in_executor(None, ingest_file, temp_file_path, uploaded_file.filename)
            return result

        except Exception as e:
            logger.error(f"Error processing {uploaded_file.filename}: {str(e)}")
            return {"file": uploaded_file.filename, "status": f"Error: {str(e)}"}
        
        finally:
            if os.path.exists(temp_file_path):
                os.remove(temp_file_path)

@router.post("/upload-files")
async def upload_files(files: list[UploadFile] = File(...)):
    file_count = len(files)
    logger.info(f"Parallel Batch Upload Started: {file_count} files")

    semaphore = asyncio.Semaphore(3)
    tasks = [process_single_file(f, semaphore) for f in files]
    responses = await asyncio.gather(*tasks)

    logger.info(f"Parallel Batch Upload Completed: {file_count} files processed.")
    return {"results": responses}