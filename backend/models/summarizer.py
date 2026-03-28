import math
import os
import re
import time
import warnings
from collections import Counter
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Dict, List, Optional

try:
    from google import genai as google_genai
except ImportError:
    google_genai = None

try:
    with warnings.catch_warnings():
        warnings.simplefilter("ignore", FutureWarning)
        import google.generativeai as legacy_genai
except ImportError:
    legacy_genai = None


class FastSummarizer:
    """Gemini-backed summarizer with a stronger local extractive fallback."""

    MODEL_NAME = "gemini-1.5-flash"
    _instance = None
    STOPWORDS = {
        "a", "an", "and", "are", "as", "at", "be", "been", "being", "but", "by",
        "for", "from", "had", "has", "have", "he", "her", "his", "if", "in", "into",
        "is", "it", "its", "of", "on", "or", "that", "the", "their", "them", "they",
        "this", "to", "was", "were", "will", "with", "you", "your",
    }

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
        self.gemini_backend = None

        if google_genai is None and legacy_genai is None:
            return

        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key:
            return

        try:
            if google_genai is not None:
                self.model = google_genai.Client(api_key=api_key)
                self.gemini_backend = "google_genai"
                self.using_gemini = True
                return
        except Exception:
            self.model = None
            self.using_gemini = False
            self.gemini_backend = None

        try:
            if legacy_genai is not None:
                legacy_genai.configure(api_key=api_key)
                self.model = legacy_genai.GenerativeModel(self.MODEL_NAME)
                self.gemini_backend = "legacy_genai"
                self.using_gemini = True
        except Exception:
            self.model = None
            self.using_gemini = False
            self.gemini_backend = None

    def summarize_chunk(
        self,
        text: str,
        min_length: int = 60,
        max_length: int = 150,
        summary_options=None,
    ) -> str:
        if not text:
            return ""

        clean_text = re.sub(r"\s+", " ", text).strip()
        if len(clean_text.split()) < 30:
            return clean_text

        if self.using_gemini and self.model is not None:
            try:
                prompt = self._build_prompt(clean_text, min_length, max_length, summary_options or {})
                response_text = self._generate_with_model(prompt)
                if self._looks_too_extractive(response_text, clean_text):
                    response_text = ""
                polished = self._normalize_model_output(
                    response_text,
                    min_length=min_length,
                    max_length=max_length,
                    summary_options=summary_options or {},
                )
                if polished:
                    return polished
            except Exception:
                pass

        return self.extractive_fallback(
            clean_text,
            min_length=min_length,
            max_length=max_length,
            summary_options=summary_options,
        )

    def _build_prompt(
        self,
        text: str,
        min_length: int,
        max_length: int,
        summary_options: Dict,
    ) -> str:
        tone = summary_options.get("tone", "neutral").replace("_", " ")
        style = summary_options.get("style", "paragraph").replace("_", " ")
        requested_length = summary_options.get("length", "medium")
        focus_keywords = summary_options.get("focus_keywords") or []
        include_key_points = summary_options.get("include_key_points", True)
        include_quotes = summary_options.get("include_quotes", False)

        style_instruction = {
            "paragraph": "Write in 1 to 3 coherent paragraphs.",
            "bullet points": "Write as concise bullet points.",
            "bullet_points": "Write as concise bullet points.",
            "executive summary": "Write an executive summary with a brief overview and key takeaways.",
            "executive_summary": "Write an executive summary with a brief overview and key takeaways.",
        }.get(style, "Write in clear paragraphs.")

        extra_requirements = self._get_core_requirements(
            tone=tone,
            style_instruction=style_instruction,
            length_instruction=self._get_length_instruction(requested_length, min_length, max_length),
        )

        if include_key_points:
            extra_requirements.append("Make sure the most important points are explicitly stated.")
        if include_quotes:
            extra_requirements.append("Include at most one brief direct quote only if it is essential.")
        if focus_keywords:
            extra_requirements.append(
                "Give extra attention to these topics: " + ", ".join(str(k) for k in focus_keywords[:8])
            )

        requirements_text = "\n".join(f"- {item}" for item in extra_requirements)
        return (
            "You are an AI that creates accurate, meaningful, high-quality summaries.\n"
            "Read the source carefully, preserve the real meaning, and prioritize specificity over generic wording.\n"
            "Your summary must be a true summary, not a copy, paraphrase-free excerpt, or lightly trimmed version of the source.\n\n"
            "Task:\n"
            "Summarize the following text in a clear, faithful way.\n\n"
            f"Rules:\n{requirements_text}\n\n"
            f"TEXT:\n{text}"
        )

    def _get_length_instruction(self, requested_length: str, min_length: int, max_length: int) -> str:
        mapping = {
            "very short": "Keep the summary to 60 to 90 words in one compact paragraph.",
            "short": "Keep the summary concise, about 80 to 120 words, in one clear paragraph, and no more than 5 to 6 lines.",
            "medium": "Keep the summary around 140 to 220 words with enough detail to explain the main ideas clearly.",
            "long": "Write a detailed summary of about 220 to 360 words that covers the full main flow, key ideas, and important outcomes.",
            "detailed": "Write a comprehensive summary of about 320 to 520 words that captures all major ideas, developments, and conclusions.",
        }
        return mapping.get(
            requested_length,
            f"Keep the summary between about {min_length} and {max_length} words."
        )

    def _get_core_requirements(self, tone: str, style_instruction: str, length_instruction: str) -> List[str]:
        return [
            length_instruction,
            "Focus only on the main ideas, key events, and most important outcomes.",
            "Remove unnecessary details, long descriptions, examples, repetition, and dialogue unless essential.",
            "Do not copy sentences from the source; rewrite everything in fresh, natural language.",
            "Do not quote or reproduce long phrases from the source unless explicitly asked.",
            "Blend related ideas together instead of listing every detail from the source in order.",
            "Use simple, clear, easy-to-understand language.",
            "Keep the summary factually accurate and faithful to the source.",
            "Do not add information that is not present in the text.",
            "Keep the flow logical from beginning to end.",
            f"Use a {tone} tone.",
            style_instruction,
        ]

    def _build_refinement_prompt(
        self,
        summary_text: str,
        min_length: int,
        max_length: int,
        summary_options: Dict,
    ) -> str:
        tone = summary_options.get("tone", "neutral").replace("_", " ")
        style = summary_options.get("style", "paragraph").replace("_", " ")
        requested_length = summary_options.get("length", "medium")

        style_instruction = {
            "paragraph": "Keep the result as a clean paragraph summary.",
            "bullet points": "Keep the result as concise bullet points.",
            "bullet_points": "Keep the result as concise bullet points.",
            "executive summary": "Keep the result as an executive summary with a brief overview and key takeaways.",
            "executive_summary": "Keep the result as an executive summary with a brief overview and key takeaways.",
        }.get(style, "Keep the result in clear paragraphs.")

        return (
            "Act as an expert academic editor. Rewrite the given summary to improve clarity, coherence, "
            "readability, and factual precision while preserving the original meaning.\n\n"
            "Requirements:\n"
            "- Eliminate redundancy and repeated phrases.\n"
            "- Use precise and natural English.\n"
            "- Ensure smooth transitions between sentences.\n"
            f"- Follow this requested length: {self._get_length_instruction(requested_length, min_length, max_length)}\n"
            f"- Use a {tone} tone.\n"
            f"- {style_instruction}\n"
            "- Keep the summary faithful to the source information already present.\n"
            "- Return only the improved summary.\n\n"
            f"SUMMARY TO IMPROVE:\n{summary_text}"
        )

    def _normalize_model_output(
        self,
        text: str,
        min_length: int,
        max_length: int,
        summary_options: Dict,
    ) -> str:
        clean = re.sub(r"\n{3,}", "\n\n", (text or "").strip())
        clean = re.sub(r"[ \t]+", " ", clean)
        if not clean:
            return ""

        words = clean.split()
        if len(words) > max_length + max(20, max_length // 8):
            clean = self._truncate_to_word_limit(clean, max_length)

        min_acceptable = max(25, int(min_length * 0.55))
        if len(clean.split()) < min_acceptable:
            return ""

        return clean.strip()

    def _looks_too_extractive(self, summary_text: str, source_text: str) -> bool:
        summary_sentences = self._split_sentences(summary_text)
        if not summary_sentences:
            return False

        normalized_source = self._normalize_for_overlap(source_text)
        copied_sentences = 0
        long_sentence_count = 0

        for sentence in summary_sentences:
            normalized_sentence = self._normalize_for_overlap(sentence)
            if len(normalized_sentence.split()) < 10:
                continue
            long_sentence_count += 1
            if normalized_sentence and normalized_sentence in normalized_source:
                copied_sentences += 1

        if long_sentence_count == 0:
            return False

        return copied_sentences / long_sentence_count >= 0.45

    def _normalize_for_overlap(self, text: str) -> str:
        return re.sub(r"\s+", " ", re.sub(r"[^a-z0-9 ]+", " ", (text or "").lower())).strip()

    def fast_summarize_chunk(self, text: str, min_length: int = 60, max_length: int = 150) -> str:
        return self.summarize_chunk(text, min_length=min_length, max_length=max_length)

    def refine_summary(
        self,
        summary_text: str,
        min_length: int = 60,
        max_length: int = 150,
        summary_options=None,
    ) -> str:
        clean_summary = re.sub(r"\s+", " ", (summary_text or "")).strip()
        if not clean_summary:
            return ""

        options = summary_options or {}

        if self.using_gemini and self.model is not None:
            try:
                prompt = self._build_refinement_prompt(
                    clean_summary,
                    min_length=min_length,
                    max_length=max_length,
                    summary_options=options,
                )
                refined_text = self._generate_with_model(prompt)
                if not self._looks_too_extractive(refined_text, clean_summary):
                    polished = self._normalize_model_output(
                        refined_text,
                        min_length=min_length,
                        max_length=max_length,
                        summary_options=options,
                    )
                    if polished:
                        return polished
            except Exception:
                pass

        fallback = self._cleanup_summary_text(clean_summary)
        return self._trim_summary(
            fallback or clean_summary,
            min_length=min_length,
            max_length=max_length,
        )

    def _generate_with_model(self, prompt: str) -> str:
        if not self.model:
            return ""

        if self.gemini_backend == "google_genai":
            response = self.model.models.generate_content(
                model=self.MODEL_NAME,
                contents=prompt,
            )
            return getattr(response, "text", "") or ""

        response = self.model.generate_content(prompt)
        return getattr(response, "text", "") or ""

    def extractive_fallback(
        self,
        text: str,
        min_length: int = 60,
        max_length: int = 150,
        summary_options=None,
    ) -> str:
        sentences = self._split_sentences(text)
        if not sentences:
            words = text.split()
            summary = " ".join(words[: min(len(words), max_length)]).strip()
            if summary and summary[-1] not in ".!?":
                summary += "."
            return summary

        ranked_sentences = self._rank_sentences(sentences, summary_options or {})
        target_sentence_count = self._target_sentence_count(min_length, max_length, len(sentences))
        selected_indices = sorted(idx for idx, _ in ranked_sentences[:target_sentence_count])
        selected = [sentences[idx] for idx in selected_indices]

        if not selected:
            selected = sentences[: min(3, len(sentences))]

        rewritten = self._rewrite_selected_content(selected, summary_options or {})
        summary = self._trim_summary(rewritten, min_length=min_length, max_length=max_length)
        if len(summary.split()) < max(30, int(min_length * 0.55)):
            summary = self._trim_summary(" ".join(selected), min_length=min_length, max_length=max_length)
        return self._apply_style(summary, summary_options or {})

    def _split_sentences(self, text: str) -> List[str]:
        raw_sentences = re.split(r"(?<=[.!?])\s+|\n+", text)
        sentences = []
        for sentence in raw_sentences:
            clean = re.sub(r"\s+", " ", sentence).strip(" -\t\r\n")
            if len(clean.split()) >= 6:
                sentences.append(clean)
        return sentences

    def _rank_sentences(self, sentences: List[str], summary_options: Dict) -> List[tuple]:
        tokenized = [re.findall(r"[a-zA-Z']+", sentence.lower()) for sentence in sentences]
        frequencies = Counter(
            token
            for tokens in tokenized
            for token in tokens
            if token not in self.STOPWORDS and len(token) > 2
        )
        max_freq = max(frequencies.values(), default=1)

        focus_keywords = {
            keyword.lower().strip()
            for keyword in summary_options.get("focus_keywords", [])
            if str(keyword).strip()
        }

        scored = []
        total_sentences = max(1, len(sentences))
        for idx, sentence in enumerate(sentences):
            tokens = tokenized[idx]
            if not tokens:
                continue

            keyword_score = sum(frequencies.get(token, 0) / max_freq for token in tokens)
            focus_score = sum(1.5 for token in tokens if token in focus_keywords)
            length = len(tokens)
            length_penalty = 0.0 if 8 <= length <= 32 else 0.4
            position_bonus = 0.0
            if idx == 0:
                position_bonus += 1.1
            elif idx < math.ceil(total_sentences * 0.2):
                position_bonus += 0.6
            if idx >= math.floor(total_sentences * 0.8):
                position_bonus += 0.25

            score = keyword_score + focus_score + position_bonus - length_penalty
            scored.append((idx, score))

        scored.sort(key=lambda item: item[1], reverse=True)
        return scored

    def _target_sentence_count(self, min_length: int, max_length: int, available: int) -> int:
        target_words = max(min_length, min(max_length, (min_length + max_length) // 2))
        approx_sentences = max(2, round(target_words / 22))
        return max(1, min(available, approx_sentences))

    def _trim_summary(self, text: str, min_length: int, max_length: int) -> str:
        sentences = self._split_sentences(text)
        if not sentences:
            return text.strip()

        summary = " ".join(sentences)
        while len(summary.split()) > max_length and len(sentences) > 1:
            sentences.pop()
            summary = " ".join(sentences)

        if len(summary.split()) < min_length * 0.6 and len(sentences) < len(self._split_sentences(text)):
            summary = text.strip()

        if len(summary.split()) > max_length:
            summary = self._truncate_to_word_limit(summary, max_length)

        if summary and summary[-1] not in ".!?":
            summary += "."
        return summary

    def _rewrite_selected_content(self, sentences: List[str], summary_options: Dict) -> str:
        points = []
        seen_keys = set()
        for sentence in sentences:
            point = self._compress_sentence(sentence)
            key = self._fingerprint_text(point)
            if point and key not in seen_keys:
                seen_keys.add(key)
                points.append(point)

        if not points:
            points = [self._compress_sentence(sentence) for sentence in sentences[:3] if sentence.strip()]

        tone = (summary_options or {}).get("tone", "neutral")
        style = (summary_options or {}).get("style", "paragraph")
        transitions = self._tone_transitions(tone)

        if style == "bullet_points":
            bullet_points = []
            for idx, point in enumerate(points[:6]):
                prefix = "Highlights" if idx == 0 else "Also notes"
                bullet_points.append(f"- {self._ensure_sentence(self._lead_point(point, prefix.lower(), include_connector=True))}")
            return "\n".join(bullet_points)

        if style == "executive_summary":
            overview = self._ensure_sentence(self._combine_points(points[:2], tone))
            detail_points = [f"- {self._ensure_sentence(point)}" for point in points[2:6]]
            lines = ["Overview", overview]
            if detail_points:
                lines.extend(["", "Key Takeaways", *detail_points])
            return "\n".join(lines)

        sentences_out = []
        for idx, point in enumerate(points[:5]):
            if idx == 0:
                sentence = self._ensure_sentence(self._lead_point(point, transitions["lead"]))
            else:
                sentence = self._ensure_sentence(self._lead_point(point, transitions["follow"]))
            sentences_out.append(sentence)
        return " ".join(sentences_out)

    def _compress_sentence(self, sentence: str) -> str:
        clean = re.sub(r"\([^)]*\)", "", sentence)
        clean = re.sub(r"[\"'`]", "", clean)
        clean = re.sub(r"\s+", " ", clean).strip(" -\t\r\n")
        clean = re.split(r"\s*[;:]\s*", clean)[0]
        clean = re.split(r"\s+(?:however|moreover|meanwhile|therefore|instead)\s+", clean, maxsplit=1, flags=re.IGNORECASE)[0]
        clean = re.sub(
            r"^(?:this chapter|this section|the author|the text|the passage|the book)\s+(?:explains|describes|shows|argues|states|discusses|focuses on)\s+that\s+",
            "",
            clean,
            flags=re.IGNORECASE,
        )

        words = clean.split()
        if len(words) > 24:
            clean = " ".join(words[:24]).strip()
        return clean.strip(" ,")

    def _combine_points(self, points: List[str], tone: str) -> str:
        usable = [point for point in points if point]
        if not usable:
            return ""
        if len(usable) == 1:
            return self._lead_point(usable[0], self._tone_transitions(tone)["lead"])
        first = usable[0].rstrip(".!?")
        second = usable[1].rstrip(".!?")
        second = second[0].lower() + second[1:] if len(second) > 1 else second.lower()
        return f"{first}, while it also highlights {second}"

    def _lead_point(self, point: str, lead_in: str, include_connector: bool = True) -> str:
        clean = point.strip()
        if not clean:
            return ""
        if include_connector:
            clean = clean[0].lower() + clean[1:] if len(clean) > 1 else clean.lower()
            return f"{lead_in} {clean}"
        return clean

    def _tone_transitions(self, tone: str) -> Dict[str, str]:
        tone_key = (tone or "neutral").replace("_", " ").lower()
        if tone_key == "academic":
            return {"lead": "The text explains that", "follow": "It further notes that"}
        if tone_key == "professional":
            return {"lead": "The summary shows that", "follow": "It also emphasizes that"}
        if tone_key == "casual":
            return {"lead": "The text says that", "follow": "It also points out that"}
        return {"lead": "The text explains that", "follow": "It also highlights that"}

    def _ensure_sentence(self, text: str) -> str:
        clean = (text or "").strip()
        if not clean:
            return ""
        if clean[-1] not in ".!?":
            clean += "."
        return clean

    def _fingerprint_text(self, text: str) -> str:
        tokens = [
            token for token in re.findall(r"[a-zA-Z']+", (text or "").lower())
            if token not in self.STOPWORDS and len(token) > 2
        ]
        return " ".join(tokens[:8])

    def _cleanup_summary_text(self, text: str) -> str:
        cleaned = (text or "").strip()
        if not cleaned:
            return ""

        patterns = [
            (r"\b(It further notes that)\s+\1\b", r"\1"),
            (r"\b(It also highlights that)\s+\1\b", r"\1"),
            (r"\b(It also emphasizes that)\s+\1\b", r"\1"),
            (r"\bhowever,\s+responsible\b", "responsible"),
        ]
        for pattern, replacement in patterns:
            cleaned = re.sub(pattern, replacement, cleaned, flags=re.IGNORECASE)

        cleaned = re.sub(r"\s+", " ", cleaned).strip()
        return cleaned

    def _truncate_to_word_limit(self, text: str, max_words: int) -> str:
        words = text.split()
        trimmed = " ".join(words[:max_words]).strip()
        trimmed = re.sub(r"\s+[^\w\s]*$", "", trimmed).strip()
        if trimmed and trimmed[-1] not in ".!?":
            trimmed += "."
        return trimmed

    def _apply_style(self, text: str, summary_options: Dict) -> str:
        style = (summary_options or {}).get("style", "paragraph")
        if style == "bullet_points":
            sentences = self._split_sentences(text)
            return "\n".join(f"- {sentence.rstrip('.!?')}." for sentence in sentences[:8])
        if style == "executive_summary":
            sentences = self._split_sentences(text)
            if not sentences:
                return text
            overview = sentences[0]
            key_points = sentences[1:5]
            lines = ["Overview", overview]
            if key_points:
                lines.append("")
                lines.append("Key Takeaways")
                lines.extend(f"- {sentence.rstrip('.!?')}." for sentence in key_points)
            return "\n".join(lines)
        return text.strip()

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
