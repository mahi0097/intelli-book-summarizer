# frontend/upload.py

import streamlit as st
import os, sys, time
from bson import ObjectId

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from backend.auth import is_logged_in, get_current_user, logout as backend_logout
from backend.text_extractor import process_book
from backend.summarizer import generate_summary
from utils.database import (
    create_book,
    update_book_status,
    update_book_text,
    create_summary,
    db
)

UPLOAD_DIR = "data/uploads/"
MAX_FILE_SIZE_MB = 10


def top_header(user):
    col1, col2, col3 = st.columns([3, 2, 1])

    with col1:
        st.markdown("## 📚 Intelligent Book Summarizer")

    with col2:
        st.write("")

    with col3:
        st.write(f"👤 **{user['name']}**")
        if st.button("Logout"):
            backend_logout(st.session_state)
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
    if not is_logged_in(st.session_state):
        st.error("You must log in first.")
        st.session_state.page = "login"
        st.rerun()
    return get_current_user(st.session_state)


def validate_file(uploaded_file):
    if uploaded_file is None:
        return "No file selected."

    size_mb = uploaded_file.size / (1024 * 1024)
    if size_mb > MAX_FILE_SIZE_MB:
        return f"File too large: {size_mb:.2f}MB. Limit is 10MB."

    ext = uploaded_file.name.split(".")[-1].lower()
    if ext not in ("txt", "pdf", "docx"):
        return "Unsupported file type."

    return None


def upload_page():
    user = require_login()

    # Add UI header + navigation
    top_header(user)
    sidebar_nav()

    st.markdown("## 📤 Upload Book")
    st.write("Supported formats: **PDF, DOCX, TXT**")

    uploaded_file = st.file_uploader("Choose a file", type=["txt", "pdf", "docx"])

    if uploaded_file:
        error = validate_file(uploaded_file)
        if error:
            st.error(error)
            return

        filename = uploaded_file.name
        suggested_title = filename.rsplit(".", 1)[0]

        st.subheader("Book Details")
        title = st.text_input("Title", value=suggested_title)
        author = st.text_input("Author (optional)")
        chapter = st.text_input("Chapter (optional)")

        if st.button("📤 Upload & Extract"):
            os.makedirs(UPLOAD_DIR, exist_ok=True)
            file_path = os.path.join(UPLOAD_DIR, filename)

            with open(file_path, "wb") as f:
                f.write(uploaded_file.getbuffer())

            # Create book record
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
                st.error("Extraction failed.")
                return

            data = extract["extraction"]
            st.success("✔ Text successfully extracted!")

            st.info(f"**Words:** {data['word_count']} | **Characters:** {data['char_count']}")

            st.session_state.latest_book_id = book_id
            st.rerun()

    st.markdown("---")
    st.subheader(" Summary")

    # SHOW SUMMARY BUTTON FOR LATEST BOOK
    if "latest_book_id" in st.session_state:
        bid = st.session_state.latest_book_id
        book = db.books.find_one({"_id": ObjectId(bid)})

        if book and book["status"] == "text_extracted":
            if st.button("✨ Generate Summary"):
                update_book_status(bid, "summarizing")

                with st.spinner("Generating summary..."):
                    summary_text = generate_summary(bid)

                create_summary(
                    book_id=bid,
                    user_id=user["user_id"],
                    summary_text=summary_text,
                    summary_length="short",
                    summary_style="paragraphs",
                    chunk_summaries=[summary_text],
                    processing_time=0.2
                )

                update_book_status(bid, "completed")
                st.success("✔ Summary generated!")

                # Display Clean Summary
                st.markdown("###  Summary Output")
                st.write(summary_text)  # clean, no padding
                st.rerun()

    st.markdown("---")
    st.subheader(" Upload History")

    mongo = db
    books = list(
        mongo.books.find({"user_id": ObjectId(user["user_id"])}).sort("uploaded_at", -1)
    )

    if not books:
        st.info("No books uploaded yet.")
        return

    for book in books:
        bid = str(book["_id"])

        st.write(f"###  {book['title']}")
        st.caption(f"Status: **{book['status']}**")
        st.caption(f"Words: {book.get('word_count', '—')} | Characters: {book.get('char_count', '—')}")

        c1, c2, c3 = st.columns([1,1,1])

        with c1:
            if st.button(" Summary", key=f"sumb-{bid}"):
                summary = db.summaries.find_one({"book_id": ObjectId(bid)})
                if summary:
                    st.markdown("### Summary Output")
                    st.write(summary["summary_text"])
                else:
                    st.warning("No summary available.")

        with c2:
            if st.button("🗑 Delete", key=f"del-{bid}"):
                db.books.delete_one({"_id": ObjectId(bid)})
                db.summaries.delete_many({"book_id": ObjectId(bid)})
                st.success("Deleted!")
                st.rerun()
