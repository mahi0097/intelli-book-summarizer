import streamlit as st
import os
import sys
from datetime import datetime, timedelta
from bson import ObjectId

# Import backend & database
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from backend.auth import get_current_user
from utils.database import db
from frontend.helper import get_current_user, is_logged_in




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
    """Main dashboard page with history buttons"""
    
    if not is_logged_in():
        st.error("Please login to access the dashboard")
        st.session_state.page = "login"
        st.rerun()
        return
    # Get current user
    user = get_current_user()
    if isinstance(user, dict):
        user_name = user.get('name', user.get('username', 'User'))
    else:
        user_name = "User"
    # Dashboard header
    st.title(f"📊 Dashboard - Welcome {user['name']}!")
    st.markdown("""
<style>
.metric-container {
    background-color: #f8f9fa;
    padding: 16px;
    border-radius: 10px;
    margin-bottom: 10px;
}
.summary-card {
    background-color: #ffffff;
    padding: 14px;
    border-radius: 8px;
    border: 1px solid #eee;
}
</style>
""", unsafe_allow_html=True)

    st.markdown(f"**Last login:** {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    st.divider()
    
    # Get user statistics
    stats = get_user_stats(user["user_id"])
    
    # Statistics Cards - Simple version
    st.subheader("Your Statistics")
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("📚 Books Uploaded", stats["total_books"])
    
    with col2:
        st.metric("📄 Summaries Generated", stats["total_summaries"])
    
    with col3:
        st.metric("🔤 Total Words", f"{stats['total_words']:,}")
    
    with col4:
        if stats["latest_activity"]:
            activity_time = time_ago(stats["latest_activity"])
            st.metric("🕐 Last Activity", activity_time)
        else:
            st.metric("🕐 Last Activity", "Never")
    
    st.divider()
    
    # NEW: Version Management Section
    st.subheader("📚 Version Management")
    st.write("Manage and compare different versions of your summaries")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.button("📜 View Version History", 
                    use_container_width=True,
                    help="View all versions of your summaries with timestamps and settings"):
            st.session_state.page = "summary_history"
            st.rerun()
    
    with col2:
        if st.button("🔍 Compare Versions", 
                    use_container_width=True,
                    help="Compare different summary versions side-by-side"):
            st.session_state.page = "compare"
            st.rerun()
    
    with col3:
        if st.button("⭐ Favorite Summaries", 
                    use_container_width=True,
                    help="View and manage your favorite summaries"):
            # We'll navigate to summaries page with filter for favorites
            st.session_state.page = "summaries"
            st.session_state.show_favorites = True
            st.rerun()
    
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
    
    # Recent Books Section
    if recent_books:
        st.write("**📚 Recent Books:**")
        for book in recent_books:
            time_str = time_ago(book.get("uploaded_at"))
            book_id = str(book["_id"])
            
            col1, col2, col3 = st.columns([3, 1, 1])
            with col1:
                st.write(f"• **{book.get('title', 'Untitled')}**")
                st.caption(f"Uploaded: {time_str} | Words: {book.get('word_count', 0):,}")
            
            with col2:
                if st.button("📖 View", key=f"view_book_{book_id}", use_container_width=True):
                    st.session_state.current_book = book_id
                    st.session_state.page = "mybooks"
                    st.rerun()
            
            with col3:
                if st.button("✨ Summarize", key=f"sum_book_{book_id}", use_container_width=True):
                    st.session_state.current_book = book_id
                    st.session_state.page = "generate_summary"
                    st.rerun()
    
    # Recent Summaries Section
    if recent_summaries:
        st.write("**📄 Recent Summaries:**")
        for summary in recent_summaries:
            book = mongo.books.find_one({"_id": summary["book_id"]})
            book_title = book.get("title", "Unknown Book") if book else "Unknown Book"
            time_str = time_ago(summary.get("created_at"))
            summary_id = str(summary["_id"])
            
            # Check if this summary has multiple versions
            version_count = mongo.summaries.count_documents({
                "book_id": summary["book_id"],
                "user_id": uid
            })
            
            col1, col2, col3, col4 = st.columns([3, 1, 1, 1])
            with col1:
                version_text = f"v{summary.get('version', 1)}"
                if version_count > 1:
                    version_text += f" ({version_count} versions)"
                
                favorite_star = "⭐ " if summary.get('is_favorite') else ""
                active_badge = "✅ " if summary.get('is_active') else ""
                
                st.write(f"• {favorite_star}{active_badge}**{book_title}** ({version_text})")
                st.caption(f"Created: {time_str} | Words: {summary.get('word_count', 0):,}")
            
            with col2:
                if st.button("👁️ View", key=f"view_sum_{summary_id}", use_container_width=True):
                    st.session_state.current_summary = summary_id
                    st.session_state.page = "summaries"
                    st.rerun()
            
            with col3:
                if st.button("📝 History", key=f"hist_sum_{summary_id}", use_container_width=True):
                    st.session_state.selected_book_for_history = str(summary["book_id"])
                    st.session_state.page = "summary_history"
                    st.rerun()
            
            with col4:
                if version_count > 1:
                    if st.button("🔍 Compare", key=f"comp_sum_{summary_id}", use_container_width=True):
                        st.session_state.selected_book_for_comparison = str(summary["book_id"])
                        st.session_state.page = "compare"
                        st.rerun()
    
    if not recent_books and not recent_summaries:
        st.info("No recent activity. Start by uploading your first book!")
    
    st.divider()
    
    # Quick Actions - Expanded
    st.subheader("Quick Actions")
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        if st.button("📤 Upload Book", 
                    use_container_width=True,
                    help="Upload a new book file to summarize"):
            st.session_state.page = "upload"
            st.rerun()
    
    with col2:
        if st.button("📚 My Books", 
                    use_container_width=True,
                    help="View and manage all your uploaded books"):
            st.session_state.page = "mybooks"
            st.rerun()
    
    with col3:
        if st.button("✨ Generate Summary", 
                    use_container_width=True,
                    help="Generate a summary for your book"):
            st.session_state.page = "generate_summary"
            st.rerun()
    
    with col4:
        if st.button("📜 All Summaries", 
                    use_container_width=True,
                    help="View all your generated summaries"):
            st.session_state.page = "summaries"
            st.rerun()
    
    # Additional info at bottom
    st.divider()
    
    # Tips and Information
    with st.expander("💡 Tips & Information", expanded=False):
        st.info("""
        **Version Management Features:**
        
        1. **Version History**: Track all versions of your summaries with timestamps
        2. **Compare Versions**: Side-by-side comparison with diff highlighting
        3. **Favorites**: Mark your best summaries for quick access
        4. **Archive**: Store old versions without deleting them
        5. **Restore**: Bring back any previous version
        
        **Pro Tips:**
        - Generate multiple summaries with different settings to compare results
        - Mark your best summaries as favorites for quick access
        - Use the comparison feature to see how your summaries improve over time
        - Archive old versions instead of deleting to maintain a complete history
        """)
    
    # System Information
    with st.expander("📊 System Information", expanded=False):
        try:
            # Get additional stats
            total_users = db.users.count_documents({})
            active_today = db.summaries.count_documents({
                "created_at": {"$gte": datetime.utcnow().replace(hour=0, minute=0, second=0)}
            })
            
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("👥 Total Users", total_users)
            with col2:
                st.metric("📈 Summaries Today", active_today)
            with col3:
                st.metric("📅 Active Days", (datetime.now() - user.get('created_at', datetime.now())).days)
        except:
            st.write("System statistics temporarily unavailable")


def navigate_to(page):
    """Navigate to a specific page"""
    st.session_state.page = page
    st.rerun()