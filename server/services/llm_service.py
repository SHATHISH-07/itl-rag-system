import json
import logging
import re
from core.llm_client import client, LLM_MODEL

logger = logging.getLogger(__name__)

def generate_answer(query: str, retrieved_chunks: list) -> list:
    if not retrieved_chunks:
        return []

    # Prepare context: include the source directly so the LLM can map it easily
    context_blocks = []
    for i, c in enumerate(retrieved_chunks, start=1):
        source_name = c.get('metadata', {}).get('source', 'Unknown Document')
        text_content = c.get('text', '').strip()
        context_blocks.append(f"[Doc {i}] SOURCE: {source_name}\nCONTENT: {text_content}")
    
    context = "\n\n".join(context_blocks)

    # Simplified, Strict Prompt
    prompt = f"""
### ROLE
You are a Precise Data Extraction Engine. 

### INPUT DATA
USER QUERY: "{query}"
NUMBER OF CHUNKS: {len(retrieved_chunks)}

DOCUMENTS:
{context}

### TASK
Analyze each [Doc X] and return a JSON array containing EXACTLY {len(retrieved_chunks)} objects.

### JSON SCHEMA
[
  {{
    "title": "A unique 3-5 word noun phrase describing the SPECIFIC TOPIC of this chunk (e.g. 'Space Seed Germination', '19th Century Tea Trade')",
    "content": "A concise summary of what this specific document contains regarding the topic.",
    "source": "The exact filename from the SOURCE field",
    "score": "0-100% based on relevance to the query",
    "doc_id": X
  }}
]

### STRICT RULES
1. **UNIQUE TITLES**: Do NOT use 'Irrelevant Document', 'Step-by-Step', or the user's query as a title. Identify the unique subject of the text.
2. **NO NEGATIVES**: Do not start with 'Unfortunately' or 'The document doesn't say'. Just state what information IS there.
3. **1:1 MAPPING**: You must process every document provided. Ensure 'doc_id' matches the [Doc X] number.
4. **CLEAN OUTPUT**: Return ONLY the raw JSON array. No markdown blocks, no intro text, no explanations.
"""

    try:
        response = client.chat.completions.create(
            model=LLM_MODEL,
            messages=[
                {
                    "role": "system", 
                    "content": "You are a JSON extraction tool. You provide unique, descriptive titles for data chunks and avoid generic responses."
                },
                {"role": "user", "content": prompt}
            ],
            temperature=0
        )

        raw_content = response.choices[0].message.content
        
        # Strip potential markdown backticks
        clean_json = re.sub(r"```json|```", "", raw_content).strip()
        
        # Remove any non-printable control characters that break JSON parsing
        clean_json = re.sub(r"[\x00-\x1F\x7F]", " ", clean_json)
        
        data = json.loads(clean_json)
        
        if isinstance(data, list):
            return data
        return []

    except Exception as e:
        logger.error(f"LLM Processing Error: {str(e)}")
        # Return a safe fallback if parsing fails
        return []