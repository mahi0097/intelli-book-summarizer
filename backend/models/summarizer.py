import google.generativeai as genai
import os
import re
from typing import List
from concurrent.futures import ThreadPoolExecutor, as_completed


class FastSummarizer:

    MODEL_NAME = "gemini-1.5-flash"   # fast + cheap model

    _instance = None

    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._init_model()
        return cls._instance

    def _init_model(self):

        print("⚡ Loading Gemini summarizer")

        genai.configure(api_key=os.getenv("GEMINI_API_KEY"))

        self.model = genai.GenerativeModel(self.MODEL_NAME)

        self.chunk_chars = 4000

        print("✅ Gemini model ready")

    # -------------------------------------------------

    def summarize_chunk(self, text: str) -> str:

        if not text or len(text) < 100:
            return text

        try:

            prompt = f"""
            Summarize the following text clearly and concisely.

            TEXT:
            {text}
            """

            response = self.model.generate_content(prompt)

            return response.text.strip()

        except Exception as e:

            print(f"⚠️ Gemini failed: {e}")
            return self.extractive_fallback(text)

    # -------------------------------------------------

    def extractive_fallback(self, text: str) -> str:

        sentences = re.split(r'[.!?]', text)
        sentences = [s.strip() for s in sentences if len(s.strip()) > 20]

        return ". ".join(sentences[:2]) + "." if sentences else text[:200]

    # -------------------------------------------------

    def smart_chunk_text(self, text: str) -> List[str]:

        words = text.split()

        words_per_chunk = 700

        chunks = []

        for i in range(0, len(words), words_per_chunk):

            chunk = " ".join(words[i:i + words_per_chunk])

            if len(chunk) > 80:
                chunks.append(chunk)

        print(f"📦 Smart chunks created: {len(chunks)}")

        return chunks

    # -------------------------------------------------

    def summarize_chunks_parallel(self, chunks: List[str]) -> List[str]:

        summaries = []

        with ThreadPoolExecutor(max_workers=3) as executor:

            futures = [executor.submit(self.summarize_chunk, c) for c in chunks]

            for f in as_completed(futures):
                try:
                    summaries.append(f.result())
                except:
                    pass

        return summaries