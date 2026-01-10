# backend/admin_api.py - UPDATED (STREAMLIT HELPER FUNCTIONS)
import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from bson import ObjectId
from datetime import datetime, timedelta
from utils.database import db
import pandas as pd

# ========== ADMIN HELPER FUNCTIONS FOR STREAMLIT ==========

def get_all_users_admin(page=1, limit=50, filters=None):
    """Get all users for admin dashboard"""
    try:
        query = {}
        if filters:
            if filters.get('role'):
                query['role'] = filters['role']
            if filters.get('email'):
                query['email'] = {"$regex": filters['email'], "$options": "i"}
        
        skip = (page - 1) * limit
        users = list(db.users.find(query).skip(skip).limit(limit))
        total = db.users.count_documents(query)
        
        processed_users = []
        for user in users:
            # Get user statistics
            summary_count = db.summaries.count_documents({"user_id": user['_id']})
            book_count = db.books.count_documents({"user_id": user['_id']})
            
            processed_user = {
                "id": str(user['_id']),
                "name": user.get('name', ''),
                "email": user.get('email', ''),
                "role": user.get('role', 'user'),
                "created_at": user.get('created_at'),
                "stats": {
                    "summaries": summary_count,
                    "books": book_count
                }
            }
            processed_users.append(processed_user)
        
        return {
            "success": True,
            "data": {
                "users": processed_users,
                "total": total,
                "page": page,
                "limit": limit,
                "total_pages": (total + limit - 1) // limit
            }
        }
        
    except Exception as e:
        return {"success": False, "error": str(e)}

def get_user_detail_admin(user_id):
    """Get detailed user information for admin"""
    try:
        user = db.users.find_one({"_id": ObjectId(user_id)})
        if not user:
            return {"success": False, "error": "User not found"}
        
        # Get user statistics
        summary_count = db.summaries.count_documents({"user_id": ObjectId(user_id)})
        book_count = db.books.count_documents({"user_id": ObjectId(user_id)})
        
        # Get recent summaries
        recent_summaries = list(db.summaries.find(
            {"user_id": ObjectId(user_id)}
        ).sort("created_at", -1).limit(10))
        
        for summary in recent_summaries:
            summary['_id'] = str(summary['_id'])
            summary['book_id'] = str(summary.get('book_id'))
        
        # Get user activity timeline
        activity = list(db.summaries.aggregate([
            {"$match": {"user_id": ObjectId(user_id)}},
            {"$group": {
                "_id": {"$dateToString": {"format": "%Y-%m-%d", "date": "$created_at"}},
                "count": {"$sum": 1},
                "avg_words": {"$avg": "$word_count"}
            }},
            {"$sort": {"_id": -1}},
            {"$limit": 30}
        ]))
        
        user_data = {
            "id": str(user['_id']),
            "name": user.get('name', ''),
            "email": user.get('email', ''),
            "role": user.get('role', 'user'),
            "created_at": user.get('created_at'),
            "stats": {
                "total_summaries": summary_count,
                "total_books": book_count,
                "avg_summary_length": db.summaries.aggregate([
                    {"$match": {"user_id": ObjectId(user_id)}},
                    {"$group": {"_id": None, "avg": {"$avg": "$word_count"}}}
                ]).next().get('avg', 0) if summary_count > 0 else 0
            },
            "recent_summaries": recent_summaries,
            "activity_timeline": activity
        }
        
        return {"success": True, "data": user_data}
        
    except Exception as e:
        return {"success": False, "error": str(e)}

def update_user_role_admin(user_id, new_role, admin_id):
    """Update user role (admin function)"""
    try:
        if new_role not in ['user', 'admin', 'moderator']:
            return {"success": False, "error": "Invalid role"}
        
        user = db.users.find_one({"_id": ObjectId(user_id)})
        if not user:
            return {"success": False, "error": "User not found"}
        
        old_role = user.get('role', 'user')
        
        # Update role
        result = db.users.update_one(
            {"_id": ObjectId(user_id)},
            {"$set": {"role": new_role, "updated_at": datetime.utcnow()}}
        )
        
        if result.modified_count > 0:
            # Log the action
            db.admin_actions.insert_one({
                "action": "update_user_role",
                "user_id": ObjectId(user_id),
                "admin_id": ObjectId(admin_id),
                "timestamp": datetime.utcnow(),
                "metadata": {
                    "old_role": old_role,
                    "new_role": new_role,
                    "user_email": user.get('email')
                }
            })
            
            return {"success": True, "message": f"User role updated from {old_role} to {new_role}"}
        else:
            return {"success": False, "error": "Failed to update user role"}
            
    except Exception as e:
        return {"success": False, "error": str(e)}

def get_all_summaries_admin(page=1, limit=50, filters=None):
    """Get all summaries for admin view"""
    try:
        query = {}
        
        if filters:
            if filters.get('user_id'):
                query['user_id'] = ObjectId(filters['user_id'])
            if filters.get('book_id'):
                query['book_id'] = ObjectId(filters['book_id'])
            if filters.get('is_active') is not None:
                query['is_active'] = filters['is_active']
            if filters.get('date_from'):
                query['created_at'] = {"$gte": filters['date_from']}
            if filters.get('date_to'):
                if 'created_at' in query:
                    query['created_at']['$lte'] = filters['date_to']
                else:
                    query['created_at'] = {"$lte": filters['date_to']}
        
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
            book = db.books.find_one({"_id": ObjectId(summary["book_id"])})
            if book:
                summary["book_info"] = {
                    "title": book.get("title", "Unknown"),
                    "author": book.get("author", "Unknown")
                }
        
        return {
            "success": True,
            "data": {
                "summaries": summaries,
                "total": total,
                "page": page,
                "limit": limit,
                "total_pages": (total + limit - 1) // limit
            }
        }
        
    except Exception as e:
        return {"success": False, "error": str(e)}

def get_summary_analytics(time_range="30d"):
    """Get summary analytics for admin dashboard"""
    try:
        # Calculate date range
        end_date = datetime.utcnow()
        if time_range == "7d":
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
            "success": True,
            "data": {
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
        }
        
    except Exception as e:
        return {"success": False, "error": str(e)}

def delete_summary_admin(summary_id, admin_id):
    """Delete summary (admin function)"""
    try:
        # Get summary first to log
        summary = db.summaries.find_one({"_id": ObjectId(summary_id)})
        if not summary:
            return {"success": False, "error": "Summary not found"}
        
        # Delete summary
        result = db.summaries.delete_one({"_id": ObjectId(summary_id)})
        
        if result.deleted_count > 0:
            # Log the admin action
            db.admin_actions.insert_one({
                "action": "delete_summary",
                "summary_id": ObjectId(summary_id),
                "admin_id": ObjectId(admin_id),
                "timestamp": datetime.utcnow(),
                "metadata": {
                    "summary_text_preview": summary.get('summary_text', '')[:100],
                    "user_id": str(summary.get('user_id')),
                    "book_id": str(summary.get('book_id'))
                }
            })
            
            return {"success": True, "message": f"Summary {summary_id} deleted successfully"}
        else:
            return {"success": False, "error": "Failed to delete summary"}
            
    except Exception as e:
        return {"success": False, "error": str(e)}

def get_system_stats_admin():
    """Get system statistics and health"""
    try:
        stats = db.stats.find_one({"_id": "system_stats"})
        
        if not stats:
            stats = {
                "last_maintenance": None,
                "summary_count": 0,
                "user_count": 0,
                "book_count": 0
            }
        
        # Add current stats
        current_stats = {
            "summaries": db.summaries.count_documents({}),
            "users": db.users.count_documents({}),
            "books": db.books.count_documents({}),
            "failed_books": db.books.count_documents({"status": "failed"}),
            "processing_books": db.books.count_documents({"status": "processing"}),
            "completed_summaries": db.summaries.count_documents({"is_active": True})
        }
        
        return {
            "success": True,
            "data": {
                "stored_stats": stats,
                "current_stats": current_stats
            }
        }
        
    except Exception as e:
        return {"success": False, "error": str(e)}

def run_maintenance_cleanup(admin_id):
    """Run system maintenance cleanup"""
    try:
        from utils.database import cleanup_orphaned_data, delete_temporary_books
        
        results = {}
        
        # Cleanup orphaned data
        orphaned_result = cleanup_orphaned_data()
        results['orphaned_cleanup'] = orphaned_result
        
        # Cleanup temporary books
        temp_books_deleted = delete_temporary_books(older_than_hours=24)
        results['temporary_books'] = {"deleted": temp_books_deleted}
        
        # Update database statistics
        db.stats.update_one(
            {"_id": "system_stats"},
            {"$set": {
                "last_maintenance": datetime.utcnow(),
                "summary_count": db.summaries.count_documents({}),
                "user_count": db.users.count_documents({}),
                "book_count": db.books.count_documents({})
            }},
            upsert=True
        )
        
        # Log maintenance action
        db.admin_actions.insert_one({
            "action": "maintenance_cleanup",
            "admin_id": ObjectId(admin_id),
            "timestamp": datetime.utcnow(),
            "metadata": results
        })
        
        return {
            "success": True,
            "message": "Maintenance cleanup completed",
            "results": results
        }
        
    except Exception as e:
        return {"success": False, "error": str(e)}