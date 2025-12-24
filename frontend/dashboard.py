# frontend/dashboard.py

import streamlit as st
import os
import sys
from datetime import datetime, timedelta
from bson import ObjectId

# Import backend & database
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from backend.auth import get_current_user
from utils.database import db


def time_ago(timestamp):
    """Convert timestamp to human-readable time ago"""
    if not timestamp:
        return "—"
    
    now = datetime.utcnow()
    diff = now - timestamp
    
    if diff < timedelta(minutes=1):
        return "Just now"
    if diff < timedelta(hours=1):
        minutes = diff.seconds // 60
        return f"{minutes} minute{'s' if minutes > 1 else ''} ago"
    if diff < timedelta(days=1):
        hours = diff.seconds // 3600
        return f"{hours} hour{'s' if hours > 1 else ''} ago"
    if diff < timedelta(days=7):
        return f"{diff.days} day{'s' if diff.days > 1 else ''} ago"
    
    return timestamp.strftime("%b %d, %Y")


def get_user_stats(user_id):
    """Get comprehensive user statistics"""
    try:
        uid = ObjectId(user_id)
    except:
        uid = user_id
    
    mongo = db
    
    # Basic counts
    total_books = mongo.books.count_documents({"user_id": uid})
    total_summaries = mongo.summaries.count_documents({"user_id": uid})
    
    # Get last activity
    last_book = mongo.books.find_one({"user_id": uid}, sort=[("uploaded_at", -1)])
    last_summary = mongo.summaries.find_one({"user_id": uid}, sort=[("created_at", -1)])
    
    latest_activity = None
    if last_book:
        latest_activity = last_book.get("uploaded_at")
    if last_summary and (not latest_activity or last_summary["created_at"] > latest_activity):
        latest_activity = last_summary["created_at"]
    
    # Word count statistics
    pipeline = [
        {"$match": {"user_id": uid}},
        {"$group": {
            "_id": None,
            "total_words": {"$sum": "$word_count"},
            "avg_words": {"$avg": "$word_count"},
            "max_words": {"$max": "$word_count"}
        }}
    ]
    
    word_stats = list(mongo.books.aggregate(pipeline))
    
    return {
        "total_books": total_books,
        "total_summaries": total_summaries,
        "latest_activity": latest_activity,
        "total_words": word_stats[0]["total_words"] if word_stats else 0,
        "avg_book_words": word_stats[0]["avg_words"] if word_stats else 0,
        "max_book_words": word_stats[0]["max_words"] if word_stats else 0
    }


def dashboard_page():
    """Main dashboard page - simplified version"""
    
    # Get current user
    user = get_current_user(st.session_state)
    
    # Dashboard header
    st.title(f"📊 Dashboard - Welcome {user['name']}!")
    st.markdown(f"**Last login:** {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    st.divider()
    
    # Get user statistics
    stats = get_user_stats(user["user_id"])
    
    # Statistics Cards - Simple version
    st.subheader("Your Statistics")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric("📚 Books Uploaded", stats["total_books"])
    
    with col2:
        st.metric("📄 Summaries Generated", stats["total_summaries"])
    
    with col3:
        st.metric("🔤 Total Words", f"{stats['total_words']:,}")
    
    st.divider()
    
    # Recent Activity - Simplified
    st.subheader("Recent Activity")
    
    try:
        uid = ObjectId(user["user_id"])
    except:
        uid = user["user_id"]
    
    mongo = db
    
    # Get recent books
    recent_books = list(mongo.books.find({"user_id": uid})
                       .sort("uploaded_at", -1)
                       .limit(5))
    
    # Get recent summaries
    recent_summaries = list(mongo.summaries.find({"user_id": uid})
                           .sort("created_at", -1)
                           .limit(5))
    
    if recent_books:
        st.write("**Recent Books:**")
        for book in recent_books:
            time_str = time_ago(book.get("uploaded_at"))
            st.write(f"• **{book.get('title', 'Untitled')}** - {time_str}")
    
    if recent_summaries:
        st.write("**Recent Summaries:**")
        for summary in recent_summaries:
            book = mongo.books.find_one({"_id": summary["book_id"]})
            book_title = book.get("title", "Unknown Book") if book else "Unknown Book"
            time_str = time_ago(summary.get("created_at"))
            version = f" (v{summary.get('version', 1)})" if summary.get('version', 1) > 1 else ""
            st.write(f"• **{book_title}**{version} - {time_str}")
    
    if not recent_books and not recent_summaries:
        st.info("No recent activity. Start by uploading your first book!")
    
    st.divider()
    
    # Quick Actions - Simplified
    st.subheader("Quick Actions")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.button("📤 Upload Book", use_container_width=True):
            st.session_state.page = "upload"
            st.rerun()
    
    with col2:
        if st.button("📚 My Books", use_container_width=True):
            st.session_state.page = "mybooks"
            st.rerun()
    
    with col3:
        if st.button("✨ Generate Summary", use_container_width=True):
            st.session_state.page = "generate_summary"
            st.rerun()
    
    # Additional info at bottom
    st.divider()
    
    if recent_books:
        st.write("**Quick Access to Recent Books:**")
        cols = st.columns(min(3, len(recent_books)))
        
        for idx, book in enumerate(recent_books[:3]):
            with cols[idx]:
                if st.button(f"Summarize: {book.get('title', 'Book')[:15]}...", 
                           key=f"quick_sum_{book['_id']}", 
                           use_container_width=True):
                    st.session_state.current_book = str(book["_id"])
                    st.session_state.page = "generate_summary"
                    st.rerun()


def navigate_to(page):
    """Navigate to a specific page"""
    st.session_state.page = page
    st.rerun()