import os
import re
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import List, Optional

try:
    import google.generativeai as genai
except ImportError:
    genai = None


class FastSummarizer:
    """Gemini-backed summarizer with a local extractive fallback."""

    MODEL_NAME = "gemini-1.5-flash"
    _instance = None

    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._is_initialized = False
        return cls._instance

    def __init__(self, model_name: Optional[str] = None):
        self.model_name = model_name or self.MODEL_NAME
        self.max_input_tokens = 4000
        self.chunk_chars = 4000

        if not getattr(self, "_is_initialized", False):
            self._init_model()
            self._is_initialized = True

    def _init_model(self):
        self.model = None
        self.using_gemini = False

        if genai is None:
            return

        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key:
            return

        try:
            genai.configure(api_key=api_key)
            self.model = genai.GenerativeModel(self.MODEL_NAME)
            self.using_gemini = True
        except Exception:
            self.model = None
            self.using_gemini = False

    def summarize_chunk(self, text: str, min_length: int = 60, max_length: int = 150, summary_options=None) -> str:
        if not text:
            return ""

        if len(text.strip()) < 100:
            return text.strip()

        if self.using_gemini and self.model is not None:
            try:
                prompt = (
                    "Summarize the following text clearly and concisely.\n\n"
                    f"Target length: about {min_length}-{max_length} words.\n\n"
                    f"TEXT:\n{text}"
                )
                response = self.model.generate_content(prompt)
                response_text = getattr(response, "text", "") or ""
                if response_text.strip():
                    return response_text.strip()
            except Exception:
                pass

        return self.extractive_fallback(text, min_length=min_length, max_length=max_length)

    def fast_summarize_chunk(self, text: str, min_length: int = 60, max_length: int = 150) -> str:
        return self.summarize_chunk(text, min_length=min_length, max_length=max_length)

    def extractive_fallback(self, text: str, min_length: int = 60, max_length: int = 150) -> str:
        sentences = [s.strip() for s in re.split(r"[.!?]", text) if len(s.strip()) > 20]
        if sentences:
            target_sentences = 2 if max_length <= 120 else 3
            return ". ".join(sentences[:target_sentences]) + "."

        words = text.split()
        if not words:
            return ""

        target_words = max(20, min(len(words), max_length))
        summary = " ".join(words[:target_words]).strip()
        if summary and summary[-1] not in ".!?":
            summary += "."
        return summary

    def smart_chunk_text(self, text: str) -> List[str]:
        words = text.split()
        words_per_chunk = 700
        chunks = []

        for i in range(0, len(words), words_per_chunk):
            chunk = " ".join(words[i:i + words_per_chunk])
            if len(chunk) > 80:
                chunks.append(chunk)

        return chunks or ([text.strip()] if text and text.strip() else [])

    def summarize_chunks_parallel(self, chunks: List[str], max_workers: int = 3) -> List[str]:
        summaries = []

        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            futures = [executor.submit(self.summarize_chunk, chunk) for chunk in chunks]

            for future in as_completed(futures):
                try:
                    summaries.append(future.result())
                except Exception:
                    pass

        return summaries

    def parallel_summarize(self, chunks: List[str], max_workers: int = 3) -> List[str]:
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            return list(executor.map(self.fast_summarize_chunk, chunks))


class UltraFastSummarizer:
    """Lightweight extractive summarizer used by unit and performance tests."""

    def __init__(self):
        self.name = "UltraFastExtractive"

    def generate_ultra_fast_summary(self, text: str):
        started_at = time.time()
        clean_text = (text or "").strip()

        if not clean_text:
            return {
                "success": False,
                "summary_text": "",
                "processing_time": round(time.time() - started_at, 4),
            }

        sentences = [s.strip() for s in re.split(r"(?<=[.!?])\s+|\n+", clean_text) if s.strip()]
        if len(sentences) >= 2:
            summary_text = " ".join(sentences[:2])
        else:
            words = clean_text.split()
            summary_text = " ".join(words[: min(80, len(words))])
            if summary_text and summary_text[-1] not in ".!?":
                summary_text += "."

        return {
            "success": True,
            "summary_text": summary_text,
            "processing_time": round(time.time() - started_at, 4),
        }
