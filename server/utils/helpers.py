import os
import re
import docx
import nltk
from nltk.tokenize import PunktSentenceTokenizer
import logging
import fitz
import hashlib
from core.redis_client import redis_client
from core.embeddings import model
import json

logger = logging.getLogger(__name__)

RELEVANCE_SKIP_WORDS = [
    r'\bcontents\b', 
    r'\btable of contents\b', 
    r'\bindex\b', 
    r'\bbibliography\b', 
    r'\breferences\b'
]

try:
    nltk.data.find('tokenizers/punkt')
except LookupError:
    logger.info("NLTK punkt tokenizer not found. Downloading...")
    nltk.download('punkt', quiet=True)

EMBEDDING_DIM = 384

# Function to Chunk text with optimized sliding window approach
def chunk_text(text: str):
    text = re.sub(r'(\w+)-\s+(\w+)', r'\1\2', text)
    text = re.sub(r'\s+', ' ', text).strip()

    # 2. Initial tokenization
    tokenizer = PunktSentenceTokenizer()
    raw_sentences = tokenizer.tokenize(text)

    processed_sentences = []
    temp_buffer = ""

    for s in raw_sentences:
        s = re.sub(r'[\.\s_]{2,}$', '', s).strip()
        
        if len(s.split()) < 5: 
            temp_buffer += s + " "
        else:
            processed_sentences.append(temp_buffer + s)
            temp_buffer = ""
    
    if temp_buffer and processed_sentences:
        processed_sentences[-1] += " " + temp_buffer.strip()

    chunks = []
    WINDOW_SIZE = 10  
    STEP_SIZE = 8     

    for i in range(0, len(processed_sentences), STEP_SIZE):
        window = processed_sentences[i:i + WINDOW_SIZE]
        if not window:
            continue

        chunk = " ".join(window).strip()
        if len(chunk) > 0:
            chunks.append(chunk)

        if i + WINDOW_SIZE >= len(processed_sentences):
            break
  
    logger.info(f"Refined Chunking: {len(chunks)} chunks created from {len(processed_sentences)} true sentences.")
    return chunks

# Function to extract k from query
def extract_k(query: str) -> int:
    match = re.search(r'\b(\d+)\b', query)
    if match:
        return int(match.group(1))

    word_to_num = {
        "one": 1, "two": 2, "three": 3, "four": 4, "five": 5,
        "six": 6, "seven": 7, "eight": 8, "nine": 9, "ten": 10
    }

    query_lower = query.lower()
    for word, num in word_to_num.items():
        if word in query_lower:
            return num
    return 3 

# Function to format score into percentage and relevance label
def format_score(score):
    percentage = round(score * 100)
    if score >= 0.85:
        label = "Highly Relevant"
    elif score >= 0.70:
        label = "Relevant"
    elif score >= 0.50:
        label = "Moderately Relevant"
    else:
        label = "Low Relevance"
    return f"{percentage}% - {label}"

# Function to get collection name from file name
def get_collection_name(file_name):
    clean_name = re.sub(r'[^\w\s-]', '', file_name.lower().replace(".txt", ""))
    return f"{clean_name}_collection"

# Function to extract text from various file types with enhanced PDF filtering
def extract_text_from_file(file_path: str, filename: str) -> str:
    ext = os.path.splitext(filename)[1].lower()
    logger.info(f"Extracting text from {filename} (extension: {ext})")
    
    try:
        if ext in [".txt", ".py", ".ts", ".js", ".csv"]:
            with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                return f.read()
                
        elif ext == ".pdf":
            doc = fitz.open(file_path)
            text_blocks = []
            total_pages = len(doc)
            
            for i, page in enumerate(doc):
                page_text = page.get_text("text")
                lower_text = page_text.lower().strip()
                
                if not lower_text:
                    continue

                is_boundary_page = (i < 8 or i > (total_pages - 8))
                
                if is_boundary_page:
                    header_area = lower_text[:300]
                    if any(re.search(pattern, header_area) for pattern in RELEVANCE_SKIP_WORDS):
                        logger.info(f"Skipping page {i+1}: Matched exclusion keyword.")
                        continue
                    
                    dot_density = lower_text.count('.') / len(lower_text) if len(lower_text) > 0 else 0
                    if dot_density > 0.05: 
                        logger.info(f"Skipping page {i+1}: High dot density (TOC detected).")
                        continue

                text_blocks.append(page_text)
            
            doc.close()
            full_text = "\n".join(text_blocks)
            logger.info(f"Extracted {len(full_text)} characters from {filename} after filtering.")
            return full_text
                
        elif ext == ".docx":
            doc = docx.Document(file_path)
            return "\n\n".join(p.text for p in doc.paragraphs if p.text.strip())
            
        return ""

    except Exception as e:
        logger.error(f"Error extracting text from {filename}: {str(e)}", exc_info=True)
        return ""

# Caching functions
def make_cache_key(prefix: str, text: str):
    normalized = " ".join(text.lower().strip().split())
    return f"{prefix}:{hashlib.sha256(normalized.encode()).hexdigest()}"

# Function to Format score into percentage and relevance label
def format_score(score):
    percentage = round(score * 100)
    if score >= 0.85:
        return f"{percentage}% - Highly Relevant"
    elif score >= 0.60:
        return f"{percentage}% - Relevant & Accurate"
    elif score >= 0.35:
        return f"{percentage}% - Partially Relevant"
    else:
        return f"{percentage}% - Low Relevance"

# Function to get embedding with caching
def get_embedding(query: str):
    embedding_key = make_cache_key("embedding", query)
    if redis_client:
        cached = redis_client.get(embedding_key)
        if cached:
            return json.loads(cached)

    vector = model.encode([query])[0].tolist()
    if redis_client:
        redis_client.setex(embedding_key, 3600, json.dumps(vector))
    return vector

def enforce_section_citations(answer: str) -> str:
    sections = re.split(r"(<h3>.*?</h3>)", answer)

    fixed_output = ""
    current_doc = "[Doc 1]"  # fallback

    for part in sections:
        if part.startswith("<h3>"):
            fixed_output += part
        else:
            if "[Doc" not in part:
                part += f"<br/><b>{current_doc}</b>"
            else:
                # extract last used doc for next fallback
                docs = re.findall(r"\[Doc \d+\]", part)
                if docs:
                    current_doc = docs[-1]

            fixed_output += part

    return fixed_output
