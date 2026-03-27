import os
import re
import docx
import nltk
from pypdf import PdfReader

try:
    nltk.data.find('tokenizers/punkt')
except LookupError:
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

# Formatting the calculated score to percentage
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

# Qdrant Collection name generator
def get_collection_name(file_name):
    clean_name = re.sub(r'[^\w\s-]', '', file_name.lower().replace(".txt", ""))
    return f"{clean_name}_collection"

# Text Extractor
def extract_text_from_file(file_path: str, filename: str) -> str:
    ext = os.path.splitext(filename)[1].lower()
    
    if ext in [".txt", ".py", ".ts", ".js", ".csv"]:
        with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
            return f.read()
            
    elif ext == ".pdf":
        try:
            reader = PdfReader(file_path)
            text = ""
            for page in reader.pages:
                extracted = page.extract_text()
                if extracted:
                    text += extracted + "\n"
            return text
        except Exception as e:
            print(f"Error reading PDF {filename}: {e}")
            return ""
            
    elif ext == ".docx":
        try:
            doc = docx.Document(file_path)
            return "\n".join(paragraph.text for paragraph in doc.paragraphs)
        except Exception as e:
            print(f"Error reading DOCX {filename}: {e}")
            return ""
            
    else:
        return ""