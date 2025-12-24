# backend/text_extractor.py

import os
import pdfplumber
import docx
from utils.database import update_book_text, update_book_status
from bson import ObjectId


def extract_text_from_txt(file_path):
    try:
        # Try UTF-8 first
        with open(file_path, "r", encoding="utf-8") as f:
            text = f.read()
            return {"success": True, "text": text}

    except UnicodeDecodeError:
        # Fallback encodings
        try:
            with open(file_path, "r", encoding="latin-1") as f:
                text = f.read()
                return {"success": True, "text": text}
        except:
            return {"success": False, "error": "Unable to read TXT file."}


def extract_text_from_pdf(file_path):
    try:
        text_output = []

        with pdfplumber.open(file_path) as pdf:
            for page in pdf.pages:
                extracted = page.extract_text()
                if extracted:
                    text_output.append(extracted)

        full_text = "\n".join(text_output)

        if not full_text.strip():
            return {"success": False, "error": "PDF contains no extractable text."}

        return {"success": True, "text": full_text}

    except Exception as e:
        return {"success": False, "error": f"PDF extraction failed: {str(e)}"}


def extract_text_from_docx(file_path):
    try:
        document = docx.Document(file_path)
        lines = []

        for para in document.paragraphs:
            if para.text.strip():
                lines.append(para.text)

        full_text = "\n".join(lines)

        if not full_text.strip():
            return {"success": False, "error": "Empty or invalid DOCX file."}

        return {"success": True, "text": full_text}

    except Exception as e:
        return {"success": False, "error": f"DOCX extraction failed: {str(e)}"}

def extract_text(file_path):
    ext = file_path.split(".")[-1].lower()

    if ext == "txt":
        return extract_text_from_txt(file_path)
    elif ext == "pdf":
        return extract_text_from_pdf(file_path)
    elif ext == "docx":
        return extract_text_from_docx(file_path)
    else:
        return {"success": False, "error": "Unsupported file type."}


def process_book(book_id, file_path):
    """
    Runs full extraction pipeline:
    1. Detect file type
    2. Extract text
    3. Count words + characters
    4. Save text into database
    """

    extraction = extract_text(file_path)

    if not extraction["success"]:
        update_book_status(book_id, "extraction_failed")
        return {"success": False, "error": extraction["error"]}

    text = extraction["text"]

    # Word & character count
    words = text.split()
    word_count = len(words)
    char_count = len(text)

    # Save extracted text into DB
    update_book_text(
        book_id=book_id,
        raw_text=text,
        word_count=word_count,
        char_count=char_count,
        status="text_extracted"
    )

    return {
        "success": True,
        "extraction": {
            "text": text,
            "word_count": word_count,
            "char_count": char_count
        }
    }
