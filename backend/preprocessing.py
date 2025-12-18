import re
from langdetect import detect
import nltk
from nltk.teokenize import sent_tokenize

nltk.download('punkt')

#clean text
def clean_text(text):
    if not text :
        return ""
    
    text  = re.sub(r'\s+',' ',text)
    text = re.sub(r'\n+','\n',text)
    text = text.strip()
    return text

#Sentence Segmentation

def segmant_sentences(text):
    if not text:
        return []
    return sent_tokenize(text)

#Language detect

def detect_lan(text):
    try:
        return detect(text)
    except:
        return 'Unknown'
    
#text status
def calculate_text_stats(text):
    word = text.split()
    senetnce = segmant_sentences(text)

    word_count = len(word)
    sentence_count = len(senetnce)

    return {
        "Word_count":word_count,
        "Character_count": len(text),
        "sentence_count":sentence_count,
        "avg_sentence)length":word_count / sentence_count if sentence_count else 0,
        "estimated_reading_time_min":round(word_count/200,2)

    } 

def chunk_text(text,chunk_size=1000,overlap=100):
    sentence = segmant_sentences(text)
    chunks = []

    current_chunk = []
    current_length = 0
    chunk_id = 1

    for senetences in sentence:
        words = senetences.split()
        if current_length + len(words) > chunk_size:
            chunks.append({
                "chunk_id":chunk_id,
                "text": " ".join(current_chunk)
            }) 
            chunk_id+=1
            current_chunk = current_chunk[-overlap:]
            current_length = sum(len(s.split()) for s in current_chunk)
        current_chunk.append(senetences)
        current_length += len(words)
    if current_chunk:
        chunks.append({
            "chunk_id": chunk_id,
            "text": " ".join(current_chunk)
        })

    return chunks
def  preprocess_for_summarization(text,chunk_size=1000):
    if not text or len(text.split()) < 100:
        raise ValueError("Text too short for summarization.")

    cleaned_text = clean_text(text)
    language = detect_lan(clean_text)
    sentence = segmant_sentences(cleaned_text)
    stats = calculate_text_stats(cleaned_text)
    chunk = chunk_text(cleaned_text,chunk_size)

    return{
        "cleaned_text": cleaned_text,
        "language": language,
        "sentences": sentence,
        "stats": stats,
        "chunks": chunk
    }   