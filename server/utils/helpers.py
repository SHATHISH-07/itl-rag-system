import os
import re
import docx
import nltk
import logging
from pypdf import PdfReader

# Setup logger for this module
logger = logging.getLogger(__name__)

try:
    nltk.data.find('tokenizers/punkt')
except LookupError:
    logger.info("NLTK punkt tokenizer not found. Downloading...")
    nltk.download('punkt', quiet=True)

def chunk_text(text, chunk_size=250, overlap=50):
    sentences = nltk.sent_tokenize(text)
    chunks = []
    current_chunk = []
    current_length = 0

    for sentence in sentences:
        words = sentence.split()

        if current_length + len(words) > chunk_size:
            chunks.append(" ".join(current_chunk))
            overlap_words = " ".join(current_chunk).split()[-overlap:]
            current_chunk = [" ".join(overlap_words)]
            current_length = len(overlap_words)

        current_chunk.append(sentence)
        current_length += len(words)

    if current_chunk:
        chunks.append(" ".join(current_chunk))

    logger.debug(f"Chunking complete: created {len(chunks)} chunks from text.")
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
                content = f.read()
                logger.info(f"Read {len(content)} characters from text file.")
                return content
                
        elif ext == ".pdf":
            reader = PdfReader(file_path)
            text = ""
            for i, page in enumerate(reader.pages):
                extracted = page.extract_text()
                if extracted:
                    text += extracted + "\n"
            logger.info(f"Extracted {len(text)} characters from {len(reader.pages)} PDF pages.")
            return text
                
        elif ext == ".docx":
            doc = docx.Document(file_path)
            content = "\n".join(paragraph.text for paragraph in doc.paragraphs)
            logger.info(f"Extracted {len(content)} characters from DOCX.")
            return content
            
        else:
            logger.warning(f"Unsupported file extension: {ext} for file {filename}")
            return ""

    except Exception as e:
        logger.error(f"Error extracting text from {filename}: {str(e)}", exc_info=True)
        return ""