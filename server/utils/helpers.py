import os
import re
import docx
import nltk
from nltk.tokenize import PunktSentenceTokenizer
import logging
import fitz

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

def chunk_text(text: str):
    text = re.sub(r'(\w+)-\s+(\w+)', r'\1\2', text)
    text = re.sub(r'\s+', ' ', text).strip()
    
    tokenizer = PunktSentenceTokenizer()
    sentences = tokenizer.tokenize(text)
    
    cleaned_sentences = []
    for s in sentences:
        s_cleaned = re.sub(r'[\.\s_]{2,}$', '', s).strip()
        
        if len(s_cleaned) > 5 and any(c.isalpha() for c in s_cleaned):
            cleaned_sentences.append(s_cleaned)

    chunks = []
    STEP_SIZE = 8      
    WINDOW_SIZE = 10    

    for i in range(0, len(cleaned_sentences), STEP_SIZE):
        window = cleaned_sentences[i : i + WINDOW_SIZE]
        if not window:
            continue
            
        chunk_content = " ".join(window).strip()
        
        if len(chunk_content) > 0 and (chunk_content.count('.') / len(chunk_content) > 0.3):
            continue

        chunks.append(chunk_content)
        
        if i + WINDOW_SIZE >= len(cleaned_sentences):
            break
            
    logger.info(f"Scaled Chunking: created {len(chunks)} cleaned chunks.")
    return chunks

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

def get_collection_name(file_name):
    clean_name = re.sub(r'[^\w\s-]', '', file_name.lower().replace(".txt", ""))
    return f"{clean_name}_collection"

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
                    if dot_density > 0.05: # If more than 5% of characters are dots
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