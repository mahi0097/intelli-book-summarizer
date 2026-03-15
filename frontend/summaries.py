# frontend/summaries.py - UPDATED VERSION

import streamlit as st
import sys
import os
from datetime import datetime
from bson import ObjectId

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from utils.database import get_db
from frontend.helper import get_current_user, is_logged_in
# ✅ Import sidebar CSS from navbar.py
from frontend.navbar import get_sidebar_css


def load_summaries_css():
    # ✅ Inject sidebar CSS from navbar.py
    sidebar_css = get_sidebar_css()
    st.markdown(sidebar_css, unsafe_allow_html=True)

    st.markdown("""
    <style>
    /* ===============================
       THEME COLORS
    =============================== */
    :root {
        --primary: #2563eb;
        --bg-light: #f8fafc;
        --bg-dark: #0f172a;
        --card-light: #ffffff;
        --card-dark: #1e293b;
        --border-light: #e5e7eb;
        --border-dark: #334155;
    }

    /* App background */
    .stApp {
        background: #eef6ff;
    }

    /* Auto dark mode */
    @media (prefers-color-scheme: dark) {
        .stApp {
            background: var(--bg-dark);
            color: #e5e7eb;
        }
    }

    /* Book sections & summary cards */
    [data-testid="stExpander"],
    [data-testid="stMetric"],
    .stTextArea textarea {
        background: var(--card-light);
        border-radius: 14px;
        border: 1px solid var(--border-light);
        padding: 16px;
        box-shadow: 0 10px 25px rgba(0,0,0,0.06);
        transition: all 0.3s ease;
        animation: fadeUp 0.45s ease;
    }

    /* Dark mode cards */
    @media (prefers-color-scheme: dark) {
        [data-testid="stExpander"],
        [data-testid="stMetric"],
        .stTextArea textarea {
            background: var(--card-dark);
            border-color: var(--border-dark);
        }
    }

    /* Hover animation */
    [data-testid="stExpander"]:hover {
        transform: translateY(-5px);
        box-shadow: 0 18px 40px rgba(37,99,235,0.28);
    }

    /* Buttons */
    .main .stButton > button {
        background: linear-gradient(135deg, #2563eb, #1d4ed8);
        color: white;
        border-radius: 12px;
        font-weight: 600;
        border: none;
        transition: all 0.25s ease;
    }

    .main .stButton > button:hover {
        transform: translateY(-3px);
        box-shadow: 0 12px 30px rgba(37,99,235,0.4);
    }

    /* Read full summary textarea */
    .stTextArea textarea {
        font-size: 0.95rem;
        line-height: 1.6;
    }

    /* Metrics */
    [data-testid="stMetric"] {
        padding: 18px;
    }

    /* Divider */
    hr {
        border: none;
        height: 1px;
        background: linear-gradient(to right, transparent, #93c5fd, transparent);
    }

    /* Animation */
    @keyframes fadeUp {
        from {
            opacity: 0;
            transform: translateY(14px);
        }
        to {
            opacity: 1;
            transform: translateY(0);
        }
    }
    </style>
    """, unsafe_allow_html=True)


def show_summaries_page():
    load_summaries_css()

    """Display all user summaries with comparison option"""
    if not is_logged_in():
        st.error("Login required")
        st.session_state.page = "login"
        st.rerun()
        return

    user = get_current_user()
    if not user or "user_id" not in user:
        st.error("Invalid session. Please login again.")
        st.session_state.page = "login"
        st.rerun()
        return

    st.title("📚 My Summaries")

    # Add helpful instructions
    with st.expander("📋 How to compare summary versions", expanded=True):
        st.markdown("""
        ### 🔍 To compare summary versions:
        
        1. **Find a book with multiple versions** below
        2. **Click the "🔍 Compare" button** on any version
        3. **Select two versions** to compare
        4. **View differences** highlighted in color
        
        **Tip:** Create multiple versions by generating summaries with different settings.
        """)

    # Normalize user_id
    user_id = user["user_id"]
    try:
        if isinstance(user_id, str):
            user_obj_id = ObjectId(user_id)
        else:
            user_obj_id = user_id
    except:
        st.error("Invalid user ID format")
        return

    # Get user's summaries
    db = get_db()
    try:
        summaries = list(db.summaries.find({
            "user_id": user_obj_id
        }).sort("created_at", -1))
    except Exception as e:
        st.error(f"Error loading summaries: {str(e)}")
        summaries = []

    if not summaries:
        st.info("""
        📭 **No summaries generated yet.**
        
        **To get started:**
        1. Upload a book from the **Upload Book** page
        2. Generate a summary from the **Generate Summary** page
        3. Create another summary for the same book with different settings
        4. Come back here to compare them!
        """)

        col1, col2 = st.columns(2)
        with col1:
            if st.button("📤 Upload Book", use_container_width=True):
                st.session_state.page = "upload"
                st.rerun()
        with col2:
            if st.button("✨ Generate Summary", use_container_width=True):
                st.session_state.page = "generate_summary"
                st.rerun()
        return

    # Group summaries by book
    books_dict = {}
    for summary in summaries:
        book_id = str(summary.get("book_id", ""))
        if book_id not in books_dict:
            try:
                book = db.books.find_one({"_id": ObjectId(book_id)})
            except:
                book = None
            books_dict[book_id] = {
                "book_info": book,
                "summaries": []
            }
        books_dict[book_id]["summaries"].append(summary)

    # Display summaries by book
    for book_id, data in books_dict.items():
        book = data["book_info"]
        book_summaries = data["summaries"]

        # Sort by version (newest first)
        book_summaries.sort(key=lambda x: x.get("version", 0), reverse=True)

        st.markdown("---")

        if book:
            book_title = book.get("title", "Untitled Book")
            author = book.get("author", "Unknown Author")
            version_count = len(book_summaries)

            col_header1, col_header2 = st.columns([3, 1])

            with col_header1:
                st.subheader(f"📘 {book_title}")
                if author and author != "Unknown Author":
                    st.caption(f"by {author}")
                st.caption(f"{version_count} version{'s' if version_count != 1 else ''}")

            with col_header2:
                if version_count > 1:
                    if st.button("🔍 Compare All",
                                 key=f"compare_all_{book_id}",
                                 use_container_width=True,
                                 type="primary"):
                        st.session_state.selected_book_for_comparison = book_id
                        st.session_state.page = "compare"
                        st.rerun()

        # Display each summary version
        for summary in book_summaries:
            summary_id = str(summary.get("_id", ""))

            with st.expander(f"📄 Version {summary.get('version', 1)}", expanded=False):
                col_sum1, col_sum2 = st.columns([3, 1])

                with col_sum1:
                    created_at = summary.get("created_at", "")
                    if isinstance(created_at, datetime):
                        created_str = created_at.strftime("%Y-%m-%d %H:%M")
                    else:
                        created_str = str(created_at)[:16]

                    badges = []
                    if summary.get("is_favorite"):
                        badges.append("⭐ Favorite")
                    if summary.get("is_default") or summary.get("is_active"):
                        badges.append("✅ Default")

                    st.caption(f"Created: {created_str}")
                    if badges:
                        st.caption(" • ".join(badges))

                    summary_text = summary.get("summary_text", "No content")
                    word_count = len(summary_text.split())

                    if len(summary_text) > 300:
                        st.write(f"{summary_text[:300]}...")
                        st.caption(f"{word_count} words (truncated)")
                        if st.button("📖 Read Full", key=f"read_{summary_id}"):
                            st.text_area("Full Summary",
                                         value=summary_text,
                                         height=200,
                                         key=f"full_{summary_id}")
                    else:
                        st.write(summary_text)
                        st.caption(f"{word_count} words")

                with col_sum2:
                    if st.button("⭐" if not summary.get("is_favorite") else "★",
                                 key=f"fav_{summary_id}",
                                 help="Toggle favorite"):
                        new_status = not summary.get("is_favorite", False)
                        db.summaries.update_one(
                            {"_id": ObjectId(summary_id)},
                            {"$set": {"is_favorite": new_status}}
                        )
                        st.success("Favorite status updated!")
                        st.rerun()

                    if not summary.get("is_default") and not summary.get("is_active"):
                        if st.button("📌",
                                     key=f"default_{summary_id}",
                                     help="Set as default"):
                            try:
                                db.summaries.update_many(
                                    {"book_id": ObjectId(book_id), "user_id": user_obj_id},
                                    {"$set": {"is_default": False, "is_active": False}}
                                )
                                db.summaries.update_one(
                                    {"_id": ObjectId(summary_id)},
                                    {"$set": {"is_default": True, "is_active": True}}
                                )
                                st.success("Set as default version!")
                                st.rerun()
                            except Exception as e:
                                st.error(f"Error: {str(e)}")

                if len(book_summaries) > 1:
                    st.markdown("---")
                    if st.button("🔍 Compare with other versions",
                                 key=f"compare_{summary_id}",
                                 use_container_width=True):
                        st.session_state.selected_book_for_comparison = book_id
                        st.session_state.selected_summary = summary_id
                        st.session_state.page = "compare"
                        st.rerun()

    # Statistics at bottom
    st.markdown("---")
    st.subheader("📊 Summary Statistics")

    total_summaries = len(summaries)
    total_books = len(books_dict)
    favorite_count = sum(1 for s in summaries if s.get("is_favorite"))
    default_count = sum(1 for s in summaries if s.get("is_default") or s.get("is_active"))

    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Total Summaries", total_summaries)
    with col2:
        st.metric("Books with Summaries", total_books)
    with col3:
        st.metric("Favorite Summaries", favorite_count)
    with col4:
        st.metric("Default Summaries", default_count)


# Alias for app.py
def summaries_page():
    show_summaries_page()
