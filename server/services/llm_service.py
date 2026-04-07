import re
import json
import logging
from core.llm_client import client, LLM_MODEL

logger = logging.getLogger(__name__)

def generate_answer(query: str, retrieved_chunks: list):
    if not retrieved_chunks:
        return [{"doc_id": 0, "title": "Not Found", "content": "No documents found."}]

    context_str = "\n\n".join([f"CHUNK_ID: {i+1}\nCONTENT: {c.get('text')}" for i, c in enumerate(retrieved_chunks)])

    prompt = f"""
USER QUERY: "{query}"
DOCUMENTS:
{context_str}

1. RELEVANCE: If documents are unrelated to "{query}", return doc_id: 0.
2. TASK: Rephrase EACH relevant chunk into professional analysis.
3. OUTPUT: Return a JSON LIST of objects. One for each CHUNK_ID.

FORMAT:
[
  {{ "doc_id": 1, "title": "Unique Title", "content": "Analysis" }}
]
"""
    try:
        res = client.chat.completions.create(
            model=LLM_MODEL,
            messages=[{"role": "system", "content": "JSON-only output."}, {"role": "user", "content": prompt}],
            temperature=0.1
        )
        raw = res.choices[0].message.content
        match = re.search(r'(\[.*\])', raw, re.DOTALL)
        if match:
            data = json.loads(match.group(0))
            return data if isinstance(data, list) else [data]
        return []
    except Exception as e:
        logger.error(f"Error: {e}")
        return []