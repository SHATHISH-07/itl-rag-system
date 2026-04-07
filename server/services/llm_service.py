import json
import logging
import re
from core.llm_client import client, LLM_MODEL

logger = logging.getLogger(__name__)

def generate_answer(query: str, retrieved_chunks: list):
    if not retrieved_chunks:
        return {"status": "no_relevant_data"}
    
    sorted_chunks = sorted(retrieved_chunks, key=lambda x: x.get("score", 0), reverse=True)
    context = "\n\n".join([
        f"[ID: {i+1}] SOURCE: {c.get('source')}\nCONTENT: {c.get('text')}"
        for i, c in enumerate(sorted_chunks[:10])
    ])

    prompt = f"""
You are a Lead Historical Researcher. Your task is to transform raw document snippets into a structured analysis of the ORIGINS and CAUSES of the Great War.

USER QUERY: "{query}"

DOCUMENTS:
{context}

STRICT ANALYTICAL PIPELINE:
1. RE-RANK BY INTENT: Disregard the provided 'score'. Re-order the results so that the most fundamental causes (e.g., Alliances, Assassination, Nationalism) appear first.
2. TITLE TRANSFORMATION: The "title" MUST be a 4-7 word analytical claim that answers the query.
   - BAD: "Nationalism and the War"
   - GOOD: "Nationalism as a Catalyst for European Mobilization"
3. CONTENT RE-FRAMING: You are not summarizing the document; you are explaining how the document's facts answer "{query}".
   - Every first sentence must start with a causal claim (e.g., "The document indicates that...", "A primary factor was...").
   - Follow with two supporting factual sentences.
4. CHRONOLOGICAL FILTER: If a document describes 1917 or 1918 (late-war), you must explicitly frame it as a "long-term consequence" or "pre-existing tension" to make it relevant to the 'Causes' query.
5. NO REPETITION: If two documents say the same thing, merge the best facts into one entry or discard the weaker one.
6. In the Final Response if the retrived chunk is of 7 then the final answer should be 7 entries, if the retrived chunk is of 5 then the final answer should be 5 entries and so on. The final answer should not be more than the retrived chunk or less than the retrived chunk.

EXPECTED JSON STRUCTURE:
[
  {{
    "doc_id": number,
    "title": "Analytical Causal Heading",
    "content": "Three sentences: [Causal Claim]. [Supporting Evidence]. [Historical Significance].",
    "source": "filename",
    "score": "Original score from context"
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