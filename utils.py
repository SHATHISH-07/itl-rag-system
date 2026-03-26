import re

# Chunkimg the retrieved text
def chunk_text(text, chunk_size=250, overlap=50):
    sentences = re.split(r'(?<=[.!?])\s+', text)

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