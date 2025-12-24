# utils/database.py

import os
import re
import bcrypt
from bson import ObjectId
from pymongo import MongoClient, ASCENDING
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

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


# In utils/database.py, update the create_book function:

def create_book(user_id, title, author="", chapter="", file_path="", raw_text=""):
    """Create a new book entry in database"""
    try:
        book_data = {
            "user_id": ObjectId(user_id) if isinstance(user_id, str) else user_id,
            "title": title,
            "author": author,
            "chapter": chapter,
            "file_path": file_path,
            "raw_text": raw_text,
            "status": "uploaded",
            "uploaded_at": datetime.now(),
            "word_count": len(raw_text.split()) if raw_text else 0,
            "file_type": file_path.split(".")[-1].lower() if file_path else "txt"
        }
        result = db.books.insert_one(book_data)
        return result.inserted_id
    except Exception as e:
        print(f"Error creating book: {e}")
        return None


def update_book_status(book_id, status):
    """Update book workflow status."""
    db.books.update_one(
        {"_id": ObjectId(book_id)},
        {"$set": {"status": status}}
    )


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
def get_book_by_id(book_id):
    return db.books.find_one({"_id":ObjectId(book_id)})

def update_progress(book_id,message,percentage):
    db.progress.update_one(
        {"book_id":ObjectId(book_id)},
        {
            "$set":{
                "message":message,
                "percentage":percentage,
                "updated_at":datetime.utcnow()

            }
        },
        upsert=True
    )  
    db.books.update_one(
        {"_id": ObjectId(book_id)},
        {
            "$set": {
                "progress": percentage,
                "progress_message": message,
                "updated_at": datetime.utcnow()
            }
        }
    )  

def get_progress(book_id):
    return db.progress.find_one({"book_id":ObjectId(book_id)})

def log_error(book_id, error_message):
    db.errors.insert_one({
        "book_id": book_id,
        "error": error_message,
        "created_at": datetime.utcnow()
    })

def save_summary(book_id, user_id, summary_text, chunk_summaries, summary_options):
    return create_summary(
        book_id=book_id,
        user_id=user_id,
        summary_text=summary_text,
        summary_length=summary_options.get("length"),
        summary_style=summary_options.get("style"),
        chunk_summaries=chunk_summaries,
        processing_time=summary_options.get("processing_time", 0)
    )


def delete_book_and_summary(book_id):
    """Delete a book and all its associated data"""
    try:
        # Convert string ID to ObjectId
        if isinstance(book_id, str):
            try:
                book_id = ObjectId(book_id)
            except Exception as e:
                print(f"Invalid book ID format: {book_id}, error: {e}")
                return False
        
        # First get the book details to check file path
        book = db.books.find_one({"_id": book_id})
        if not book:
            print(f"Book {book_id} not found in database")
            return False
        
        # Store book info for logging
        book_title = book.get("title", "Unknown")
        is_temporary = book.get("is_temporary", False)
        
        # Delete the book file if it exists and is not in use
        file_deleted = False
        if book and "file_path" in book:
            file_path = book.get("file_path")
            try:
                if file_path and os.path.exists(file_path):
                    # Check if it's a temporary file
                    if is_temporary or "temp_" in os.path.basename(file_path):
                        os.remove(file_path)
                        file_deleted = True
                        print(f"Deleted temporary file: {file_path}")
                    else:
                        # For regular files, ask or implement retention policy
                        print(f"Keeping uploaded file: {file_path}")
            except Exception as e:
                print(f"Warning: Could not delete file {file_path}: {e}")
        
        # Delete all associated data in correct order
        deleted_count = 0
        
        # 1. Delete progress data if exists
        progress_result = db.progress.delete_many({"book_id": book_id})
        if progress_result.deleted_count > 0:
            deleted_count += progress_result.deleted_count
            print(f"Deleted {progress_result.deleted_count} progress records")
        
        # 2. Delete any error logs
        error_result = db.errors.delete_many({"book_id": book_id})
        if error_result.deleted_count > 0:
            deleted_count += error_result.deleted_count
            print(f"Deleted {error_result.deleted_count} error records")
        
        # 3. Delete summaries (there could be multiple if regenerated)
        summary_result = db.summaries.delete_many({"book_id": book_id})
        if summary_result.deleted_count > 0:
            deleted_count += summary_result.deleted_count
            print(f"Deleted {summary_result.deleted_count} summaries")
        
        # 4. Delete the book itself
        book_result = db.books.delete_one({"_id": book_id})
        if book_result.deleted_count > 0:
            deleted_count += book_result.deleted_count
            print(f"Deleted book: {book_title}")
        
        # Clean up session states if they exist (for Streamlit)
        try:
            import streamlit as st
            # Clean up any session states related to this book
            session_keys_to_clean = [
                f"show_text_{book_id}",
                f"show_summary_{book_id}",
                f"confirm_delete_{book_id}",
                f"view_{book_id}",
                f"close_{book_id}"
            ]
            
            for key in session_keys_to_clean:
                if key in st.session_state:
                    del st.session_state[key]
        except:
            pass  # Not in Streamlit context
        
        success = book_result.deleted_count > 0
        
        if success:
            print(f"Successfully deleted book '{book_title}' and associated data")
            print(f"Total items deleted: {deleted_count}")
        else:
            print(f"Failed to delete book '{book_title}'")
        
        return success
        
    except Exception as e:
        print(f"Error deleting book {book_id}: {e}")
        import traceback
        traceback.print_exc()
        return False


def delete_all_user_books(user_id):
    """Delete all books and associated data for a user"""
    try:
        if isinstance(user_id, str):
            user_id = ObjectId(user_id)
        
        print(f"Deleting all books for user: {user_id}")
        
        # Get all books for this user
        user_books = list(db.books.find({"user_id": user_id}))
        total_books = len(user_books)
        
        if total_books == 0:
            print("No books found for user")
            return True
        
        deleted_count = 0
        failed_count = 0
        
        # Delete each book individually
        for book in user_books:
            book_id = str(book["_id"])
            if delete_book_and_summary(book_id):
                deleted_count += 1
            else:
                failed_count += 1
        
        print(f"Deleted {deleted_count}/{total_books} books successfully")
        print(f"Failed to delete {failed_count} books")
        
        return failed_count == 0
        
    except Exception as e:
        print(f"Error deleting all user books: {e}")
        return False


def delete_temporary_books(user_id=None, older_than_hours=24):
    """Delete temporary books (optional: for specific user and older than X hours)"""
    try:
        from datetime import datetime, timedelta
        
        # Build query for temporary books
        query = {"is_temporary": True}
        
        if user_id:
            if isinstance(user_id, str):
                user_id = ObjectId(user_id)
            query["user_id"] = user_id
        
        if older_than_hours:
            cutoff_time = datetime.now() - timedelta(hours=older_than_hours)
            query["uploaded_at"] = {"$lt": cutoff_time}
        
        # Find temporary books
        temp_books = list(db.books.find(query))
        
        if not temp_books:
            print(f"No temporary books found matching criteria")
            return 0
        
        print(f"Found {len(temp_books)} temporary books to clean up")
        
        deleted_count = 0
        for book in temp_books:
            book_id = str(book["_id"])
            if delete_book_and_summary(book_id):
                deleted_count += 1
        
        print(f"Deleted {deleted_count} temporary books")
        return deleted_count
        
    except Exception as e:
        print(f"Error deleting temporary books: {e}")
        return 0


def cleanup_orphaned_data():
    """Clean up orphaned data (summaries without books, etc.)"""
    try:
        print("Starting data cleanup...")
        
        # Find all books
        all_books = list(db.books.find({}, {"_id": 1}))
        book_ids = [str(b["_id"]) for b in all_books]
        
        # Find orphaned summaries (summaries without corresponding books)
        orphaned_summaries = 0
        all_summaries = list(db.summaries.find({}, {"_id": 1, "book_id": 1}))
        
        for summary in all_summaries:
            summary_book_id = str(summary["book_id"])
            if summary_book_id not in book_ids:
                db.summaries.delete_one({"_id": summary["_id"]})
                orphaned_summaries += 1
        
        print(f"Deleted {orphaned_summaries} orphaned summaries")
        
        # Clean up orphaned progress data
        orphaned_progress = 0
        all_progress = list(db.progress.find({}, {"_id": 1, "book_id": 1}))
        
        for progress in all_progress:
            progress_book_id = str(progress.get("book_id", ""))
            if progress_book_id and progress_book_id not in book_ids:
                db.progress.delete_one({"_id": progress["_id"]})
                orphaned_progress += 1
        
        print(f"Deleted {orphaned_progress} orphaned progress records")
        
        return {
            "orphaned_summaries": orphaned_summaries,
            "orphaned_progress": orphaned_progress
        }
        
    except Exception as e:
        print(f"Error in data cleanup: {e}")
        return {"error": str(e)}

def save_summary_with_metadata(
        book_id,
        user_id,
        summary_text,
        chunk_summaries,
        summary_options,
        refinement_metadata=None,
        preprocessing_stats=None,
        processing_stats=None,
        version=None,
        is_active=True
) :
    """
    Enhancing Save Summary Function with version control and metadata
    """   
    try:
        existing_summaries = list(db.summaries.find({
            "book_id":ObjectId(book_id),
            "user_id":ObjectId(user_id),

        }).sort("version",-1).limit(1))

        if version is None:
            version = 1
            if existing_summaries:
                version = existing_summaries[0].get("version",0) + 1
        if is_active and version > 1:
            db.summaries.update_many({
                "book_id":ObjectId(book_id),
                "user_id":ObjectId(user_id),
                "is_active": True
            },
            {"$set":{"is_active":False}}
            )  
        summary_doc = {
            "book_id": ObjectId(book_id),
            "user_id":ObjectId(user_id),
            "summary_text": summary_text,
            "chunk_summaries": chunk_summaries,
            "summary_options": summary_options,
            "refinement_metadata": refinement_metadata or {},
            "preprocessing_stats": preprocessing_stats or {},
            "processing_stats": processing_stats or {},
            "version": version,
            "is_active": is_active,
            "summary_type": summary_options.get("type", "auto_generated"),
            "word_count": len(summary_text.split()),
            "char_count": len(summary_text),
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow(),
            "tags": summary_options.get("tags", []),
            "access_level": summary_options.get("access_level", "private"),
            "is_favorite": False,
            "rating": None,
            "feedback": None
        }  
        result = db.summaries.insert_one(summary_doc)

        log_summary_action(
            summary_id = result.inserted_id,
            user_id = user_id,
            action = "create",
            metadata={
                "version":version,
                "book_id":book_id,
                "word_count" : summary_doc["word_count"]
            }
        ) 
        return str(result.inserted_id)

    except Exception as e:
        print(f"Error saving summary with metadata: {e}")
        raise   

def get_summary_by_id(summary_id,include_book_info=True):
    """
    Get Summary by ID with optional book information
    """       
    try:
        summary = db.summaries.find_one({"_id":ObjectId(summary_id)})

        if not summary:
            return None

        summary["_id"] = str(summary["_id"])
        summary["book_id"] = str(summary["book_id"])
        summary_id["user_id"] = str(summary["user_id"])

        if include_book_info:
            book = get_book_by_id(summary["book_id"])
            if book:
                summary["book_info"] = {
                    "title": book.get("title","Unknown"),
                    "author":book.get("author","Unkown"),
                    "upload_data":book.get("uploaded_at")
                } 
            return summary
    except Exception as e:
        print(f"Error getting summary by ID:{e}")
        return None

def get_user_summaries_with_pagination(
    user_id,
    page=1,
    limit=20,
    filters=None,
    sort_by="created_at",
    sort_order=-1
):
    """
    Get paginated summaries form user with filtering options
    """
    try:
        query = {"user_id":ObjectId(user_id)}

        if filter:
            if filter.get("book_id"):
                query["book_id"] = ObjectId(filter["book_id"])
            if filter.get("is_active") is not None:
                query["is_active"] = filter["is_active"]
            if filter.get("summary_type"):
                query["summary_types"] = filter["summary_type"]   
            if filters.get("min_word_count"):
                query["word_count"] = {"$gte": filters["min_word_count"]}
            if filters.get("max_word_count"):
                if "word_count" in query:
                    query["word_count"]["$lte"] = filters["max_word_count"]
                else:
                    query["word_count"] = {"$lte": filters["max_word_count"]}
            if filters.get("date_from"):
                query["created_at"] = {"$gte": filters["date_from"]}
            if filters.get("date_to"):
                if "created_at" in query:
                    query["created_at"]["$lte"] = filters["date_to"]
                else:
                    query["created_at"] = {"$lte": filters["date_to"]}

        skip = (page - 1) * limit
        total = db.summaries.count_documents(query)
        summaries = list(db.summaries.find(query)
          .sort(sort_by,sort_order)
          .skip(skip)
          .limit(limit))

        processed_summaries = []
        for summary in summaries:
            summary['_id'] = str(summary["_id"])
            summary["book_id"] = str(summary["book_id"])
            summary["user_id"] = str(summary["user_id"])

            book = get_book_by_id(summary["book_id"])
            if book:
                summary["book_title"] = book.get("title","unknown Book")
            processed_summaries.append(summary)
        return {
            "summaries": processed_summaries,
            "total":total,
            "page":page,
            "limit":limit,
            "total_pages": (total + limit -1 )// limit
        } 
    except Exception as e:
        print(f"error getting user summaries: {e}")
        return{"summaries":[],"total":0,"page":page,"limit":limit,"total_pages": 0}                           

def get_book_summary_versions(book_id, user_id):
    """
    Get all summary versions for a specific book
    """
    try:
        summaries = list(db.summaries.find({
            "book_id": ObjectId(book_id),
            "user_id": ObjectId(user_id)
        }).sort("version", -1))
        
        # Process and format versions
        for summary in summaries:
            summary["_id"] = str(summary["_id"])
            summary["book_id"] = str(summary["book_id"])
            summary["user_id"] = str(summary["user_id"])
            
            # Add version label
            if summary.get("is_active"):
                summary["version_label"] = f"v{summary['version']} (Active)"
            else:
                summary["version_label"] = f"v{summary['version']}"
        
        return summaries
        
    except Exception as e:
        print(f"Error getting book summary versions: {e}")
        return []
def update_summary_metadata(summary_id, user_id, updates):
    """
    Update summary metadata (not the summary text itself)
    """
    try:
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
            return False
        
        # Add updated timestamp
        filtered_updates["updated_at"] = datetime.utcnow()
        
        # Perform update
        result = db.summaries.update_one(
            {
                "_id": ObjectId(summary_id),
                "user_id": ObjectId(user_id)
            },
            {"$set": filtered_updates}
        )
        
        if result.modified_count > 0:
            # Log the update action
            log_summary_action(
                summary_id=summary_id,
                user_id=user_id,
                action="update",
                metadata={"updated_fields": list(filtered_updates.keys())}
            )
            return True
        
        return False
        
    except Exception as e:
        print(f"Error updating summary metadata: {e}")
        return False

def delete_summary(summary_id, user_id, permanent=False):
    """
    Delete a summary (soft delete by default)
    """
    try:
        if permanent:
            # Permanent delete
            result = db.summaries.delete_one({
                "_id": ObjectId(summary_id),
                "user_id": ObjectId(user_id)
            })
            
            if result.deleted_count > 0:
                log_summary_action(
                    summary_id=summary_id,
                    user_id=user_id,
                    action="delete_permanent",
                    metadata={}
                )
                return True
        else:
            # Soft delete (deactivate)
            result = db.summaries.update_one(
                {
                    "_id": ObjectId(summary_id),
                    "user_id": ObjectId(user_id)
                },
                {
                    "$set": {
                        "is_active": False,
                        "deleted_at": datetime.utcnow(),
                        "updated_at": datetime.utcnow()
                    }
                }
            )
            
            if result.modified_count > 0:
                log_summary_action(
                    summary_id=summary_id,
                    user_id=user_id,
                    action="delete_soft",
                    metadata={}
                )
                return True
        
        return False
        
    except Exception as e:
        print(f"Error deleting summary: {e}")
        return False

def restore_summary(summary_id, user_id):
    """
    Restore a soft-deleted summary
    """
    try:
        result = db.summaries.update_one(
            {
                "_id": ObjectId(summary_id),
                "user_id": ObjectId(user_id),
                "is_active": False
            },
            {
                "$set": {
                    "is_active": True,
                    "deleted_at": None,
                    "updated_at": datetime.utcnow()
                }
            }
        )
        
        if result.modified_count > 0:
            log_summary_action(
                summary_id=summary_id,
                user_id=user_id,
                action="restore",
                metadata={}
            )
            return True
        
        return False
        
    except Exception as e:
        print(f"Error restoring summary: {e}")
        return False

def set_active_summary_version(book_id, user_id, version):
    """
    Set a specific version as the active summary for a book
    """
    try:
        # First deactivate all versions for this book/user
        db.summaries.update_many(
            {
                "book_id": ObjectId(book_id),
                "user_id": ObjectId(user_id),
                "is_active": True
            },
            {"$set": {"is_active": False}}
        )
        
        # Activate the specified version
        result = db.summaries.update_one(
            {
                "book_id": ObjectId(book_id),
                "user_id": ObjectId(user_id),
                "version": version
            },
            {
                "$set": {
                    "is_active": True,
                    "updated_at": datetime.utcnow()
                }
            }
        )
        
        if result.modified_count > 0:
            log_summary_action(
                summary_id=None,
                user_id=user_id,
                action="set_active_version",
                metadata={"book_id": book_id, "version": version}
            )
            return True
        
        return False
        
    except Exception as e:
        print(f"Error setting active version: {e}")
        return False

def log_summary_action(summary_id, user_id, action, metadata=None):
    """
    Log summary-related actions for analytics
    """
    try:
        log_entry = {
            "summary_id": ObjectId(summary_id) if summary_id else None,
            "user_id": ObjectId(user_id),
            "action": action,
            "metadata": metadata or {},
            "timestamp": datetime.utcnow()
        }
        
        db.summary_actions.insert_one(log_entry)
        return True
        
    except Exception as e:
        print(f"Error logging summary action: {e}")
        return False

# ---------- ADMIN FUNCTIONS ----------

def get_all_summaries_admin(page=1, limit=50, filters=None):
    """
    Admin function: Get all summaries in the system
    """
    try:
        query = {}
        
        # Apply filters if provided
        if filters:
            if filters.get("user_id"):
                query["user_id"] = ObjectId(filters["user_id"])
            if filters.get("book_id"):
                query["book_id"] = ObjectId(filters["book_id"])
            if filters.get("is_active") is not None:
                query["is_active"] = filters["is_active"]
            if filters.get("date_from"):
                query["created_at"] = {"$gte": filters["date_from"]}
            if filters.get("date_to"):
                if "created_at" in query:
                    query["created_at"]["$lte"] = filters["date_to"]
                else:
                    query["created_at"] = {"$lte": filters["date_to"]}
        
        skip = (page - 1) * limit
        total = db.summaries.count_documents(query)
        
        summaries = list(db.summaries.find(query)
            .sort("created_at", -1)
            .skip(skip)
            .limit(limit))
        
        # Process summaries with user and book info
        for summary in summaries:
            summary["_id"] = str(summary["_id"])
            summary["book_id"] = str(summary["book_id"])
            summary["user_id"] = str(summary["user_id"])
            
            # Add user info
            user = db.users.find_one({"_id": ObjectId(summary["user_id"])})
            if user:
                summary["user_info"] = {
                    "name": user.get("name", "Unknown"),
                    "email": user.get("email", "Unknown")
                }
            
            # Add book info
            book = get_book_by_id(summary["book_id"])
            if book:
                summary["book_info"] = {
                    "title": book.get("title", "Unknown"),
                    "author": book.get("author", "Unknown")
                }
        
        return {
            "summaries": summaries,
            "total": total,
            "page": page,
            "limit": limit,
            "total_pages": (total + limit - 1) // limit
        }
        
    except Exception as e:
        print(f"Error getting all summaries (admin): {e}")
        return {"summaries": [], "total": 0, "page": page, "limit": limit, "total_pages": 0}

def get_summary_analytics(time_range="7d"):
    """
    Get summary analytics for admin dashboard
    """
    try:
        from datetime import datetime, timedelta
        
        # Calculate date range
        end_date = datetime.utcnow()
        if time_range == "1d":
            start_date = end_date - timedelta(days=1)
        elif time_range == "7d":
            start_date = end_date - timedelta(days=7)
        elif time_range == "30d":
            start_date = end_date - timedelta(days=30)
        elif time_range == "90d":
            start_date = end_date - timedelta(days=90)
        else:
            start_date = datetime.min  # All time
        
        # Basic counts
        total_summaries = db.summaries.count_documents({})
        active_summaries = db.summaries.count_documents({"is_active": True})
        recent_summaries = db.summaries.count_documents({
            "created_at": {"$gte": start_date}
        })
        
        # User statistics
        pipeline_users = [
            {"$group": {"_id": "$user_id", "count": {"$sum": 1}}},
            {"$group": {
                "_id": None, 
                "total_users": {"$sum": 1}, 
                "avg_summaries": {"$avg": "$count"}
            }}
        ]
        user_stats = list(db.summaries.aggregate(pipeline_users))
        
        # Summary length statistics
        pipeline_length = [
            {"$match": {"created_at": {"$gte": start_date}}},
            {"$group": {
                "_id": None,
                "avg_word_count": {"$avg": "$word_count"},
                "avg_char_count": {"$avg": "$char_count"},
                "min_word_count": {"$min": "$word_count"},
                "max_word_count": {"$max": "$word_count"}
            }}
        ]
        length_stats = list(db.summaries.aggregate(pipeline_length))
        
        # Daily summary count
        pipeline_daily = [
            {"$match": {"created_at": {"$gte": start_date}}},
            {"$group": {
                "_id": {"$dateToString": {"format": "%Y-%m-%d", "date": "$created_at"}},
                "count": {"$sum": 1}
            }},
            {"$sort": {"_id": 1}}
        ]
        daily_counts = list(db.summaries.aggregate(pipeline_daily))
        
        # Most active users
        pipeline_active_users = [
            {"$match": {"created_at": {"$gte": start_date}}},
            {"$group": {"_id": "$user_id", "count": {"$sum": 1}}},
            {"$sort": {"count": -1}},
            {"$limit": 10},
            {"$lookup": {
                "from": "users",
                "localField": "_id",
                "foreignField": "_id",
                "as": "user_info"
            }},
            {"$unwind": {"path": "$user_info", "preserveNullAndEmptyArrays": True}},
            {"$project": {
                "user_id": {"$toString": "$_id"},
                "username": "$user_info.name",
                "email": "$user_info.email",
                "summary_count": "$count"
            }}
        ]
        active_users = list(db.summaries.aggregate(pipeline_active_users))
        
        return {
            "time_range": time_range,
            "start_date": start_date,
            "end_date": end_date,
            "totals": {
                "all_summaries": total_summaries,
                "active_summaries": active_summaries,
                "recent_summaries": recent_summaries,
                "total_users": user_stats[0]["total_users"] if user_stats else 0,
                "avg_summaries_per_user": user_stats[0]["avg_summaries"] if user_stats else 0
            },
            "length_stats": length_stats[0] if length_stats else {},
            "active_users": active_users,
            "daily_counts": daily_counts
        }
        
    except Exception as e:
        print(f"Error getting summary analytics: {e}")
        return {}    
def save_summary(book_id, user_id, summary_text, chunk_summaries=None, processing_time=None):
    """Save summary to database"""
    try:
        summary_data = {
            "book_id": ObjectId(book_id) if isinstance(book_id, str) else book_id,
            "user_id": ObjectId(user_id) if isinstance(user_id, str) else user_id,
            "summary_text": summary_text,
            "summary": summary_text,  # Keep both for compatibility
            "chunk_summaries": chunk_summaries or [],
            "processing_time": processing_time or 0,
            "created_at": datetime.now(),
            "summary_length_words": len(summary_text.split()),
            "summary_length_chars": len(summary_text)
        }
        
        result = db.summaries.insert_one(summary_data)
        return str(result.inserted_id)
    except Exception as e:
        print(f"Error saving summary: {e}")
        # Try update instead
        try:
            db.summaries.update_one(
                {"book_id": ObjectId(book_id) if isinstance(book_id, str) else book_id},
                {"$set": summary_data},
                upsert=True
            )
            return f"updated_{book_id}"
        except:
            return None    

def create_database_indexes():
    """Create all necessary database indexes"""
    
    # Existing indexes
    db.users.create_index([("email", ASCENDING)], unique=True)
    db.books.create_index([("user_id", ASCENDING)])
    db.books.create_index([("title", ASCENDING)])
    db.summaries.create_index([("book_id", ASCENDING)])
    db.summaries.create_index([("user_id", ASCENDING)])
    
    # New indexes for Task 13
    db.summaries.create_index([("version", ASCENDING)])
    db.summaries.create_index([("is_active", ASCENDING)])
    db.summaries.create_index([("created_at", DESCENDING)])
    db.summaries.create_index([("user_id", ASCENDING), ("book_id", ASCENDING)])
    db.summaries.create_index([("user_id", ASCENDING), ("created_at", DESCENDING)])
    
    # Index for summary actions (analytics)
    db.summary_actions.create_index([("timestamp", DESCENDING)])
    db.summary_actions.create_index([("user_id", ASCENDING)])
    db.summary_actions.create_index([("action", ASCENDING)])
    
    print("✅ Database indexes created successfully")
