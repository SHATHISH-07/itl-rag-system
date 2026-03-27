import logging
import time
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from routes.rag import router as rag_router
from routes.file_upload import router as file_router

# 1. Global Logging Configuration
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s - %(message)s",
    handlers=[
        logging.StreamHandler() # Outputs to console
    ]
)
logger = logging.getLogger("main")

app = FastAPI(title="RAG API")

# 2. CORS Configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.middleware("http")
async def log_requests(request: Request, call_next):
    start_time = time.time()
    path = request.url.path
    method = request.method
    
    logger.info(f"Incoming request: {method} {path}")
    
    response = await call_next(request)
    
    process_time = (time.time() - start_time) * 1000
    formatted_time = "{0:.2f}ms".format(process_time)
    
    logger.info(f"Completed request: {method} {path} | Status: {response.status_code} | Time: {formatted_time}")
    
    return response

@app.get("/")
def root_reader():
    return {
        "message": "The RAG System is UP...."
    }

app.include_router(rag_router, prefix="/rag", tags=["RAG"])
app.include_router(file_router, prefix="/files", tags=["File Upload"])

logger.info("RAG API is initialized and routers are loaded.")