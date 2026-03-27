from fastapi import APIRouter, UploadFile, File
from typing import Annotated
import os
import uuid
import shutil
from services.ingestion_service import ingest_file

router = APIRouter()
TEMP_UPLOAD_DIR = "uploads"
os.makedirs(TEMP_UPLOAD_DIR, exist_ok=True)

@router.post("/upload-files")
async def upload_files(
   files: Annotated[
        list[UploadFile], File(description="Multiple files as UploadFile")
    ],
):
    responses = []

    for uploaded_file in files:
        unique_id = str(uuid.uuid4())[:8]
        safe_filename = f"{unique_id}_{uploaded_file.filename}"
        temp_file_path = os.path.join(TEMP_UPLOAD_DIR, safe_filename)

        try:
            with open(temp_file_path, "wb") as buffer:
                shutil.copyfileobj(uploaded_file.file, buffer)

            result = ingest_file(temp_file_path, uploaded_file.filename)
            responses.append(result)

        except Exception as e:
            responses.append({"file": uploaded_file.filename, "status": f"Error: {str(e)}"})
        
        finally:
            if os.path.exists(temp_file_path):
                os.remove(temp_file_path)

    return {"results": responses}