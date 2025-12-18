# frontend/dashboard.py

import streamlit as st
import os, sys
from datetime import datetime, timedelta
from bson import ObjectId

# Import backend & database
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from backend.auth import is_logged_in, get_current_user, logout as backend_logout
from utils.database import db



def time_ago(timestamp):
    if not timestamp:
        return "—"

    now = datetime.utcnow()
    diff = now - timestamp

    if diff < timedelta(minutes=1):
        return "Just now"
    if diff < timedelta(hours=1):
        return f"{diff.seconds // 60} minutes ago"
    if diff < timedelta(days=1):
        return f"{diff.seconds // 3600} hours ago"
    if diff < timedelta(days=7):
        return f"{diff.days} days ago"

    return timestamp.strftime("%b %d, %Y")


# -------------------------------------------------------
# MAIN DASHBOARD FUNCTION
# -------------------------------------------------------
def dashboard_page():

    # 🔐 Must be logged in
    if not is_logged_in(st.session_state):
        st.error("Please login first.")
        st.session_state.page = "login"
        st.rerun()
        return

    user = get_current_user(st.session_state)

    # ---------------------------------------------------
    # LEFT SIDEBAR NAVIGATION
    # ---------------------------------------------------
    with st.sidebar:
        st.title("📚 Menu")
        st.write(f"👋 Hello, **{user['name']}**")
        st.markdown("---")

        if st.button("🏠 Dashboard"):
            st.session_state.page = "dashboard"
            st.rerun()

        if st.button("📤 Upload Book"):
            st.session_state.page = "upload"
            st.rerun()

        if st.button("📘 My Books"):
            st.session_state.page = "mybooks"
            st.rerun()

        if st.button("📝 Summaries"):
            st.session_state.page = "summaries"
            st.rerun()

        st.markdown("---")
        if st.button("🚪 Logout"):
            backend_logout(st.session_state)
            st.session_state.page = "login"
            st.rerun()

    # ---------------------------------------------------
    # MAIN CONTENT
    # ---------------------------------------------------
    st.title(f" Dashboard Overview")
    st.write(f"Welcome back, **{user['name']}**!")
    st.markdown("---")

    try:
        uid = ObjectId(user["user_id"])
    except:
        uid = user["user_id"]

    mongo = db

    total_books = mongo.books.count_documents({"user_id": uid})
    total_summaries = mongo.summaries.count_documents({"user_id": uid})

    # ---------------------------------------------------
    # QUICK STATS CARDS
    # ---------------------------------------------------
    st.subheader("Quick Stats")

    col1, col2, col3 = st.columns(3)

    col1.metric("Books Uploaded", total_books)
    col2.metric("Summaries Generated", total_summaries)

    last_book = mongo.books.find_one({"user_id": uid}, sort=[("uploaded_at", -1)])
    last_summary = mongo.summaries.find_one({"user_id": uid}, sort=[("created_at", -1)])

    latest_activity = None

    if last_book:
        latest_activity = last_book.get("uploaded_at")

    if last_summary and (not latest_activity or last_summary["created_at"] > latest_activity):
        latest_activity = last_summary["created_at"]

    col3.metric("Last Activity", time_ago(latest_activity))
    st.markdown("---")

    # ---------------------------------------------------
    # RECENT ACTIVITY SECTION
    # ---------------------------------------------------
    st.subheader(" Recent Activity")

    recent_books = list(mongo.books.find({"user_id": uid}).sort("uploaded_at", -1).limit(5))
    recent_summaries = list(mongo.summaries.find({"user_id": uid}).sort("created_at", -1).limit(5))

    if not recent_books and not recent_summaries:
        st.info("No recent activity yet. Upload your first book!")
    else:
        for b in recent_books:
            st.write(f"📘 Uploaded **{b['title']}** — {time_ago(b.get('uploaded_at'))}")

        for s in recent_summaries:
            st.write(f"📝 Summary generated for book ID **{s['book_id']}** — {time_ago(s.get('created_at'))}")

    st.markdown("---")

    # ---------------------------------------------------
    # QUICK ACTION BUTTONS
    # ---------------------------------------------------
    st.subheader(" Quick Actions")

    c1, c2 = st.columns(2)

    if c1.button("📤 Upload New Book"):
        st.session_state.page = "upload"
        st.rerun()

    if c2.button("📘 View My Books"):
        st.session_state.page = "mybooks"
        st.rerun()

    c3, c4 = st.columns(2)

    if c3.button("📝 View Summaries"):
        st.session_state.page = "summaries"
        st.rerun()

    if c4.button("🚪 Logout"):
        backend_logout(st.session_state)
        st.session_state.page = "login"
        st.rerun()
