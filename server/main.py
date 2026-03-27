from fastapi import FastAPI
from routes.rag import router as rag_router
from routes.file_upload import router as file_router

app = FastAPI(title="RAG API")

@app.get("/")
def root_reader():
    return {
        "message":"The RAG Syatem is UP...."
    }

app.include_router(rag_router, prefix="/rag", tags=["RAG"])
app.include_router(file_router, prefix="/files", tags=["File Upload"])