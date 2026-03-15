import os
import re
from typing import List

import requests
from dotenv import load_dotenv


class FastSummarizer:
    """
    Summarizer with Gemini 2.5 Flash as the primary provider.
    Falls back to local Hugging Face BART if Gemini is unavailable.
    """

    GEMINI_MODEL = "gemini-2.5-flash"
    GEMINI_ENDPOINT = (
        "https://generativelanguage.googleapis.com/v1beta/models/"
        "{model}:generateContent"
    )
    HF_MODEL_NAME = "facebook/bart-base"

    _instance = None

    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self, model_name=None):
        if self._initialized:
            return

        load_dotenv()
        self.model_name = model_name or self.GEMINI_MODEL
        self.gemini_api_key = os.getenv("GEMINI_API_KEY", "").strip()
        self.provider = "gemini" if self.gemini_api_key else "huggingface"
        self.chunk_chars = 12000 if self.provider == "gemini" else 2000
        self.max_input_tokens = self.chunk_chars
        self._initialized = True

        if self.provider == "gemini":
            print(f"Using Gemini summarizer: {self.model_name}")
            return

        self._init_huggingface_model()

    def _init_huggingface_model(self):
        self.device = -1
        self.tokenizer = None
        self.model = None
        self.pipeline = None

        try:
            from transformers import AutoModelForSeq2SeqLM, AutoTokenizer, pipeline
            import torch
        except ImportError as exc:
            print(
                "Hugging Face runtime dependencies are unavailable; "
                "using extractive fallback summaries instead."
            )
            print(f"Dependency error: {exc}")
            return

        print(f"Loading Hugging Face summarizer: {self.HF_MODEL_NAME}")

        cache_dir = os.path.join(os.path.expanduser("~"), ".cache", "book_summarizer")
        os.makedirs(cache_dir, exist_ok=True)

        self.device = 0 if torch.cuda.is_available() else -1
        self.chunk_chars = 2200 if self.device == 0 else 2000

        try:
            self.tokenizer = AutoTokenizer.from_pretrained(
                self.HF_MODEL_NAME,
                cache_dir=cache_dir,
                use_fast=True,
            )

            self.model = AutoModelForSeq2SeqLM.from_pretrained(
                self.HF_MODEL_NAME,
                cache_dir=cache_dir,
                low_cpu_mem_usage=True,
            )

            self.pipeline = pipeline(
                "summarization",
                model=self.model,
                tokenizer=self.tokenizer,
                device=self.device,
                batch_size=1,
            )
        except Exception as exc:
            print(
                "Failed to initialize the Hugging Face summarizer; "
                "using extractive fallback summaries instead."
            )
            print(f"Initialization error: {exc}")
            self.device = -1
            self.tokenizer = None
            self.model = None
            self.pipeline = None
            return

        print("BART model ready")
        print(f"Chunk size: {self.chunk_chars} chars")
        print(f"Device: {'GPU' if self.device == 0 else 'CPU'}")

    def summarize_chunk(
        self,
        text: str,
        min_length=60,
        max_length=150,
        summary_options=None,
    ) -> str:
        if self.provider == "gemini":
            return self._summarize_with_gemini(text, min_length, max_length, summary_options)
        return self._summarize_with_huggingface(text, min_length, max_length)

    def _summarize_with_gemini(self, text: str, min_length=60, max_length=150, summary_options=None) -> str:
        if not text or len(text.strip()) < 50:
            return text

        summary_options = summary_options or {}
        style = summary_options.get("style", "paragraph").replace("_", " ")
        tone = summary_options.get("tone", "neutral")
        focus_keywords = summary_options.get("focus_keywords", [])
        include_key_points = summary_options.get("include_key_points", True)
        include_quotes = summary_options.get("include_quotes", False)

        structure_instruction = {
            "bullet_points": "Format the result as concise bullet points.",
            "executive_summary": "Format the result as a compact executive summary with a short heading and 2-4 clear paragraphs.",
            "paragraph": "Format the result as a well-structured paragraph summary of at least 3 sentences when the source text is long enough.",
        }.get(summary_options.get("style", "paragraph"), "Format the result as a clear paragraph summary.")

        focus_instruction = (
            f"Pay extra attention to these focus keywords: {', '.join(focus_keywords)}.\n"
            if focus_keywords else ""
        )
        key_points_instruction = "Include the main key points explicitly.\n" if include_key_points else ""
        quotes_instruction = "Include important short quotes only if they materially help the summary.\n" if include_quotes else ""

        prompt = (
            "Summarize the following book content clearly and accurately.\n"
            f"Target length: {min_length}-{max_length} words.\n"
            f"Tone: {tone}.\n"
            f"Requested style: {style}.\n"
            "Preserve key facts, names, arguments, and chronology.\n"
            f"{structure_instruction}\n"
            f"{focus_instruction}"
            f"{key_points_instruction}"
            f"{quotes_instruction}"
            "Return only the summary text.\n\n"
            f"CONTENT:\n{text[:self.chunk_chars]}"
        )

        payload = {
            "contents": [
                {
                    "parts": [
                        {"text": prompt}
                    ]
                }
            ],
            "generationConfig": {
                "temperature": 0.2,
                "topP": 0.8,
                "maxOutputTokens": min(max_length * 3, 1024),
            },
        }

        try:
            response = requests.post(
                self.GEMINI_ENDPOINT.format(model=self.model_name),
                params={"key": self.gemini_api_key},
                json=payload,
                timeout=8,
            )
            response.raise_for_status()
            data = response.json()

            candidates = data.get("candidates", [])
            if not candidates:
                raise ValueError(f"No candidates returned: {data}")

            parts = candidates[0].get("content", {}).get("parts", [])
            summary = "".join(part.get("text", "") for part in parts).strip()
            return summary or self.extractive_fallback(text, min_words=min_length, max_words=max_length)
        except Exception as e:
            print(f"Gemini summarization failed: {e}")
            return self.extractive_fallback(text, min_words=min_length, max_words=max_length)

    def _summarize_with_huggingface(self, text: str, min_length=60, max_length=150) -> str:
        if not text or len(text) < 100:
            return text

        try:
            result = self.pipeline(
                text[:self.chunk_chars],
                min_length=min_length,
                max_length=max_length,
                do_sample=False,
                num_beams=2,
                truncation=True,
                early_stopping=True,
                no_repeat_ngram_size=2,
            )
            return result[0]["summary_text"].strip()
        except Exception as e:
            print(f"Hugging Face chunk summarization failed: {e}")
            return self.extractive_fallback(text, min_words=min_length, max_words=max_length)

    def extractive_fallback(self, text: str, min_words: int = 60, max_words: int = 150) -> str:
        """Build a fuller fallback summary when model output is unavailable or too short."""
        if not text:
            return ""

        cleaned_text = re.sub(r"\s+", " ", text).strip()
        original_words = cleaned_text.split()
        original_word_count = len(original_words)
        sentences = re.split(r"(?<=[.!?])\s+", cleaned_text)
        sentences = [s.strip() for s in sentences if len(s.strip()) > 20]

        # Keep fallback output meaningfully shorter than the source when possible.
        summary_cap = max_words
        if original_word_count > 1:
            summary_cap = min(summary_cap, original_word_count - 1)
        summary_cap = max(summary_cap, 1)

        if not sentences:
            if not original_words:
                return ""
            fallback_target = min(summary_cap, max(min_words, min(120, summary_cap)))
            fallback_words = original_words[:fallback_target]
            summary = " ".join(fallback_words).strip()
            if summary and summary[-1] not in ".!?":
                summary += "."
            return summary

        selected = []
        word_total = 0
        target_words = max(min_words, 80)
        hard_cap = max(1, min(summary_cap, max(max_words, target_words)))

        for sentence in sentences:
            sentence_words = len(sentence.split())
            if sentence_words < 4:
                continue

            selected.append(sentence)
            word_total += sentence_words

            if word_total >= target_words or len(selected) >= 6:
                break

        if not selected:
            selected = sentences[:3]

        summary = " ".join(selected).strip()
        summary_words = summary.split()
        if len(summary_words) > hard_cap:
            summary = " ".join(summary_words[:hard_cap]).strip()

        if summary and summary[-1] not in ".!?":
            summary += "."
        return summary

    def smart_chunk_text(self, text: str) -> List[str]:
        words = text.split()
        if self.provider == "gemini":
            words_per_chunk = 1400
        else:
            words_per_chunk = 350 if getattr(self, "device", -1) == 0 else 280

        chunks = []
        for i in range(0, len(words), words_per_chunk):
            chunk = " ".join(words[i:i + words_per_chunk])
            if len(chunk) > 80:
                chunks.append(chunk)

        print(f"Smart chunks created: {len(chunks)} using {self.provider}")
        return chunks

    def summarize_chunks_parallel(self, chunks: List[str]) -> List[str]:
        return [self.summarize_chunk(chunk) for chunk in chunks]

    def parallel_summarize(self, chunks: List[str], max_workers=2) -> List[str]:
        # Backward-compatible alias expected by older tests.
        return self.summarize_chunks_parallel(chunks)

    def fast_summarize_chunk(self, text: str, min_length=60, max_length=150) -> str:
        # Backward-compatible alias expected by older tests.
        return self.summarize_chunk(text, min_length, max_length)


class UltraFastSummarizer:
    """Lightweight extractive summarizer kept for test/perf compatibility."""

    def __init__(self):
        self.name = "UltraFastExtractive"

    def generate_ultra_fast_summary(self, text: str):
        start_text = (text or "").strip()
        if not start_text:
            return {
                "success": False,
                "summary_text": "",
                "processing_time": 0.0,
            }

        import time

        start = time.time()
        sentences = re.split(r"(?<=[.!?])\s+", start_text)
        cleaned = [s.strip() for s in sentences if s.strip()]

        if len(cleaned) >= 3:
            summary_text = " ".join(cleaned[:3])
        else:
            words = start_text.split()
            summary_text = " ".join(words[: min(len(words), 120)])

        return {
            "success": True,
            "summary_text": summary_text.strip(),
            "processing_time": max(time.time() - start, 0.0001),
        }
