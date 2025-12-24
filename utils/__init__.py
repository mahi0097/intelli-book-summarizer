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