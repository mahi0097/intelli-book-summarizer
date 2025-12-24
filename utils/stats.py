def calculate_summary_stats(summary_text: str, original_text: str) -> dict:
    """
    Calculate statistics for summary quality.
    """

    if not summary_text or not original_text:
        return {
            "original_word_count": 0,
            "summary_word_count": 0,
            "compression_ratio": 0,
        }

    original_words = len(original_text.split())
    summary_words = len(summary_text.split())

    compression_ratio = round(summary_words / original_words, 3) if original_words else 0

    return {
        "original_word_count": original_words,
        "summary_word_count": summary_words,
        "compression_ratio": compression_ratio,
    }
