import os
import re
import docx
import nltk
from nltk.tokenize import PunktSentenceTokenizer
import logging
import fitz

logger = logging.getLogger(__name__)

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
    
    chunks = []
    STEP_SIZE = 8      
    WINDOW_SIZE = 10    

    for i in range(0, len(sentences), STEP_SIZE):
        window = sentences[i : i + WINDOW_SIZE]
        
        if not window:
            continue
            
        chunk_content = " ".join(window).strip()
        chunks.append(chunk_content)
        
        if i + WINDOW_SIZE >= len(sentences):
            break
            
    logger.info(f"Scaled Chunking: created {len(chunks)} chunks.")
    return chunks

def extract_k(query: str) -> int:
    match = re.search(r'\b(\d+)\b', query)
    if match:
        k = int(match.group(1))
        logger.debug(f"Extracted k={k} from query via digits.")
        return k

    word_to_num = {
        "one": 1, "two": 2, "three": 3, "four": 4, "five": 5,
        "six": 6, "seven": 7, "eight": 8, "nine": 9, "ten": 10
    }

    query_lower = query.lower()
    for word, num in word_to_num.items():
        if word in query_lower:
            logger.debug(f"Extracted k={num} from query via word matching.")
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
    col_name = f"{clean_name}_collection"
    logger.debug(f"Generated collection name: {col_name} for file: {file_name}")
    return col_name

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
            
            for i, page in enumerate(doc):
                page_text = page.get_text("text")
                
                lower_text = page_text.lower()
                if i < 5: 
                    if "table of contents" in lower_text or "contents" in lower_text or "index" in lower_text:
                        logger.info(f"Skipping page {i+1} (Potential TOC/Index)")
                        continue
                    if lower_text.count('.') > 50:
                        logger.info(f"Skipping page {i+1} (High dot density - likely TOC)")
                        continue

                if page_text.strip():
                    text_blocks.append(page_text)
            
            doc.close()
            full_text = "\n".join(text_blocks)
            logger.info(f"Extracted {len(full_text)} characters from PDF.")
            return full_text
                
        elif ext == ".docx":
            doc = docx.Document(file_path)
            content = "\n\n".join(p.text for p in doc.paragraphs if p.text.strip())
            return content
            
        return ""

    except Exception as e:
        logger.error(f"Error extracting text from {filename}: {str(e)}", exc_info=True)
        return ""