# tests/test_summary_orchestrator.py
import pytest
from backend.summary_orchestrator import summarize_with_retry

class DummySummarizer:
    def summarize_chunk(self, text, min_length=50, max_length=150):
        return "This is a test summary."

def test_summarize_with_valid_text():
    summarizer = DummySummarizer()
    result = summarize_with_retry(
        summarizer,
        "This is a long enough text for testing summarization.",
        {"min_length": 30, "max_length": 100}
    )
    assert result is not None

def test_summarize_with_short_text():
    summarizer = DummySummarizer()
    result = summarize_with_retry(
        summarizer,
        "Too short",
        {"min_length": 30, "max_length": 100}
    )
    assert result is None
