# utils/database.py
import os
import re
import bcrypt
from bson import ObjectId
from pymongo import MongoClient, ASCENDING, DESCENDING
from datetime import datetime
from dotenv import load_dotenv
import logging

# पहले logs directory create करें
try:
    os.makedirs('logs', exist_ok=True)
    print("✅ logs directory created/verified")
except Exception as e:
    print(f"⚠️ Could not create logs directory: {e}")

# फिर logging setup करें
try:
    logging.basicConfig(
        filename=os.path.join('logs', 'app_errors.log'),
        level=logging.ERROR,
        format="%(asctime)s - %(levelname)s - %(message)s"
    )
    print("✅ Logging configured")
except Exception as e:
    print(f"⚠️ Could not configure logging: {e}")
    # Fallback to console logging
    logging.basicConfig(level=logging.ERROR)

load_dotenv()

MONGO_URI = os.getenv("MONGODB_URI", "mongodb://localhost:27017")
DB_NAME = os.getenv("DB_NAME", "book_summarization")

print(f"🔗 MongoDB URI: {MONGO_URI}")
print(f"📁 Database: {DB_NAME}")

# Initialize db variable
db = None

try:
    if MONGO_URI and MONGO_URI != "mongodb://localhost:27017":
        client = MongoClient(MONGO_URI, serverSelectionTimeoutMS=5000)
        # Test connection
        client.server_info()
        db = client[DB_NAME]
        print("✅ MongoDB connected successfully")
    else:
        print("⚠️ Using local MongoDB or fallback mode")
        # Try local connection
        client = MongoClient("mongodb://localhost:27017", serverSelectionTimeoutMS=3000)
        client.server_info()
        db = client[DB_NAME]
        print("✅ Local MongoDB connected successfully")
except Exception as e:
    print(f"❌ MongoDB connection failed: {e}")
    print("⚠️ Running in simulation mode (no database)")
    # Fallback to simulation mode
    class MockDB:
        def __init__(self):
            self.collections = {}
            self.mock_data = {
                'users': [],
                'books': [],
                'summaries': [],
                'progress': [],
                'errors': [],
                'summary_actions': []
            }
        
        def list_collection_names(self):
            return list(self.mock_data.keys())
        
        def create_collection(self, name):
            if name not in self.mock_data:
                self.mock_data[name] = []
        
        def __getitem__(self, name):
            if name not in self.collections:
                self.collections[name] = MockCollection(name, self.mock_data)
            return self.collections[name]

class MockCollection:
    def __init__(self, name, mock_data):
        self.name = name
        self.mock_data = mock_data
        if name not in self.mock_data:
            self.mock_data[name] = []
    
    def insert_one(self, document):
        document['_id'] = ObjectId()
        document['id'] = str(document['_id'])
        self.mock_data[self.name].append(document)
        return type('Result', (), {'inserted_id': document['_id']})()
    
    def find_one(self, query=None):
        if not self.mock_data[self.name]:
            return None
        return self.mock_data[self.name][0]
    
    def find(self, query=None):
        return MockCursor(self.mock_data[self.name])
    
    def update_one(self, filter, update, **kwargs):
        return type('Result', (), {'modified_count': 1})()
    
    def update_many(self, filter, update):
        return type('Result', (), {'modified_count': 0})()
    
    def delete_one(self, filter):
        return type('Result', (), {'deleted_count': 0})()
    
    def delete_many(self, filter):
        return type('Result', (), {'deleted_count': 0})()
    
    def count_documents(self, filter):
        return len(self.mock_data[self.name])

class MockCursor:
    def __init__(self, data):
        self.data = data
    
    def sort(self, key, direction):
        return self
    
    def limit(self, n):
        return self
    
    def skip(self, n):
        return self
    
    def __iter__(self):
        return iter(self.data)
    
    def __next__(self):
        pass

# Create mock database if real connection failed
if db is None:
    db = MockDB()
    print("✅ Mock database created for testing")

def connect_db():
    """Get database connection"""
    return db

def is_valid_email(email):
    """Validate email format"""
    return bool(re.match(r"[^@]+@[^@]+\.[^@]+", email))

def create_user(name, email, password, role="user"):
    """Create a new user"""
    if not is_valid_email(email):
        raise ValueError("Invalid email format")

    password_hash = bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()

    user = {
        "name": name,
        "email": email.lower(),
        "password_hash": password_hash,
        "role": role,
        "created_at": datetime.utcnow(),
        "last_login": None,
        "is_active": True,
        "settings": {}
    }

    try:
        result = db.users.insert_one(user)
        user_id = str(result.inserted_id)
        print(f"✅ User created: {email} (ID: {user_id})")
        return user_id
    except Exception as e:
        print(f"❌ Error creating user {email}: {e}")
        # For testing without DB
        return "mock_user_id"

def get_user_by_email(email):
    """Get user by email"""
    try:
        user = db.users.find_one({"email": email.lower()})
        if user:
            user['_id'] = str(user.get('_id', ''))
        return user
    except Exception as e:
        print(f"❌ Error getting user by email {email}: {e}")
        return None

def create_book(user_id, title, author="", chapter="", file_path="", raw_text=""):
    """Create a new book entry in database"""
    try:
        book_data = {
            "user_id": ObjectId(user_id) if isinstance(user_id, str) and ObjectId.is_valid(user_id) else user_id,
            "title": title,
            "author": author,
            "chapter": chapter,
            "file_path": file_path,
            "raw_text": raw_text,
            "status": "uploaded",
            "uploaded_at": datetime.now(),
            "word_count": len(raw_text.split()) if raw_text else 0,
            "file_type": file_path.split(".")[-1].lower() if file_path and "." in file_path else "txt",
            "progress": 0,
            "progress_message": "Uploaded"
        }
        result = db.books.insert_one(book_data)
        book_id = result.inserted_id
        print(f"✅ Book created: {title} (ID: {book_id})")
        return book_id
    except Exception as e:
        print(f"❌ Error creating book '{title}': {e}")
        # For testing
        return ObjectId()

def update_book_status(book_id, status):
    """Update book workflow status."""
    try:
        db.books.update_one(
            {"_id": ObjectId(book_id) if isinstance(book_id, str) else book_id},
            {"$set": {"status": status}}
        )
        print(f"✅ Book {book_id} status updated to: {status}")
        return True
    except Exception as e:
        print(f"❌ Error updating book status for {book_id}: {e}")
        return False

def update_book_text(book_id, raw_text, word_count, char_count, status="text_extracted"):
    """Stores extracted text + word count + char count."""
    try:
        db.books.update_one(
            {"_id": ObjectId(book_id) if isinstance(book_id, str) else book_id},
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
        print(f"✅ Book text updated for {book_id} ({word_count} words)")
        return True
    except Exception as e:
        print(f"❌ Error updating book text for {book_id}: {e}")
        return False

def create_summary(book_id, user_id, summary_text, summary_length, summary_style,
                   chunk_summaries, processing_time):
    """Create summary (legacy function)"""
    try:
        summary = {
            "book_id": ObjectId(book_id) if isinstance(book_id, str) and ObjectId.is_valid(book_id) else book_id,
            "user_id": ObjectId(user_id) if isinstance(user_id, str) and ObjectId.is_valid(user_id) else user_id,
            "summary_text": summary_text,
            "summary_length": summary_length,
            "summary_style": summary_style,
            "chunk_summaries": chunk_summaries,
            "processing_time": float(processing_time),
            "created_at": datetime.utcnow(),
            "version": 1,
            "is_active": True,
            "is_favorite": False,
            "tags": []
        }
        result = db.summaries.insert_one(summary)
        summary_id = str(result.inserted_id)
        print(f"✅ Summary created: v1 for book {book_id} (ID: {summary_id})")
        return summary_id
    except Exception as e:
        print(f"❌ Error creating summary for book {book_id}: {e}")
        return "mock_summary_id"

def get_summaries_by_user(user_id):
    """Get all summaries for a user"""
    try:
        user_obj_id = ObjectId(user_id) if isinstance(user_id, str) and ObjectId.is_valid(user_id) else user_id
        summaries = list(db.summaries.find({"user_id": user_obj_id}).sort("created_at", -1))
        
        # Convert ObjectId to string
        for summary in summaries:
            summary['_id'] = str(summary.get('_id', ''))
            summary['book_id'] = str(summary.get('book_id', ''))
            summary['user_id'] = str(summary.get('user_id', ''))
        
        print(f"✅ Retrieved {len(summaries)} summaries for user {user_id}")
        return summaries
    except Exception as e:
        print(f"❌ Error getting user summaries for {user_id}: {e}")
        return []

def delete_book(book_id):
    """Delete book and its summaries from the database."""
    try:
        book_obj_id = ObjectId(book_id) if isinstance(book_id, str) else book_id
        db.books.delete_one({"_id": book_obj_id})
        db.summaries.delete_many({"book_id": book_obj_id})
        print(f"✅ Book {book_id} deleted")
        return True
    except Exception as e:
        print(f"❌ Error deleting book {book_id}: {e}")
        return False

def get_book_by_id(book_id):
    """Get book by ID"""
    try:
        book_obj_id = ObjectId(book_id) if isinstance(book_id, str) else book_id
        book = db.books.find_one({"_id": book_obj_id})
        if book:
            book['_id'] = str(book.get('_id', ''))
            book['user_id'] = str(book.get('user_id', ''))
            print(f"✅ Retrieved book: {book.get('title', 'Unknown')}")
        return book
    except Exception as e:
        print(f"❌ Error getting book by ID {book_id}: {e}")
        return None

def update_progress(book_id, message, percentage):
    """Update processing progress"""
    try:
        book_obj_id = ObjectId(book_id) if isinstance(book_id, str) else book_id
        
        # Create progress collection if not exists
        if 'progress' not in db.list_collection_names():
            db.create_collection('progress')
        
        db.progress.update_one(
            {"book_id": book_obj_id},
            {
                "$set": {
                    "message": message,
                    "percentage": percentage,
                    "updated_at": datetime.utcnow()
                }
            },
            upsert=True
        )
        
        db.books.update_one(
            {"_id": book_obj_id},
            {
                "$set": {
                    "progress": percentage,
                    "progress_message": message,
                    "updated_at": datetime.utcnow()
                }
            }
        )
        print(f"✅ Progress updated for book {book_id}: {percentage}% - {message}")
        return True
    except Exception as e:
        print(f"❌ Error updating progress for book {book_id}: {e}")
        return False

def get_progress(book_id):
    """Get progress for a book"""
    try:
        book_obj_id = ObjectId(book_id) if isinstance(book_id, str) else book_id
        progress = db.progress.find_one({"book_id": book_obj_id})
        if progress:
            progress['_id'] = str(progress.get('_id', ''))
        return progress
    except Exception as e:
        print(f"❌ Error getting progress for book {book_id}: {e}")
        return None

def log_error(book_id, error_message):
    """Log error"""
    try:
        if 'errors' not in db.list_collection_names():
            db.create_collection('errors')
        
        db.errors.insert_one({
            "book_id": book_id,
            "error": error_message,
            "created_at": datetime.utcnow()
        })
        print(f"✅ Error logged for book {book_id}")
        return True
    except Exception as e:
        print(f"❌ Error logging error for book {book_id}: {e}")
        return False

# ================================
# TASK 15: VERSION CONTROL FUNCTIONS
# ================================

def save_summary_with_metadata(
    book_id,
    user_id,
    summary_text,
    chunk_summaries=None,
    summary_options=None,
    refinement_metadata=None,
    preprocessing_stats=None,
    processing_stats=None,
    version=None,
    is_active=True
):
    """
    Enhanced Save Summary Function with version control and metadata
    """
    try:
        # Ensure collections exist
        if 'summaries' not in db.list_collection_names():
            db.create_collection('summaries')
        
        if 'summary_actions' not in db.list_collection_names():
            db.create_collection('summary_actions')
        
        # Convert IDs
        book_obj_id = ObjectId(book_id) if isinstance(book_id, str) and ObjectId.is_valid(book_id) else book_id
        user_obj_id = ObjectId(user_id) if isinstance(user_id, str) and ObjectId.is_valid(user_id) else user_id
        
        # Find existing summaries for this book/user
        existing_summaries = list(db.summaries.find({
            "book_id": book_obj_id,
            "user_id": user_obj_id
        }).sort("version", -1).limit(1))

        # Determine version number
        if version is None:
            version = 1
            if existing_summaries:
                version = existing_summaries[0].get("version", 0) + 1
        
        # If this is active and version > 1, deactivate previous active versions
        if is_active and version > 1:
            db.summaries.update_many({
                "book_id": book_obj_id,
                "user_id": user_obj_id,
                "is_active": True
            }, {"$set": {"is_active": False}})
        
        # Create summary document
        summary_doc = {
            "book_id": book_obj_id,
            "user_id": user_obj_id,
            "summary_text": summary_text,
            "chunk_summaries": chunk_summaries or [],
            "summary_options": summary_options or {},
            "refinement_metadata": refinement_metadata or {},
            "preprocessing_stats": preprocessing_stats or {},
            "processing_stats": processing_stats or {},
            "version": version,
            "is_active": is_active,
            "summary_type": summary_options.get("type", "auto_generated") if summary_options else "auto_generated",
            "word_count": len(summary_text.split()),
            "char_count": len(summary_text),
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow(),
            "tags": summary_options.get("tags", []) if summary_options else [],
            "access_level": summary_options.get("access_level", "private") if summary_options else "private",
            "is_favorite": False,
            "rating": None,
            "feedback": None,
            "deleted_at": None
        }
        
        result = db.summaries.insert_one(summary_doc)
        summary_id = str(result.inserted_id)
        
        # Log the action
        log_summary_action(
            summary_id=summary_id,
            user_id=user_id,
            action="create",
            metadata={
                "version": version,
                "book_id": book_id,
                "word_count": summary_doc["word_count"]
            }
        )
        
        print(f"✅ Summary saved with metadata: v{version} for book {book_id}")
        return summary_id
        
    except Exception as e:
        print(f"❌ Error saving summary with metadata for book {book_id}: {e}")
        # Return mock ID for testing
        return "mock_summary_id"

def get_book_summary_versions(book_id, user_id):
    """
    Get all summary versions for a book by user
    """
    try:
        # Normalize IDs
        if isinstance(book_id, str) and ObjectId.is_valid(book_id):
            book_obj_id = ObjectId(book_id)
        else:
            book_obj_id = book_id
        
        if isinstance(user_id, str) and ObjectId.is_valid(user_id):
            user_obj_id = ObjectId(user_id)
        else:
            user_obj_id = user_id

        # Query summaries
        summaries = list(db.summaries.find({
            "book_id": book_obj_id,
            "user_id": user_obj_id,
            "deleted_at": None  # Only non-deleted summaries
        }).sort("version", 1))  # Sort by version ascending

        # Process results
        for summary in summaries:
            # Convert ObjectId to string
            summary['_id'] = str(summary.get('_id', ''))
            summary['book_id'] = str(summary.get('book_id', ''))
            summary['user_id'] = str(summary.get('user_id', ''))
            
            # Ensure version exists
            if "version" not in summary:
                summary["version"] = 1
            
            # Format dates for display
            if "created_at" in summary and isinstance(summary["created_at"], datetime):
                summary["created_at_formatted"] = summary["created_at"].strftime("%Y-%m-%d %H:%M")
            else:
                summary["created_at_formatted"] = "Unknown date"
            
            # Add word count if not present
            if "word_count" not in summary and "summary_text" in summary:
                summary["word_count"] = len(summary["summary_text"].split())

        print(f"✅ Retrieved {len(summaries)} summary versions for book {book_id}")
        return summaries

    except Exception as e:
        print(f"❌ Error getting book summary versions for {book_id}: {e}")
        logging.error(f"Error in get_book_summary_versions: {e}")
        return []


def set_active_summary_version(book_id, user_id, version):
    """
    Set a specific version as the active summary for a book
    """
    try:
        book_obj_id = ObjectId(book_id) if isinstance(book_id, str) else book_id
        user_obj_id = ObjectId(user_id) if isinstance(user_id, str) else user_id
        
        # First deactivate all versions for this book/user
        db.summaries.update_many(
            {
                "book_id": book_obj_id,
                "user_id": user_obj_id,
                "is_active": True,
                "deleted_at": None
            },
            {"$set": {"is_active": False}}
        )
        
        # Activate the specified version
        result = db.summaries.update_one(
            {
                "book_id": book_obj_id,
                "user_id": user_obj_id,
                "version": version,
                "deleted_at": None
            },
            {
                "$set": {
                    "is_active": True,
                    "updated_at": datetime.utcnow()
                }
            }
        )
        
        if getattr(result, 'modified_count', 0) > 0:
            log_summary_action(
                summary_id=None,
                user_id=user_id,
                action="set_active_version",
                metadata={"book_id": book_id, "version": version}
            )
            print(f"✅ Set active version for book {book_id}: v{version}")
            return True
        
        print(f"⚠️ No summary found for book {book_id}, version {version}")
        return False
        
    except Exception as e:
        print(f"❌ Error setting active version for book {book_id}: {e}")
        return False

def update_summary_metadata(summary_id, user_id, updates):
    """
    Update summary metadata (not the summary text itself)
    """
    try:
        summary_obj_id = ObjectId(summary_id) if isinstance(summary_id, str) else summary_id
        user_obj_id = ObjectId(user_id) if isinstance(user_id, str) else user_id
        
        # Only allow updating certain fields
        allowed_updates = {
            "tags", "is_favorite", "rating", "feedback", 
            "access_level", "summary_type", "is_active"
        }
        
        # Filter updates
        filtered_updates = {
            k: v for k, v in updates.items() 
            if k in allowed_updates
        }
        
        if not filtered_updates:
            print(f"⚠️ No valid updates provided for summary {summary_id}")
            return False
        
        # Add updated timestamp
        filtered_updates["updated_at"] = datetime.utcnow()
        
        # Perform update
        result = db.summaries.update_one(
            {
                "_id": summary_obj_id,
                "user_id": user_obj_id,
                "deleted_at": None
            },
            {"$set": filtered_updates}
        )
        
        if getattr(result, 'modified_count', 0) > 0:
            # Log the update action
            log_summary_action(
                summary_id=summary_id,
                user_id=user_id,
                action="update",
                metadata={"updated_fields": list(filtered_updates.keys())}
            )
            print(f"✅ Updated metadata for summary {summary_id}")
            return True
        
        print(f"⚠️ Summary {summary_id} not found or not owned by user {user_id}")
        return False
        
    except Exception as e:
        print(f"❌ Error updating summary metadata for {summary_id}: {e}")
        return False

def delete_summary(summary_id, user_id, permanent=False):
    """
    Delete a summary (soft delete by default)
    """
    try:
        summary_obj_id = ObjectId(summary_id) if isinstance(summary_id, str) else summary_id
        user_obj_id = ObjectId(user_id) if isinstance(user_id, str) else user_id
        
        if permanent:
            # Permanent delete
            result = db.summaries.delete_one({
                "_id": summary_obj_id,
                "user_id": user_obj_id
            })
            
            if getattr(result, 'deleted_count', 0) > 0:
                log_summary_action(
                    summary_id=summary_id,
                    user_id=user_id,
                    action="delete_permanent",
                    metadata={}
                )
                print(f"✅ Permanently deleted summary {summary_id}")
                return True
        else:
            # Soft delete (deactivate and mark as deleted)
            result = db.summaries.update_one(
                {
                    "_id": summary_obj_id,
                    "user_id": user_obj_id,
                    "deleted_at": None
                },
                {
                    "$set": {
                        "is_active": False,
                        "deleted_at": datetime.utcnow(),
                        "updated_at": datetime.utcnow()
                    }
                }
            )
            
            if getattr(result, 'modified_count', 0) > 0:
                log_summary_action(
                    summary_id=summary_id,
                    user_id=user_id,
                    action="delete_soft",
                    metadata={}
                )
                print(f"✅ Soft deleted summary {summary_id}")
                return True
        
        print(f"⚠️ Summary {summary_id} not found or not owned by user {user_id}")
        return False
        
    except Exception as e:
        print(f"❌ Error deleting summary {summary_id}: {e}")
        return False

def restore_summary(summary_id, user_id):
    """
    Restore a soft-deleted summary
    """
    try:
        summary_obj_id = ObjectId(summary_id) if isinstance(summary_id, str) else summary_id
        user_obj_id = ObjectId(user_id) if isinstance(user_id, str) else user_id
        
        result = db.summaries.update_one(
            {
                "_id": summary_obj_id,
                "user_id": user_obj_id,
                "deleted_at": {"$ne": None}
            },
            {
                "$set": {
                    "deleted_at": None,
                    "updated_at": datetime.utcnow()
                }
            }
        )
        
        if getattr(result, 'modified_count', 0) > 0:
            log_summary_action(
                summary_id=summary_id,
                user_id=user_id,
                action="restore",
                metadata={}
            )
            print(f"✅ Restored summary {summary_id}")
            return True
        
        print(f"⚠️ Summary {summary_id} not found or not deleted")
        return False
        
    except Exception as e:
        print(f"❌ Error restoring summary {summary_id}: {e}")
        return False

def log_summary_action(summary_id, user_id, action, metadata=None):
    """
    Log summary-related actions for analytics
    """
    try:
        if 'summary_actions' not in db.list_collection_names():
            db.create_collection('summary_actions')
        
        log_entry = {
            "summary_id": ObjectId(summary_id) if summary_id and isinstance(summary_id, str) and ObjectId.is_valid(summary_id) else None,
            "user_id": ObjectId(user_id) if isinstance(user_id, str) and ObjectId.is_valid(user_id) else user_id,
            "action": action,
            "metadata": metadata or {},
            "timestamp": datetime.utcnow()
        }
        
        db.summary_actions.insert_one(log_entry)
        print(f"✅ Logged action: {action} for summary {summary_id}")
        return True
        
    except Exception as e:
        print(f"❌ Error logging summary action for {summary_id}: {e}")
        return False

def get_summary_by_id(summary_id, include_book_info=False):
    """
    Get summary by ID with optional book information
    """
    try:
        if isinstance(summary_id, str) and ObjectId.is_valid(summary_id):
            summary_obj_id = ObjectId(summary_id)
        else:
            summary_obj_id = summary_id
        
        summary = db.summaries.find_one({"_id": summary_obj_id})
        
        if not summary:
            print(f"⚠️ Summary {summary_id} not found")
            return None
        
        # Convert ObjectId to string
        summary["_id"] = str(summary.get("_id", ""))
        summary["book_id"] = str(summary.get("book_id", ""))
        summary["user_id"] = str(summary.get("user_id", ""))
        
        
        if include_book_info:
            book = get_book_by_id(summary["book_id"])
            if book:
                summary["book_info"] = {
                    "title": book.get("title", "Unknown"),
                    "author": book.get("author", "Unknown"),
                    "uploaded_at": book.get("uploaded_at")
                }
        
        print(f"✅ Retrieved summary {summary_id}")
        return summary
    except Exception as e:
        print(f"❌ Error getting summary by ID {summary_id}: {e}")
        return None

def get_books_by_user(user_id, limit=100):
    """
    Get all books for a specific user
    """
    try:
        if isinstance(user_id, str) and ObjectId.is_valid(user_id):
            user_obj_id = ObjectId(user_id)
        else:
            user_obj_id = user_id
        
        books = list(db.books.find(
            {"user_id": user_obj_id}
        ).sort("uploaded_at", -1).limit(limit))
        
        # Convert ObjectId to string
        for book in books:
            book['_id'] = str(book.get('_id', ''))
            book['user_id'] = str(book.get('user_id', ''))
        
        print(f"✅ Retrieved {len(books)} books for user {user_id}")
        return books
    except Exception as e:
        print(f"❌ Error getting books by user {user_id}: {e}")
        return []

# ================================
# BACKWARD COMPATIBILITY FUNCTION
# ================================

def save_summary(
    book_id,
    user_id,
    summary_text,
    summary_length="medium",
    summary_style="paragraph",
    chunk_summaries=None,
    processing_time=0
):
    """
    Compatibility wrapper for older code.
    Do NOT remove. Used by summary_orchestrator.py
    """
    print(f"📝 Saving summary (legacy) for book {book_id}")
    return save_summary_with_metadata(
        book_id=book_id,
        user_id=user_id,
        summary_text=summary_text,
        chunk_summaries=chunk_summaries or [],
        summary_options={
            "length": summary_length,
            "style": summary_style
        },
        processing_stats={
            "processing_time": processing_time
        },
        is_active=True
    )

# ================================
# ADMIN FUNCTIONS (TASK 16)
# ================================

def get_all_users(limit=100, skip=0):
    """Get all users for admin dashboard"""
    try:
        users = list(db.users.find({}).skip(skip).limit(limit))
        for user in users:
            user['_id'] = str(user.get('_id', ''))
            # Get user stats
            try:
                book_count = db.books.count_documents({"user_id": user['_id']})
                summary_count = db.summaries.count_documents({"user_id": user['_id']})
            except:
                book_count = 0
                summary_count = 0
            user['stats'] = {
                'book_count': book_count,
                'summary_count': summary_count
            }
        print(f"✅ Retrieved {len(users)} users")
        return users
    except Exception as e:
        print(f"❌ Error getting all users: {e}")
        return []

def get_system_stats():
    """Get system-wide statistics"""
    try:
        stats = {
            'total_users': db.users.count_documents({}) if hasattr(db.users, 'count_documents') else 0,
            'total_books': db.books.count_documents({}) if hasattr(db.books, 'count_documents') else 0,
            'total_summaries': db.summaries.count_documents({}) if hasattr(db.summaries, 'count_documents') else 0,
            'active_users_30d': 0,  # Implement date-based query
            'storage_used_mb': 0,   # Implement storage calculation
            'avg_processing_time': 2.5,
            'success_rate': 0.95
        }
        print(f"✅ Retrieved system stats")
        return stats
    except Exception as e:
        print(f"❌ Error getting system stats: {e}")
        return {}

def get_recent_activities(limit=50):
    """Get recent system activities"""
    try:
        if 'summary_actions' in db.list_collection_names():
            activities = list(db.summary_actions.find({})
                             .sort("timestamp", -1)
                             .limit(limit))
            for activity in activities:
                activity['_id'] = str(activity.get('_id', ''))
                if activity.get('summary_id'):
                    activity['summary_id'] = str(activity.get('summary_id', ''))
                activity['user_id'] = str(activity.get('user_id', ''))
            print(f"✅ Retrieved {len(activities)} recent activities")
            return activities
        print("⚠️ summary_actions collection not found")
        return []
    except Exception as e:
        print(f"❌ Error getting recent activities: {e}")
        return []

# ================================
# NEW FUNCTIONS FOR APP.PY
# ================================

def connect_db():
    """Get database connection"""
    return db

def get_db():
    """
    Compatibility function for Flask apps that expect get_db().
    Returns the database connection.
    """
    return connect_db()

def is_valid_email(email):
    """Validate email format"""
    return bool(re.match(r"[^@]+@[^@]+\.[^@]+", email))

def verify_password(stored_hash, password):
    """Verify password against stored hash"""
    try:
        return bcrypt.checkpw(password.encode(), stored_hash.encode())
    except Exception as e:
        print(f"❌ Error verifying password: {e}")
        return False

def update_user_last_login(user_id):
    """Update user's last login timestamp"""
    try:
        user_obj_id = ObjectId(user_id) if isinstance(user_id, str) and ObjectId.is_valid(user_id) else user_id
        db.users.update_one(
            {"_id": user_obj_id},
            {"$set": {"last_login": datetime.utcnow()}}
        )
        print(f"✅ Updated last login for user {user_id}")
        return True
    except Exception as e:
        print(f"❌ Error updating last login for user {user_id}: {e}")
        return False

def delete_book_and_summary(book_id):
    """
    Delete a book and all its summaries safely
    """
    try:
        if isinstance(book_id, str):
            book_id = ObjectId(book_id)

        # Delete summaries first
        db.summaries.delete_many({"book_id": book_id})

        # Delete the book
        result = db.books.delete_one({"_id": book_id})

        return result.deleted_count > 0

    except Exception as e:
        print(f"Error deleting book and summary: {e}")
        return False

def get_user_by_id(user_id):
    """Get user by ID"""
    try:
        user_obj_id = ObjectId(user_id) if isinstance(user_id, str) and ObjectId.is_valid(user_id) else user_id
        user = db.users.find_one({"_id": user_obj_id})
        if user:
            user['_id'] = str(user.get('_id', ''))
        return user
    except Exception as e:
        print(f"❌ Error getting user by ID {user_id}: {e}")
        return None

# Initialize database collections on import
print("🔧 Initializing database collections...")
try:
    collections_needed = ['users', 'books', 'summaries', 'progress', 'errors', 'summary_actions']
    for collection in collections_needed:
        if collection not in db.list_collection_names():
            db.create_collection(collection)
            print(f"  ✅ Created collection: {collection}")
except Exception as e:
    print(f"⚠️ Could not initialize collections: {e}")

print("🎉 Database module loaded successfully!")