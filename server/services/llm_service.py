import re
import logging
from core.llm_client import client, LLM_MODEL

logger = logging.getLogger(__name__)

def generate_answer(query: str, retrieved_chunks: list) -> str:
    
    valid_chunks = [c for c in retrieved_chunks if c.get("score", 0) > 0.40]

    if not valid_chunks:
        return "I don't know based on the provided context."

    context_blocks = []
    for i, chunk in enumerate(valid_chunks, start=1):
        clean_text = re.sub(r"\s+", " ", chunk.get("text", "")).strip()
        context_blocks.append(f"[Doc {i}] {clean_text}")

    context = "\n\n".join(context_blocks)

    prompt = f"""
You are a retrieval-based AI. Answer ONLY using the provided context.
--------------------------------------------------
### OUTPUT RULES:
- Use valid HTML: <h2>, <h3>, <p>, <ul>, <li>, <b>, <br/>.
- Divide the answer into multiple <h3> sections.
- Use relavent emojis to the heading and the subheading h2 and h3
- At the end of EVERY section or list, you MUST cite the Document ID used.
- FORMAT for citation: (Source: [Doc X])
- If multiple docs are used in one section: (Source: [Doc X], [Doc Y])
--------------------------------------------------
CONTEXT:
{context}

QUESTION:
{query}
"""

    try:
        response = client.chat.completions.create(
            model=LLM_MODEL,
            messages=[
                {"role": "system", "content": "You provide structured HTML responses with [Doc X] citations."},
                {"role": "user", "content": prompt}
            ],
            temperature=0 
        )

        answer = response.choices[0].message.content
        return answer.replace("\n", " ").strip() if answer else "I don't know based on the provided context."

    except Exception as e:
        logger.error(f"LLM failure: {str(e)}")
        return "An error occurred while generating the answer."