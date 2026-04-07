import json
import logging
import re
from core.llm_client import client, LLM_MODEL

logger = logging.getLogger(__name__)

def generate_answer(query: str, retrieved_chunks: list):
    if not retrieved_chunks:
        return {"status": "no_relevant_data"}

    # Pass the top 10 chunks to the LLM to ensure it has enough material for 5+ results
    sorted_chunks = sorted(retrieved_chunks, key=lambda x: x.get("score", 0), reverse=True)
    context = "\n\n".join([
        f"[ID: {i+1}] SOURCE: {c.get('source')}\nCONTENT: {c.get('text')}"
        for i, c in enumerate(sorted_chunks[:10])
    ])

    prompt = f"""
You are an Expert Historical Analyst. Your goal is to synthesize the USER QUERY using the provided DOCUMENTS.

USER QUERY: "{query}"

DOCUMENTS:
{context}

CRITICAL ALIGNMENT RULES:
1. SEMANTIC RE-RANKING: The order of the JSON array MUST be based on relevance to the QUERY, not the retrieval score. Place the document that best explains the "Why" and "Causes" at index 0.
2. TITLE RELEVANCE: The "title" field MUST be a concise, query-specific analytical heading that captures the core insight of the document in relation to the query. It should NOT be a generic title or a direct copy from the source. the title should match the query about 90% of the time.
3. NO FILLER: If a document is about late-war events (like the 1917 blockade), explain it as a 'Secondary Factor' or discard it if it provides zero insight into the war's causes.
4. SCORE PRESERVATION: Keep the original "score" value in the JSON, but do NOT use it to determine the list order. The list order is determined by Query-Relevance.
5. EXACT BREVITY: Each "content" section MUST be exactly 3 sentences. 

EXPECTED JSON STRUCTURE (ONLY):
[
  {{
    "doc_id": number,
    "title": "Query-Specific Analytical Heading",
    "content": "Exactly three sentences of factual synthesis.",
    "source": "filename",
    "score": "Original % score from context"
  }}
]
"""
    try:
        res = client.chat.completions.create(
            model=LLM_MODEL,
            messages=[
                {"role": "system", "content": "You are a JSON-only analyst who provides diverse, query-specific answers."},
                {"role": "user", "content": prompt}
            ],
            temperature=0
        )

        raw = res.choices[0].message.content
        match = re.search(r'(\[.*\])', raw, re.DOTALL)
        if not match: return {"status": "error"}

        results = json.loads(match.group(0))

        # Re-map scores accurately
        for r in results:
            idx = int(r.get("doc_id", 1)) - 1
            if 0 <= idx < len(sorted_chunks):
                score = sorted_chunks[idx].get("score", 0)
                r["score"] = f"{int(score * 100)}%"

        return results

    except Exception as e:
        logger.error(f"LLM Error: {e}")
        return {"status": "error"}