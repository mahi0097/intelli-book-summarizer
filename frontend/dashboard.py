import os
import sys
from datetime import datetime, timedelta
from bson import ObjectId
import streamlit as st

# MUST be the first Streamlit command
st.set_page_config(
    page_title="Intelligent Book Summarizer Pro",
    page_icon="📚",
    layout="wide",
    initial_sidebar_state="expanded"
)
st.session_state.setdefault("sidebar_state", "expanded")
# Import backend & database
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from utils.database import db
from frontend.helper import get_current_user, is_logged_in
# ✅ Import sidebar helpers from navbar.py
from frontend.navbar import get_sidebar_css, require_auth, get_user_info


def load_dashboard_css():
    # ✅ Inject sidebar CSS from navbar.py as a separate st.markdown call
    sidebar_css = get_sidebar_css()
    st.markdown(sidebar_css, unsafe_allow_html=True)

    st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');

:root {
    --primary-dark: #2563eb;
    --primary-light: #3b82f6;
    --accent-blue: #4facfe;
    --accent-cyan: #00f2fe;
    --bg-gradient: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    --card-bg: rgba(255, 255, 255, 0.95);
    --text-primary: #2d3748;
    --text-secondary: #718096;
    --shadow-sm: 0 4px 6px rgba(0, 0, 0, 0.05);
    --shadow-md: 0 10px 15px rgba(0, 0, 0, 0.1);
    --shadow-lg: 0 20px 25px rgba(0, 0, 0, 0.15);
    --border-radius: 16px;
}

/* Main App Background */
.stApp {
    background: #eef6ff;
    font-family: 'Inter', sans-serif;
}

/* Main Content Area */
.main .block-container {
    padding: 2rem 2.5rem;
    max-width: 1400px;
    background: transparent;
}

/* Hide Streamlit Branding */
#MainMenu {visibility: hidden;}
footer {visibility: hidden;}
header {visibility: visible;}

/* ===== WELCOME HEADER ===== */
.welcome-header {
    background: var(--card-bg);
    border-radius: var(--border-radius);
    padding: 1.5rem 2rem;
    margin-bottom: 2rem;
    box-shadow: var(--shadow-lg);
    border: 1px solid rgba(255, 255, 255, 0.2);
    backdrop-filter: blur(10px);
}

.welcome-header h1 {
    color: var(--primary-dark);
    font-size: 2.2rem;
    font-weight: 700;
    margin: 0;
    letter-spacing: -0.02em;
}

.welcome-header p {
    color: var(--text-secondary);
    font-size: 1rem;
    margin: 0.5rem 0 0 0;
}

/* ===== STATISTICS CARDS ===== */
.stat-card {
    background: var(--card-bg);
    border-radius: var(--border-radius);
    padding: 1.5rem;
    box-shadow: var(--shadow-md);
    border-top: 4px solid var(--accent-blue);
    transition: transform 0.3s ease, box-shadow 0.3s ease;
    height: 100%;
    backdrop-filter: blur(10px);
}

.stat-card:hover {
    transform: translateY(-5px);
    box-shadow: var(--shadow-lg);
}

.stat-card .stat-label {
    color: var(--text-secondary);
    font-size: 0.9rem;
    font-weight: 500;
    text-transform: uppercase;
    letter-spacing: 0.05em;
    margin-bottom: 0.5rem;
}

.stat-card .stat-value {
    color: var(--primary-dark);
    font-size: 2.2rem;
    font-weight: 700;
    line-height: 1.2;
}

/* ===== SECTION HEADERS ===== */
.section-header {
    color: var(--text-primary);
    font-size: 1.5rem;
    font-weight: 600;
    margin: 2rem 0 1.5rem 0;
    letter-spacing: -0.01em;
}

/* ===== RECENT ACTIVITY CARDS ===== */
.activity-card {
    background: var(--card-bg);
    border-radius: 12px;
    padding: 1rem;
    margin-bottom: 0.75rem;
    box-shadow: var(--shadow-sm);
    border: 1px solid rgba(255, 255, 255, 0.2);
    backdrop-filter: blur(10px);
    transition: all 0.3s ease;
}

.activity-card:hover {
    box-shadow: var(--shadow-md);
    transform: translateX(5px);
}

.activity-title {
    color: var(--primary-dark);
    font-weight: 600;
    font-size: 1rem;
    margin: 0;
}

.activity-meta {
    color: var(--text-secondary);
    font-size: 0.85rem;
    margin: 0.25rem 0 0 0;
}

/* ===== EXPANDER STYLING ===== */
.streamlit-expanderHeader {
    background: var(--card-bg) !important;
    border-radius: 12px !important;
    color: var(--primary-dark) !important;
    font-weight: 600 !important;
    border: 1px solid rgba(255, 255, 255, 0.2) !important;
    backdrop-filter: blur(10px) !important;
}

.streamlit-expanderContent {
    background: var(--card-bg) !important;
    border-radius: 0 0 12px 12px !important;
    border: 1px solid rgba(255, 255, 255, 0.2) !important;
    border-top: none !important;
    backdrop-filter: blur(10px) !important;
}

/* ===== CUSTOM BUTTON OVERRIDES (main content only) ===== */
.main .stButton > button {
    border-radius: 12px !important;
    font-weight: 500 !important;
    transition: all 0.3s ease !important;
}

/* Responsive adjustments */
@media (max-width: 768px) {
    .main .block-container {
        padding: 1rem;
    }

    .welcome-header h1 {
        font-size: 1.8rem;
    }

    .stat-card .stat-value {
        font-size: 1.8rem;
    }
}

/* Custom scrollbar */
::-webkit-scrollbar {
    width: 8px;
    height: 8px;
}

::-webkit-scrollbar-track {
    background: rgba(255, 255, 255, 0.1);
    border-radius: 10px;
}

::-webkit-scrollbar-thumb {
    background: rgba(255, 255, 255, 0.3);
    border-radius: 10px;
}

::-webkit-scrollbar-thumb:hover {
    background: rgba(255, 255, 255, 0.4);
}
</style>
""", unsafe_allow_html=True)


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
    except Exception:
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
    load_dashboard_css()

    # ✅ Use get_user_info() from navbar.py — no duplicate logic
    user_name, user_id = get_user_info()

    # Now do the login check for the main content area
    if not is_logged_in():
        st.error("Please login to access the dashboard")
        st.session_state.page = "login"
        return

    # Main Content
    # Welcome Header Section
    st.markdown(f"""
    <div class="welcome-header">
        <h1>📊 Dashboard</h1>
        <p>Welcome back, {user_name}! • Last login: {datetime.now().strftime('%B %d, %Y at %I:%M %p')}</p>
    </div>
    """, unsafe_allow_html=True)

    # Get user statistics
    if user_id:
        stats = get_user_stats(user_id)
    else:
        stats = {
            "total_books": 0,
            "total_summaries": 0,
            "total_words": 0,
            "latest_activity": None
        }

    # Statistics Cards
    st.markdown('<h2 class="section-header">📈 Overview</h2>', unsafe_allow_html=True)

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.markdown(f"""
        <div class="stat-card">
            <div class="stat-label">📚 Books Uploaded</div>
            <div class="stat-value">{stats["total_books"]}</div>
        </div>
        """, unsafe_allow_html=True)

    with col2:
        st.markdown(f"""
        <div class="stat-card">
            <div class="stat-label">📄 Summaries Generated</div>
            <div class="stat-value">{stats["total_summaries"]}</div>
        </div>
        """, unsafe_allow_html=True)

    with col3:
        st.markdown(f"""
        <div class="stat-card">
            <div class="stat-label">🔤 Total Words</div>
            <div class="stat-value">{stats['total_words']:,}</div>
        </div>
        """, unsafe_allow_html=True)

    with col4:
        activity_time = time_ago(stats["latest_activity"]) if stats["latest_activity"] else "Never"
        st.markdown(f"""
        <div class="stat-card">
            <div class="stat-label">🕐 Last Activity</div>
            <div class="stat-value">{activity_time}</div>
        </div>
        """, unsafe_allow_html=True)

    # Version Management Section
    st.markdown('<h2 class="section-header">🔄 Version Management</h2>', unsafe_allow_html=True)

    col1, col2, col3 = st.columns(3)

    with col1:
        if st.button("📜 View Version History", key="content_history", use_container_width=True):
            st.session_state.page = "summary_history"
            st.rerun()

    with col2:
        if st.button("🔍 Compare Versions", key="content_compare", use_container_width=True):
            st.session_state.page = "compare"
            st.rerun()

    with col3:
        if st.button("⭐ Favorite Summaries", key="content_favorites", use_container_width=True):
            st.session_state.page = "summaries"
            st.session_state.show_favorites = True
            st.rerun()

    # Recent Activity Section
    st.markdown('<h2 class="section-header">🕒 Recent Activity</h2>', unsafe_allow_html=True)

    if user_id:
        try:
            uid = ObjectId(user_id)
        except Exception:
            uid = user_id

        mongo = db

        # Get recent books
        recent_books = list(mongo.books.find({"user_id": uid})
                            .sort("uploaded_at", -1)
                            .limit(5))

        if recent_books:
            for book in recent_books:
                time_str = time_ago(book.get("uploaded_at"))
                book_id = str(book["_id"])

                col1, col2, col3 = st.columns([4, 1, 1])

                with col1:
                    st.markdown(f"""
                    <div class="activity-card">
                        <p class="activity-title">{book.get('title', 'Untitled')}</p>
                        <p class="activity-meta">Uploaded: {time_str} • {book.get('word_count', 0):,} words</p>
                    </div>
                    """, unsafe_allow_html=True)

                with col2:
                    if st.button("👁️ View", key=f"view_book_{book_id}", use_container_width=True):
                        st.session_state.current_book = book_id
                        st.session_state.page = "mybooks"
                        st.rerun()

                with col3:
                    if st.button("✨ Summarize", key=f"sum_book_{book_id}", use_container_width=True):
                        st.session_state.current_book = book_id
                        st.session_state.page = "generate_summary"
                        st.rerun()
        else:
            st.markdown("""
            <div class="activity-card">
                <p class="activity-title">No books uploaded yet</p>
                <p class="activity-meta">Click "Upload Book" to get started!</p>
            </div>
            """, unsafe_allow_html=True)
    else:
        st.markdown("""
        <div class="activity-card">
            <p class="activity-title">Unable to load user data</p>
            <p class="activity-meta">Please try logging in again</p>
        </div>
        """, unsafe_allow_html=True)

    # Tips & Information Expander
    with st.expander("💡 Tips & Information", expanded=False):
        st.markdown("""
        <div style="color: var(--text-primary);">
            <h4 style="color: var(--primary-dark); margin-bottom: 1rem;">✨ Version Management Features:</h4>
            <ul style="list-style-type: none; padding-left: 0;">
                <li style="margin-bottom: 0.75rem;">📌 <strong>Version History</strong> — Track all versions of your summaries with timestamps</li>
                <li style="margin-bottom: 0.75rem;">🔄 <strong>Compare Versions</strong> — Side-by-side comparison with diff highlighting</li>
                <li style="margin-bottom: 0.75rem;">⭐ <strong>Favorites</strong> — Mark your best summaries for quick access</li>
                <li style="margin-bottom: 0.75rem;">↩️ <strong>Restore</strong> — Bring back any previous version</li>
            </ul>
        </div>
        """, unsafe_allow_html=True)


def navigate_to(page):
    """Navigate to a specific page"""
    st.session_state.page = page
    st.rerun()
