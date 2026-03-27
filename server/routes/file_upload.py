import os
import uuid
import shutil
import logging
from fastapi import APIRouter, UploadFile, File
from typing import Annotated
from services.ingestion_service import ingest_file

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger("file_uploader")

router = APIRouter()
TEMP_UPLOAD_DIR = "uploads"
os.makedirs(TEMP_UPLOAD_DIR, exist_ok=True)

@router.post("/upload-files")
async def upload_files(
    files: list[UploadFile] = File(description="Multiple files as UploadFile")
):
    responses = []
    file_count = len(files)
    
    logger.info(f"Batch Upload Started: Processing {file_count} file(s)")

    for index, uploaded_file in enumerate(files, start=1):
        logger.info(f"[{index}/{file_count}] Starting processing for: {uploaded_file.filename}")
        
        unique_id = str(uuid.uuid4())[:8]
        safe_filename = f"{unique_id}_{uploaded_file.filename}"
        temp_file_path = os.path.join(TEMP_UPLOAD_DIR, safe_filename)

        try:
            with open(temp_file_path, "wb") as buffer:
                shutil.copyfileobj(uploaded_file.file, buffer)
            
            logger.info(f"[{index}/{file_count}] Ingesting file: {uploaded_file.filename}")
            result = ingest_file(temp_file_path, uploaded_file.filename)
            
            logger.info(f"SUCCESS: File '{uploaded_file.filename}' processed.")
            responses.append(result)

        except Exception as e:
            logger.error(f"FAILURE: Failed to process '{uploaded_file.filename}'. Error: {str(e)}", exc_info=True)
            responses.append({"file": uploaded_file.filename, "status": f"Error: {str(e)}"})
        
        finally:
            if os.path.exists(temp_file_path):
                os.remove(temp_file_path)

    logger.info(f"Batch Upload Completed: {file_count} files processed.")
    return {"results": responses}