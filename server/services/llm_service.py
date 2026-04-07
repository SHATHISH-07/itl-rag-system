import json
import logging
import re
from core.llm_client import client, LLM_MODEL

logger = logging.getLogger(__name__)

def is_procedural_query(query: str):
    keywords = ["how", "steps", "procedure", "make", "prepare", "recipe", "guide", "instructions", "process"]
    return any(k in query.lower() for k in keywords)

def generate_answer(query: str, retrieved_chunks: list):
    if not retrieved_chunks:
        return {"status": "no_relevant_data", "answer": "I don't know based on the provided context."}

    context_blocks = []
    for i, c in enumerate(retrieved_chunks, start=1):
        source_name = c.get('source', 'Unknown Document')
        text_content = c.get('text', '').strip()
        context_blocks.append(f"[ID: {i}] SOURCE: {source_name}\nCONTENT: {text_content}")

    context = "\n\n".join(context_blocks)

    prompt = f"""
You are a precise technical synthesizer. Your goal is to summarize the provided DOCUMENTS to answer the USER QUERY.

USER QUERY: "{query}"

DOCUMENTS:
{context}

RULES:
1. CONCISE SUMMARY: Each "content" field must be exactly 4 to 5 sentences long. Avoid long-winded "walls of text."
2. DIRECTNESS: Get straight to the point. Every sentence must provide unique, factual value from the document.
3. CITATION: Mention the [ID: number] within the narrative flow of your summary.
4. JSON ONLY: Do not provide any conversational text before or after the JSON array.

EXPECTED JSON STRUCTURE:
[
  {{
    "doc_id": number,
    "title": "Short, Descriptive Heading",
    "content": "A high-density summary consisting of exactly 4 to 5 professional sentences based on this document.",
    "source": "filename from the doc source",
    "score": "0-100%"
  }}
]
"""

    try:
        response = client.chat.completions.create(
            model=LLM_MODEL,
            messages=[
                {"role": "system", "content": "You are a specialized JSON agent that provides dense, 4-5 sentence summaries of technical text."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.15
        )

        raw = response.choices[0].message.content
        match = re.search(r'(\[.*\]|\{.*\})', raw, re.DOTALL)
        if not match: 
            raise ValueError("No JSON detected in LLM output")
            
        clean = re.sub(r"[\x00-\x1F\x7F]", " ", match.group(0))
        return json.loads(clean)

    except Exception as e:
        logger.error(f"LLM error: {e}")
        return {"status": "error", "answer": f"LLM failed: {str(e)}"}