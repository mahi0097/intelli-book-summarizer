# backend/summarizer.py

from utils.database import db
from bson import ObjectId

def generate_summary(book_id):
    """
    Generate a simple summary from extracted text.
    Later you can replace this with OpenAI/HuggingFace.
    """

    # Fetch book from DB
    book = db.books.find_one({"_id": ObjectId(book_id)})

    if not book:
        return "No book found."

    text = book.get("raw_text", "")

    if not text or len(text.strip()) == 0:
        return "No text available for summarization."

    # -------------------------------
    # SIMPLE PLACEHOLDER SUMMARY
    # -------------------------------
    extracted_words = text.split()
    first_120_words = " ".join(extracted_words[:120])

    summary = (
        "### ✨ Auto-Generated Summary\n\n"
        + first_120_words
        + "\n\n*(This is a placeholder summary. Replace with an AI model later.)*"
    )

    return summary
