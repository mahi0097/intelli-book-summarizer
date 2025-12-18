# utils/database.py

import os
import re
import bcrypt
from bson import ObjectId
from pymongo import MongoClient, ASCENDING
from datetime import datetime
from dotenv import load_dotenv

# Load .env values
load_dotenv()

MONGO_URI = os.getenv("MONGODB_URI")
DB_NAME = os.getenv("DB_NAME")

client = MongoClient(MONGO_URI)
db = client[DB_NAME]


# --------------------------------------------------------
# Utility: Return DB ref
# --------------------------------------------------------
def connect_db():
    return db


# --------------------------------------------------------
# Validators
# --------------------------------------------------------
def is_valid_email(email):
    return bool(re.match(r"[^@]+@[^@]+\.[^@]+", email))


# --------------------------------------------------------
# Create User
# --------------------------------------------------------
def create_user(name, email, password, role="user"):
    if not is_valid_email(email):
        raise ValueError("Invalid email format")

    password_hash = bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()

    user = {
        "name": name,
        "email": email.lower(),
        "password_hash": password_hash,
        "role": role,
        "created_at": datetime.utcnow()
    }

    result = db.users.insert_one(user)
    return str(result.inserted_id)


# --------------------------------------------------------
# Get User by Email
# --------------------------------------------------------
def get_user_by_email(email):
    return db.users.find_one({"email": email.lower()})


# --------------------------------------------------------
# Create Book
# --------------------------------------------------------
def create_book(user_id, title, file_path, author="", chapter="", raw_text=""):
    """Stores uploaded book metadata. raw_text will be updated after extraction."""
    
    book = {
        "user_id": ObjectId(user_id),
        "title": title,
        "author": author,
        "chapter": chapter,
        "file_path": file_path,
        "raw_text": raw_text,
        "word_count": 0,
        "char_count": 0,
        "uploaded_at": datetime.utcnow(),
        "status": "uploaded"  # uploaded → extracting → text_extracted → summarizing → completed
    }

    result = db.books.insert_one(book)
    return str(result.inserted_id)


# --------------------------------------------------------
# Update Book Status
# --------------------------------------------------------
def update_book_status(book_id, status):
    """Update book workflow status."""
    db.books.update_one(
        {"_id": ObjectId(book_id)},
        {"$set": {"status": status}}
    )


# --------------------------------------------------------
# Update Extracted Text + Metadata
# --------------------------------------------------------
def update_book_text(book_id, raw_text, word_count, char_count, status="text_extracted"):
    """Stores extracted text + word count + char count."""

    db.books.update_one(
        {"_id": ObjectId(book_id)},
        {
            "$set": {
                "raw_text": raw_text,
                "word_count": word_count,
                "char_count": char_count,
                "status": status,
                "text_extracted_at": datetime.utcnow()
            }
        }
    )


# --------------------------------------------------------
# Create Summary Record
# --------------------------------------------------------
def create_summary(book_id, user_id, summary_text, summary_length, summary_style,
                   chunk_summaries, processing_time):

    summary = {
        "book_id": ObjectId(book_id),
        "user_id": ObjectId(user_id),
        "summary_text": summary_text,
        "summary_length": summary_length,     # short / medium / long
        "summary_style": summary_style,       # paragraphs / bullets
        "chunk_summaries": chunk_summaries,   # JSON array
        "processing_time": float(processing_time),
        "created_at": datetime.utcnow()
    }

    result = db.summaries.insert_one(summary)
    return str(result.inserted_id)


# --------------------------------------------------------
# Fetch Summaries
# --------------------------------------------------------
def get_summaries_by_user(user_id):
    return list(
        db.summaries.find({"user_id": ObjectId(user_id)})
        .sort("created_at", -1)
    )

def delete_book(book_id):
    """Delete book and its summaries from the database."""
    try:
        # Delete the book
        db.books.delete_one({"_id": ObjectId(book_id)})

        # Delete all summaries linked to this book
        db.summaries.delete_many({"book_id": ObjectId(book_id)})

        return True
    except Exception as e:
        print("Error deleting book:", e)
        return False



# --------------------------------------------------------
# Create Database Indexes
# --------------------------------------------------------
def create_indexes():
    db.users.create_index([("email", ASCENDING)], unique=True)
    db.books.create_index([("user_id", ASCENDING)])
    db.books.create_index([("title", ASCENDING)])
    db.summaries.create_index([("book_id", ASCENDING)])
    db.summaries.create_index([("user_id", ASCENDING)])
