import re
import logging
from core.llm_client import client, LLM_MODEL
from utils.helpers import format_score

logger = logging.getLogger(__name__)

def generate_answer(query: str, retrieved_chunks: list) -> str:
    logger.info(f"Generating answer for query: '{query}'")
    
    # Filter out extremely low relevance chunks (Noise Filter)
    valid_chunks = [c for c in retrieved_chunks if c.get("score", 0) > 0.40]

    if not valid_chunks:
        return "I don't know based on the provided context."

    context_blocks = []
    for i, chunk in enumerate(valid_chunks, start=1):
        clean_text = re.sub(r"\s+", " ", chunk.get("text", "")).strip()
        score = chunk.get("score", 0)
        f_score = format_score(score)
        
        block = f"[Doc {i}] (Source: {chunk.get('source', 'Unknown')}, Relevance: {f_score}) {clean_text}"
        context_blocks.append(block)

    context = " ".join(context_blocks)
    logger.info(f"Context constructed with {len(valid_chunks)} chunks")

    prompt = f"""
You are a retrieval-based AI assistant. Answer the question strictly using ONLY the provided context.

RULES (MANDATORY)

* Use ONLY the given context.
* Do NOT use prior knowledge.
* Do NOT hallucinate or assume missing information.
* If the answer is not present in the context, respond EXACTLY:
  "I don't know based on the provided context."
* Don't include any unnecessary information in the final result
* Do not reply for the empty query and whitespaces.

ANSWER STRUCTURE (STRICT)

* Organize your answer clearly using HTML tags:
  * <h2> for main headings (include relavent emojis)
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
* format: <b>(Sources: filename | Relevance: XX%)</b>
* If multiple relevance scores exist for the same filename, use the HIGHEST relevance.
* Do NOT put citations inside headings or bullet points.
* Do NOT repeat the same filename in multiple citations for the same section.
* Do not hallucinate on the filenames should not mention file names on your own

FINAL SOURCES SUMMARY

* At the end of the answer, list ALL UNIQUE sources used in the entire response.
* Include ONLY the filenames (ignore relevance scores in this summary).
* If a filename appears multiple times, show it only once.
* Always be sure to give a file name once even if multiple source come from the same file then in the final source it is enough to mention the file name only once also never forget to mention any source file name in the sections and aslo at the final
* Format exactly like:
<p><b>Sources:</b> filename1, filename2</p>

CONTEXT
{context}

QUESTION
{query}
"""

    try:
        response = client.chat.completions.create(
            model=LLM_MODEL,
            messages=[
                {"role": "system", "content": "You are a specialized RAG assistant that provides structured HTML responses."},
                {"role": "user", "content": prompt}
            ],
            temperature=0 
        )

        answer = response.choices[0].message.content
        return answer.replace("\n", " ").strip() if answer else "I don't know based on the provided context."

    except Exception as e:
        logger.error(f"LLM failure: {str(e)}")
        return "An error occurred while generating the answer."