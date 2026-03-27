from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from routes.rag import router as rag_router
from routes.file_upload import router as file_router

app = FastAPI(title="RAG API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def root_reader():
    return {
        "message":"The RAG Syatem is UP...."
    }

app.include_router(rag_router, prefix="/rag", tags=["RAG"])
app.include_router(file_router, prefix="/files", tags=["File Upload"])