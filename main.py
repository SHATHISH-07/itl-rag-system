from fastapi import FastAPI
from pydantic import BaseModel
from rag import retrieve
from groq import Groq
import os
from dotenv import load_dotenv
import re
from utils import format_score

# env loading
load_dotenv()
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
LLM_MODEL = os.getenv("LLM_MODEL")

# Fast api initialization
app = FastAPI()

# Groq api setup
client = Groq(api_key=GROQ_API_KEY)

class QueryRequest(BaseModel):
    query: str

# Response generating function
def generate_answer(query, retrieved_chunks):
    context_blocks = []

    for i, chunk in enumerate(retrieved_chunks, start=1):
        clean_text = re.sub(r"\s+", " ", chunk.get("text", "")).strip()

        score = round(chunk.get("score", 0), 2)
        formatted_score = format_score(score)

        block = (
            f"[Doc {i}] "
            f"(Source: {chunk.get('source', 'Unknown')}, Relevance: {formatted_score})" 
            f"{clean_text}"
        )

        context_blocks.append(block)

    context = " ".join(context_blocks)

    prompt = f"""
You are a retrieval-based AI assistant. Answer the question strictly using ONLY the provided context.

RULES (MANDATORY)

* Use ONLY the given context.
* Do NOT use prior knowledge.
* Do NOT hallucinate or assume missing information.
* If the answer is not present in the context, respond EXACTLY:
  "I don't know based on the provided context."

ANSWER STRUCTURE (STRICT)

* Organize your answer clearly using HTML tags:
  * <h2> for main headings (include emojis)
  * <h3> for sub-headings
  * <p> for paragraphs / explanations
  * <ul><li> for bullet points
  * Highlight key terms with <b>...</b>
  * Use <br/> for line breaks (do NOT use \n)
* Keep content readable, professional, and well-structured.
* Avoid repeating the same information in multiple sections.
* If asked for "top", "list", or "points": keep explanation short.
* If asked for "explain" or "detailed": provide structured and clear explanations.

SOURCE CITATION RULES

* Every section (<h2> or <h3> and its content) MUST end with EXACTLY ONE citation.
* format: <p><b>(Sources: filename | Relevance: XX%)</b></p>
* If multiple relevance scores exist for the same filename, use the HIGHEST relevance.
* Do NOT put citations inside headings or bullet points.
* Do NOT repeat the same filename in multiple citations for the same section.

FINAL SOURCES SUMMARY

* At the end of the answer, list ALL UNIQUE sources used in the entire response.
* Include ONLY the filenames (ignore relevance scores in this summary).
* If a filename appears multiple times, show it only once.
* Format exactly like:
<p><b>Sources:</b> filename1, filename2</p>

CONTEXT
{context}

QUESTION
{query}
"""

    response = client.chat.completions.create(
        model=LLM_MODEL,
        messages=[
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user", "content": prompt}
        ]
    )

    answer = response.choices[0].message.content
    clean_answer = answer.replace("\n", " ").strip()

    return clean_answer

# root endpoint
@app.get("/")
def home():
    return {"message": "RAG API is running"}

# chat endpoint
@app.post("/query")
def query_rag(request: QueryRequest):
    query = request.query
    results = retrieve(query)

    if not results:
        return{
            "query":query,
            "answer":"No relavent answer",
            "sources":[]
        }

    answer = generate_answer(query, results)
    sources = list(set([r["source"] for r in results]))

    return {
        "query": query,
        "answer": answer,
        "sources": sources
    }