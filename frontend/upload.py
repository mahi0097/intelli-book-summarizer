import streamlit as st
import os
import sys
import time
import asyncio
from datetime import datetime
from bson import ObjectId

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from frontend.helper import is_logged_in, get_current_user, clear_user_session

from backend.text_extractor import process_book
from backend.summary_orchestrator import generate_summary
from utils.database import (
    create_book,
    update_book_status,
    db,
    delete_book_and_summary
)
from utils.error_handler import error_handler, FileProcessingError, RateLimitError
from utils.validators import InputValidator
from frontend.error_ui import safe_execute, display_error_ui

def load_upload_css():
    st.markdown("""
    <style>
    /* ===============================
       COLORS
    =============================== */
    :root {
        --primary: #2563eb;
        --bg-light: #f8fafc;
        --bg-dark: #0f172a;
        --card-light: #ffffff;
        --card-dark: #1e293b;
    }

    /* Page background */
    .stApp {
        background: #eef6ff;
    }
    /* Dark mode auto */
    @media (prefers-color-scheme: dark) {
        .stApp {
            background: var(--bg-dark);
            color: #e5e7eb;
        }
    }

    /* Upload cards / sections */
    .upload-card,
    [data-testid="stFileUploader"],
    [data-testid="stExpander"],
    [data-testid="stMetric"] {
        background: var(--card-light);
        border-radius: 14px;
        padding: 16px;
        border: 1px solid #e5e7eb;
        box-shadow: 0 10px 30px rgba(0,0,0,0.06);
        transition: all 0.3s ease;
        animation: fadeUp 0.5s ease;
    }

    /* Dark mode cards */
    @media (prefers-color-scheme: dark) {
        .upload-card,
        [data-testid="stFileUploader"],
        [data-testid="stExpander"],
        [data-testid="stMetric"] {
            background: var(--card-dark);
            border-color: #334155;
        }
    }

    /* Hover animation */
    [data-testid="stFileUploader"]:hover,
    [data-testid="stExpander"]:hover {
        transform: translateY(-5px);
        box-shadow: 0 18px 40px rgba(37,99,235,0.25);
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

    /* Progress bar */
    .stProgress > div > div {
        background-color: #2563eb;
    }

    /* Divider */
    .main hr {
        border: none;
        height: 1px;
        background: linear-gradient(to right, transparent, #93c5fd, transparent);
    }

    /* Animation */
    @keyframes fadeUp {
        from {
            opacity: 0;
            transform: translateY(12px);
        }
        to {
            opacity: 1;
            transform: translateY(0);
        }
    }
    </style>
    """, unsafe_allow_html=True)


UPLOAD_DIR = "data/uploads/"
MAX_FILE_SIZE_MB = 10


def top_header(user):
    col1, col2, col3 = st.columns([3, 2, 1])

    with col1:
        st.markdown("## 📚 Intelligent Book Summarizer")

    with col3:
        st.write(f"👤 **{user['name']}**")
        if st.button("🚪 Logout"):
            clear_user_session()
            st.session_state.page = "login"
            st.rerun()



def sidebar_nav():
    with st.sidebar:
        st.title(" Navigation")
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


def require_login():
    if not is_logged_in():

        st.error("You must log in first.")
        st.session_state.page = "login"
        st.rerun()
    return get_current_user()


def validate_file(uploaded_file):
    if uploaded_file is None:
        return "No file selected."

    size_mb = uploaded_file.size / (1024 * 1024)
    if size_mb > MAX_FILE_SIZE_MB:
        return "File exceeds 10MB limit."

    ext = uploaded_file.name.split(".")[-1].lower()
    if ext not in ("txt", "pdf", "docx"):
        return "Unsupported file type."

    return None


def show_upload_page():
    load_upload_css()
    user = require_login()

    st.markdown("## 📤 Upload Book")

    uploaded_file = st.file_uploader("Choose a file", type=["txt", "pdf", "docx"])

    if uploaded_file:
        error = validate_file(uploaded_file)
        if error:
            st.error(error)
            return

        filename = uploaded_file.name
        title = filename.rsplit(".", 1)[0]

        author = st.text_input("Author (optional)")
        chapter = st.text_input("Chapter (optional)")

        if st.button("📤 Upload & Extract"):
            os.makedirs(UPLOAD_DIR, exist_ok=True)
            file_path = os.path.join(UPLOAD_DIR, filename)

            with open(file_path, "wb") as f:
                f.write(uploaded_file.getbuffer())

            book_id = create_book(
                user_id=user["user_id"],
                title=title,
                author=author,
                chapter=chapter,
                file_path=file_path,
                raw_text=""
            )

            update_book_status(book_id, "extracting")

            with st.spinner("Extracting text..."):
                extract = process_book(book_id, file_path)

            if not extract["success"]:
                st.error("Text extraction failed.")
                update_book_status(book_id, "failed")
                return

            st.success("✔ Text extracted successfully!")
            st.session_state.latest_book_id = str(book_id)
            st.rerun()

    st.markdown("---")
    st.subheader("Generate Summary")

    if "latest_book_id" in st.session_state:
        bid = st.session_state.latest_book_id
        book = db.books.find_one({"_id": ObjectId(bid)})

        if book and book["status"] == "text_extracted":
            
            # Summary options
            col1, col2 = st.columns(2)
            with col1:
                length = st.selectbox("Summary Length", ["short", "medium", "long"], index=1)
            with col2:
                style = st.selectbox("Style", ["paragraph", "bullets"], index=1)
            
            if st.button("🚀 Start AI Summarization"):
                update_book_status(bid, "processing")

                # Create progress containers
                progress_bar = st.progress(0)
                progress_text = st.empty()
                status_container = st.empty()
                summary_container = st.empty()
                error_container = st.empty()

                try:
                    # Run summarization
                    status_container.info("🚀 Starting summarization process...")
                    progress_bar.progress(10)
                    progress_text.write("**Progress:** 10% - Initializing summarization...")
                    
                    # IMPORTANT FIX: Handle async properly for Streamlit
                    try:
                        # Try to get existing event loop
                        loop = asyncio.get_event_loop()
                    except RuntimeError:
                        # Create new event loop if none exists
                        loop = asyncio.new_event_loop()
                        asyncio.set_event_loop(loop)
                    
                    # Run the async function
                    summary_result = loop.run_until_complete(
                        generate_summary(
                            book_id=bid,
                            user_id=user["user_id"],
                            summary_options={
                                "length": length,
                                "style": style
                            }
                        )
                    )
                    
                    # Update progress to 50%
                    progress_bar.progress(50)
                    progress_text.write("**Progress:** 50% - Summarization complete, processing results...")
                    
                    # Check if summary was successful
                    if summary_result.get("success"):
                        # Extract summary text
                        summary_text = summary_result.get("summary", "")
                        if not summary_text:
                            # Try to get from database
                            summary_doc = db.summaries.find_one({"book_id": ObjectId(bid)})
                            if summary_doc:
                                summary_text = summary_doc.get("summary_text") or summary_doc.get("summary", "")
                        
                        if summary_text:
                            # Update progress to 100%
                            progress_bar.progress(100)
                            progress_text.write("**Progress:** 100% - Summary ready!")
                            status_container.success("✅ Summary generated successfully!")
                            
                            # Display summary
                            summary_container.markdown("### 📘 Summary")
                            summary_container.write(summary_text)
                            
                            # Update book status
                            update_book_status(bid, "completed")
                            
                            # Show stats if available
                            if "stats" in summary_result:
                                with st.expander("📊 Summary Statistics"):
                                    stats = summary_result["stats"]
                                    st.write(f"**Original length:** {stats.get('original_length', 'N/A')} words")
                                    st.write(f"**Summary length:** {stats.get('summary_length', 'N/A')} words")
                                    st.write(f"**Compression ratio:** {stats.get('compression_ratio', 'N/A')}%")
                                    st.write(f"**Processing time:** {stats.get('processing_time', 'N/A')} seconds")
                        else:
                            error_container.error("❌ Summary was generated but text is empty.")
                            update_book_status(bid, "failed")
                    else:
                        error_message = summary_result.get('error', 'Unknown error')
                        error_container.error(f"❌ Summarization failed: {error_message}")
                        update_book_status(bid, "failed")
                        
                        # Store error in database for debugging
                        db.books.update_one(
                            {"_id": ObjectId(bid)},
                            {"$set": {"error_message": error_message}}
                        )

                except Exception as e:
                    error_msg = f"❌ Error during summarization: {str(e)}"
                    error_container.error(error_msg)
                    update_book_status(bid, "failed")
                    
                    # Store error in database
                    db.books.update_one(
                        {"_id": ObjectId(bid)},
                        {"$set": {"error_message": str(e)}}
                    )
                
                # Add refresh button
                st.markdown("---")
                if st.button("🔄 Refresh Page"):
                    st.rerun()

    st.markdown("---")
    st.subheader("📚 Upload History")
    
    # Add filtering options
    col1, col2, col3 = st.columns([2, 2, 1])
    
    with col1:
        sort_option = st.selectbox(
            "Sort by",
            ["Newest First", "Oldest First", "Title A-Z", "Title Z-A"]
        )
    
    with col2:
        status_filter = st.selectbox(
            "Filter by Status",
            ["All", "uploaded", "extracting", "text_extracted", "processing", "completed", "failed"]
        )
    
    with col3:
        st.write("")  # Spacing
        if st.button("🔄 Refresh List"):
            st.rerun()
    
    # Build query
    query = {"user_id": ObjectId(user["user_id"])}
    if status_filter != "All":
        query["status"] = status_filter
    
    # Get books based on query
    books = list(db.books.find(query))
    
    # Apply sorting
    if sort_option == "Newest First":
        books.sort(key=lambda x: x.get("uploaded_at", datetime.min), reverse=True)
    elif sort_option == "Oldest First":
        books.sort(key=lambda x: x.get("uploaded_at", datetime.max))
    elif sort_option == "Title A-Z":
        books.sort(key=lambda x: x.get("title", "").lower())
    elif sort_option == "Title Z-A":
        books.sort(key=lambda x: x.get("title", "").lower(), reverse=True)
    
    if not books:
        st.info("No books uploaded yet.")
        return
    
    # Display books with delete functionality
    for book in books:
        bid = str(book["_id"])
        
        # Create a unique key for each book's expander
        with st.expander(f"📘 {book['title']} - Status: {book['status'].replace('_', ' ').title()}"):
            col1, col2 = st.columns([3, 1])
            
            with col1:
                st.write(f"**Author:** {book.get('author', 'Not specified')}")
                st.write(f"**Uploaded:** {book.get('uploaded_at', 'N/A').strftime('%Y-%m-%d %H:%M') if isinstance(book.get('uploaded_at'), datetime) else 'N/A'}")
                st.write(f"**Word Count:** {book.get('word_count', 'N/A')}")
                st.write(f"**File Type:** {book.get('file_type', 'N/A')}")
                
                # Show error message if failed
                if book.get("status") == "failed" and book.get("error_message"):
                    st.error(f"**Error:** {book['error_message']}")
            
            with col2:
                # Create a container for buttons to prevent re-render issues
                btn_col1, btn_col2 = st.columns(2)
                
                with btn_col1:
                    if st.button("📖 View", key=f"view-btn-{bid}"):
                        st.session_state[f"show_summary_{bid}"] = True
                
                with btn_col2:
                    # Delete button with confirmation
                    if st.button("🗑️ Delete", key=f"delete-btn-{bid}", type="secondary"):
                        st.session_state[f"confirm_delete_{bid}"] = True
        
        # Show summary if view button was clicked
        if st.session_state.get(f"show_summary_{bid}", False):
            st.markdown(f"#### Summary for {book['title']}:")
            
            summary = db.summaries.find_one({"book_id": ObjectId(bid)})
            if summary:
                summary_text = summary.get("summary_text") or summary.get("summary")
                if summary_text:
                    st.write(summary_text)
                    
                    # Show summary metadata if available
                    if "summary_length" in summary:
                        st.caption(f"Summary length: {summary['summary_length']} words")
                    if "created_at" in summary:
                        st.caption(f"Generated on: {summary['created_at'].strftime('%Y-%m-%d %H:%M')}")
                else:
                    st.warning("Summary exists but text is empty.")
            else:
                st.warning("No summary available for this book.")
            
            if st.button("Close Summary", key=f"close-{bid}"):
                st.session_state[f"show_summary_{bid}"] = False
                st.rerun()
        
        # Show delete confirmation (outside expander but after it)
        if st.session_state.get(f"confirm_delete_{bid}", False):
            st.warning(f"Are you sure you want to delete '{book['title']}' and its summary?")
            col_yes, col_no = st.columns(2)
            with col_yes:
                if st.button("✅ Yes, Delete", key=f"confirm-yes-{bid}"):
                    result = delete_book_and_summary(bid)
                    if result:
                        st.success("Book deleted successfully!")
                        # Clear session states
                        for key in [f"show_summary_{bid}", f"confirm_delete_{bid}"]:
                            if key in st.session_state:
                                del st.session_state[key]
                        time.sleep(1)
                        st.rerun()
                    else:
                        st.error("Failed to delete book.")
            with col_no:
                if st.button("❌ Cancel", key=f"confirm-no-{bid}"):
                    st.session_state[f"confirm_delete_{bid}"] = False
                    st.rerun()
    
    # Show statistics
    st.markdown("---")
    st.subheader("📊 Statistics")
    col_stat1, col_stat2, col_stat3 = st.columns(3)
    
    total_books = len(books)
    completed_books = len([b for b in books if b.get("status") == "completed"])
    total_words = sum([b.get("word_count", 0) for b in books if isinstance(b.get("word_count"), (int, float))])
    
    with col_stat1:
        st.metric("Total Books", total_books)
    with col_stat2:
        st.metric("Completed Summaries", completed_books)
    with col_stat3:
        st.metric("Total Words", f"{total_words:,}")
