import os
from sentence_transformers import CrossEncoder

RERANKING_CROSS_ENCODER = os.getenv("RERANKING_CROSS_ENCODER", "cross-encoder/ms-marco-MiniLM-L-6-v2")

reranker = CrossEncoder(
    RERANKING_CROSS_ENCODER,
    max_length=256,
    device="cpu"
)