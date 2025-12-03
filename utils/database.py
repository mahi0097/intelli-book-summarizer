# utils/database.py

import os
import re
import bcrypt
from bson import ObjectId
from pymongo import MongoClient, ASCENDING
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

# Load MongoDB config
MONGO_URI = os.getenv("MONGODB_URI")
DB_NAME = os.getenv("DB_NAME")

client = MongoClient(MONGO_URI)
db = client[DB_NAME]



def connect_db():
    return db



def is_valid_email(email):
    return bool(re.match(r"[^@]+@[^@]+\.[^@]+", email))


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


def get_user_by_email(email):
    return db.users.find_one({"email": email.lower()})



def create_book(user_id, title, file_path, author="", chapter="", raw_text=""):
    book = {
        "user_id": ObjectId(user_id),
        "title": title,
        "author": author,
        "chapter": chapter,
        "file_path": file_path,
        "raw_text": raw_text,
        "uploaded_at": datetime.utcnow(),
        "status": "uploaded"
    }

    result = db.books.insert_one(book)
    return str(result.inserted_id)


def update_book_status(book_id, status):
    db.books.update_one(
        {"_id": ObjectId(book_id)},
        {"$set": {"status": status}}
    )

def create_summary(book_id, user_id, summary_text, summary_length, summary_style,
                   chunk_summaries, processing_time):

    summary = {
        "book_id": ObjectId(book_id),
        "user_id": ObjectId(user_id),
        "summary_text": summary_text,
        "summary_length": summary_length,
        "summary_style": summary_style,
        "chunk_summaries": chunk_summaries,
        "processing_time": float(processing_time),
        "created_at": datetime.utcnow()
    }

    result = db.summaries.insert_one(summary)
    return str(result.inserted_id)


def get_summaries_by_user(user_id):
    return list(
        db.summaries.find({"user_id": ObjectId(user_id)})
        .sort("created_at", -1)
    )



def create_indexes():
    db.users.create_index([("email", ASCENDING)], unique=True)
    db.books.create_index([("user_id", ASCENDING)])
    db.summaries.create_index([("book_id", ASCENDING)])
    db.summaries.create_index([("user_id", ASCENDING)])

def validate_registration(name,email,password,confirm_password):
    errors  = []

    if not name or len(name) < 2:
        errors.append("name must be at least 2 char")
    if not re.match(r"^[A-Za-z ]+$",name):
        errors.append("name must contain only letters and spaces")
    #Email validation
    if not re.match(r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$", email):
        errors.append("Invalid email format.")

    #password validation
    if len(password) < 0:
        errors.append("password must be at least 8 char long")
    if not re.search(r"[A-Z]",password):
        errors.append("password must contain at east 2 uppercase letter")
    if not re.search(r"[a-z]",password):
        errors.append("password must contain at least 1 lowercase letter")
    if not re.search(r"[0-9]",password):
        errors.append("password must contain 1 at least number")
    if not re.search(r"[!@#$%^&*(),.?\":{}|<>]",password):
        errors.append("password must contain at lest 1 special char")

    #confirm password
    if password != confirm_password:
        errors.append("password do not match.")
    return errors                            
    
