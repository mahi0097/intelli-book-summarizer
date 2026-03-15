import re
import nltk
try:
    from langdetect import detect
except ImportError:
    def detect(_text):
        return "en"
from nltk.tokenize import sent_tokenize

# Check whether punkt is available. If not, segment_sentences will fall back
# to simpler splitting without trying to download data at import time.
try:
    nltk.data.find("tokenizers/punkt")
    HAS_PUNKT = True
except LookupError:
    HAS_PUNKT = False


# --------------------------------------------------
# CLEANING
# --------------------------------------------------
def clean_text(
    text,
    remove_references=True,
    remove_tables=True,
    normalize_whitespace=True
):
    if not text:
        return ""

    if remove_references:
        text = re.split(
            r"\n(?:references|bibliography|works cited)\b",
            text,
            flags=re.IGNORECASE
        )[0]

    if remove_tables:
        text = re.sub(r"\n.*\|.*\n", "\n", text)
        text = re.sub(r"\n.*\t.*\t.*\n", "\n", text)

    if normalize_whitespace:
        text = re.sub(r"\n{3,}", "\n\n", text)
        text = re.sub(r"[ \t]+", " ", text)
        text = re.sub(r"\n +\n", "\n\n", text)

    return text.strip()


# --------------------------------------------------
# SENTENCE SEGMENTATION
# --------------------------------------------------
def segment_sentences(text):
    if not text:
        return []

    try:
        sentences = sent_tokenize(text)
    except Exception:
        sentences = text.split(". ")

    if len(sentences) < 3:
        sentences = re.split(r"[•\n\-]", text)

    return [s.strip() for s in sentences if len(s.strip()) > 10]


# --------------------------------------------------
# LANGUAGE DETECTION FUNCTION
# --------------------------------------------------
def detect_language_func(text):
    try:
        return detect(text[:1500])
    except Exception:
        return "en"


# --------------------------------------------------
# STATS
# --------------------------------------------------
def calculate_text_stats(text):
    words = text.split()
    sentences = segment_sentences(text)

    return {
        "word_count": len(words),
        "character_count": len(text),
        "sentence_count": len(sentences),
        "avg_sentence_length": round(len(words) / max(len(sentences), 1), 2),
        "estimated_reading_time_min": round(len(words) / 200, 2),
    }


# --------------------------------------------------
# CHUNKING
# --------------------------------------------------
def chunk_text(text, chunk_size=1000, min_chunk_words=120):
    sentences = segment_sentences(text)

    if len(sentences) <= 1:
        words = text.split()
        return [
            {
                "chunk_id": idx + 1,
                "text": " ".join(words[i:i + chunk_size]).strip()
            }
            for idx, i in enumerate(range(0, len(words), chunk_size))
            if " ".join(words[i:i + chunk_size]).strip()
        ]

    chunks = []
    current = []
    current_len = 0
    chunk_id = 1

    for sentence in sentences:
        words = sentence.split()

        if current_len + len(words) > chunk_size and current_len >= min_chunk_words:
            chunks.append({
                "chunk_id": chunk_id,
                "text": " ".join(current)
            })
            chunk_id += 1
            current = []
            current_len = 0

        current.append(sentence)
        current_len += len(words)

    if current and current_len >= 40:
        chunks.append({
            "chunk_id": chunk_id,
            "text": " ".join(current)
        })

    return chunks


# --------------------------------------------------
# MAIN ENTRY
# --------------------------------------------------
def preprocess_for_summarization(
    text,
    chunk_size=1000,
    remove_references=True,
    remove_tables=True,
    normalize_whitespace=True,
    detect_language=True   # BOOLEAN FLAG
):
    if not text:
        return {
            "success": False,
            "error": "Text too short for summarization",
            "cleaned_text": "",
            "language": "unknown",
            "stats": {},
            "chunks": []
        }

    cleaned_text = clean_text(
        text,
        remove_references,
        remove_tables,
        normalize_whitespace
    )

    if len(cleaned_text.split()) < 80:
        return {
            "success": True,
            "cleaned_text": cleaned_text,
            "language": detect_language_func(cleaned_text) if detect_language else "unknown",
            "stats": calculate_text_stats(cleaned_text),
            "chunks": [cleaned_text]
        }

    language = detect_language_func(cleaned_text) if detect_language else "unknown"

    stats = calculate_text_stats(cleaned_text)
    chunks = chunk_text(cleaned_text, chunk_size)

    if not chunks:
        return {
            "success": False,
            "error": "Chunking failed: no valid chunks created",
            "cleaned_text": cleaned_text,
            "language": language,
            "stats": stats,
            "chunks": []
        }

    return {
        "success": True,
        "cleaned_text": cleaned_text,
        "language": language,
        "stats": stats,
        "chunks": [chunk["text"] for chunk in chunks],
        "chunk_metadata": chunks
    }
