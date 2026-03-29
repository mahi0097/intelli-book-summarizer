import re


def split_sentences(text: str):
    if not text:
        return []
    return [
        sentence.strip()
        for sentence in re.split(r"(?<=[.!?])\s+|\n+", text)
        if len(sentence.strip()) > 3
    ]


def convert_to_bullets(text: str) -> str:
    """Convert summary text into readable bullet points."""
    sentences = split_sentences(text)
    if not sentences:
        return ""

    bullets = []
    for sentence in sentences:
        clean = sentence.strip().lstrip("-*• ").strip()
        if clean and clean[-1] not in ".!?":
            clean += "."
        bullets.append(f"- {clean}")
    return "\n".join(bullets)


def convert_to_executive_summary(text: str) -> str:
    """Format summary text into a lightweight executive-summary layout."""
    sentences = split_sentences(text)
    if not sentences:
        return ""

    overview = sentences[0]
    takeaways = sentences[1:5]

    lines = ["Overview", overview]
    if takeaways:
        lines.append("")
        lines.append("Key Takeaways")
        lines.extend(
            f"- {sentence if sentence[-1] in '.!?' else sentence + '.'}"
            for sentence in takeaways
        )
    return "\n".join(lines)
