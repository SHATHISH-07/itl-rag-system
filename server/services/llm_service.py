import logging
import re
from core.llm_client import client, LLM_MODEL

logger = logging.getLogger(__name__)

MIN_SCORE = 0.40

def generate_answer(query: str, retrieved_chunks: list) -> str:
    valid_chunks = [
        {**c, "original_index": i}
        for i, c in enumerate(retrieved_chunks)
        if c.get("score", 0) >= MIN_SCORE
    ]

    if not valid_chunks:
        return "I don't know based on the provided context."

    context_blocks = [
        f"[Doc {i}] {c.get('text', '').strip()}"
        for i, c in enumerate(valid_chunks, start=1)
    ]
    context = "\n\n".join(context_blocks)

    allowed_docs = ", ".join([f"[Doc {i}]" for i in range(1, len(valid_chunks)+1)])

    prompt = f"""
Answer strictly using the context.

### OUTPUT FORMAT (MANDATORY):
You MUST follow this exact pattern for EVERY section:
<h2> Title </h2>

<h3>Section Title</h3>
<p>Explanation...</p>
<br/><b>[Doc X]</b>

<h3>Next Section</h3>
<p>Explanation...</p>
<br/><b>[Doc Y]</b>

### 🚨 STRICT RULES:
- EVERY <h3> section MUST end with its OWN citation
- If ANY section is missing citation → OUTPUT IS INVALID
- Never start with a citation, it must come at the end of the section
- DO NOT move citations to the end
- DO NOT create a final "Sources" section
- DO NOT skip citations for any section

### 🚨 ALLOWED DOC IDS:
{", ".join([f"[Doc {i}]" for i in range(1, len(valid_chunks)+1)])}

- ONLY use these Doc IDs
- NEVER invent new Doc numbers

### 🚨 ABSOLUTE VALIDATION RULE:
Before finishing your answer:
✔ Check EVERY <h3> has a citation  
✔ If not → FIX IT before output  

### RULES:
- Use ONLY: <h2>, <h3>, <p>, <ul>, <li>, <b>, <br/>
- Use emojis in headers
- Provide detailed explanation
- No hallucination
- If unsure → "I don't know based on the provided context."

CONTEXT:
{context}

QUESTION:
{query}
"""

    try:
        response = client.chat.completions.create(
            model=LLM_MODEL,
            messages=[
                {"role": "system", "content": "You generate structured HTML answers with strict citations."},
                {"role": "user", "content": prompt}
            ],
            temperature=0
        )

        answer = response.choices[0].message.content

        if not answer:
            return "I don't know based on the provided context."

        return re.sub(r"\s+", " ", answer).strip()

    except Exception as e:
        logger.error(f"LLM Error: {str(e)}")
        return "An error occurred while generating the answer."