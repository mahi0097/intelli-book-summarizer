# backend/models/summarizer.py
from transformers import pipeline, AutoTokenizer, AutoModelForSeq2SeqLM
import torch
import time
import os


class Summarizer:
    _instance = None
    _model_loaded = False
    
    def __new__(cls, model_name="sshleifer/distilbart-cnn-12-6"):
        """Singleton pattern - load model only once"""
        if cls._instance is None:
            cls._instance = super(Summarizer, cls).__new__(cls)
            cls._instance._initialize_model(model_name)
        return cls._instance
    
    def _initialize_model(self, model_name):
        """Initialize model only once"""
        try:
            print(f"⏳ Loading model: {model_name} (first time only)...")
            
            # Use cache directory
            cache_dir = os.path.join(os.path.expanduser("~"), ".cache", "book_summarizer")
            os.makedirs(cache_dir, exist_ok=True)
            
            self.tokenizer = AutoTokenizer.from_pretrained(
                model_name, 
                cache_dir=cache_dir
            )
            self.model = AutoModelForSeq2SeqLM.from_pretrained(
                model_name,
                cache_dir=cache_dir
            )

            self.pipeline = pipeline(
                "summarization",
                model=self.model,
                tokenizer=self.tokenizer,
                device=0 if torch.cuda.is_available() else -1
            )
            
            self._model_loaded = True
            print("✅ Model loaded successfully!")
            
        except Exception as e:
            print(f"❌ Model loading failed: {e}")
            raise RuntimeError(f"Failed to load summarization model: {e}")

    def summarize_chunk(self, text, max_length=150, min_length=50):
        """
        Summarize a single chunk of text
        """
        if not text or len(text.split()) < 50:
            return text[:200] if text else ""  # Return truncated text for very short chunks

        try:
            result = self.pipeline(
                text,
                max_length=max_length,
                min_length=min_length,
                do_sample=False,
                num_beams=4,
                early_stopping=True,
                truncation=True
            )
            return result[0]["summary_text"]

        except Exception as e:
            print(f"Summarization error: {e}")
            # Return first 200 characters as fallback
            return text[:200] + "..."

    def get_length_params(self, length="medium"):
        if length == "short":
            return {"max_length": 120, "min_length": 40}
        elif length == "long":
            return {"max_length": 400, "min_length": 150}
        else:
            return {"max_length": 250, "min_length": 80}

    def combine_summaries(self, chunk_summaries, combine_mode="concatenate"):
        """
        Combine multiple chunk summaries
        """
        if not chunk_summaries:
            return ""
            
        # Remove empty summaries
        valid_summaries = [s for s in chunk_summaries if s and len(s.strip()) > 0]
        
        if not valid_summaries:
            return ""
            
        combined = " ".join(valid_summaries)

        # If combine_mode is "summarize" or combined text is too long
        if combine_mode == "summarize" or len(combined.split()) > 1000:
            params = self.get_length_params("medium")
            return self.summarize_chunk(combined, **params)

        return combined

    def post_process_summary(self, summary_text):
        """
        Clean up the generated summary
        """
        if not summary_text:
            return ""
        
        # Remove duplicate sentences
        sentences = summary_text.split('. ')
        unique_sentences = []
        seen = set()
        
        for sentence in sentences:
            clean_sent = sentence.strip()
            if clean_sent and clean_sent not in seen:
                seen.add(clean_sent)
                unique_sentences.append(clean_sent)
        
        # Join back with proper punctuation
        result = '. '.join(unique_sentences)
        if result and not result.endswith('.'):
            result += '.'
        
        return result

    def generate_summary(self, chunks, length="medium", update_progress_callback=None):
        """
        chunks = list of text chunks
        update_progress_callback: function(progress_percentage, message)
        """
        start_time = time.time()
        params = self.get_length_params(length)
        
        if not chunks:
            return {
                "summary_text": "",
                "chunk_summaries": [],
                "processing_time": 0
            }

        chunk_summaries = []
        total_chunks = len(chunks)

        for i, chunk in enumerate(chunks):
            if update_progress_callback:
                progress = int(((i + 1) / total_chunks) * 100)
                update_progress_callback(progress, f"Summarizing chunk {i+1}/{total_chunks}")
            
            # Handle both dict and string chunks
            chunk_text = chunk.get("text") if isinstance(chunk, dict) else chunk
            
            summary = self.summarize_chunk(chunk_text, **params)
            if summary:
                chunk_summaries.append(summary)

        if not chunk_summaries:
            return None

        # Combine and post-process
        combined_summary = self.combine_summaries(chunk_summaries)
        final_summary = self.post_process_summary(combined_summary)

        processing_time = round(time.time() - start_time, 2)

        return {
            "summary_text": final_summary,
            "chunk_summaries": chunk_summaries,
            "processing_time": processing_time
        }