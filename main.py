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

CONTEXT USAGE RULE

* Each document in the context contains:
  * Source (file name)
  * Relevance Score
  * Content
* Use this information while answering.
* Each source appears ONLY ONCE in the context with its BEST relevance score.

RESPONSE FORMAT (STRICT HTML)

* Use <h2> for main headings (include emojis)
* Use <h3> for sub-headings
* Use <p> for explanations
* Use <ul><li> for bullet points
* Highlight important terms using <b>...</b>
* Use <br/> for line breaks (do NOT use \n)
* Keep the response clean, structured, and readable
* Do NOT include raw context in the output

EXPLANATION CONTROL (IMPORTANT)

* If the user asks for:
  * "top", "list", "points":
    → Keep explanation SHORT and focused
* If the user asks for:
  * "explain", "detailed":
    → Provide a clear and structured explanation
* Default:
  → Keep answers concise but meaningful
* Do NOT over-explain bullet points.

SOURCE + SCORE CITATION (STRICT)

* Every section MUST end with EXACTLY ONE citation.
* A section = all content under a <h2> or <h3> heading.
* The citation MUST be the LAST paragraph of the section.
* DO NOT place citations:
  * inside headings
  * inside bullet points (<ul> / <li>)
  * in the middle of a section
* Use ONLY the sources provided in the context.
* Do NOT repeat the same source multiple times.
* For example:
    * if the source is like this (Sources: filename1 | Relevance: 87%, filename1 | Relevance: 82%)
    * no need to mention the same filename here filename1 twice mention it once with the highest relavence
    * (Sources: filename1 | Relevance: 87%)

* Use the relevance scores exactly as given.
* Format EXACTLY like:
<p><b>(Sources: filename1 | Relevance: 87%, filename2 | Relevance: 82%)</b></p>

FINAL SOURCE SUMMARY (STRICT)

* At the end of the response, list ALL UNIQUE sources used.
* Include ONLY file names (no relevance scores).
* Each source must appear ONLY ONCE.
* Format EXACTLY like:
<p><b>Sources:</b> filename1, filename2</p>

IMPORTANT

* Do NOT create unnecessary sections.
* Do NOT repeat the same source multiple times.
* Ensure every section has a citation.
* Ensure the final summary is always present.

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
    answer = generate_answer(query, results)
    sources = list(set([r["source"] for r in results]))

    return {
        "query": query,
        "answer": answer,
        "sources": sources
    }