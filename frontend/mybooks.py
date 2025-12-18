# frontend/mybooks.py
import streamlit as st
import sys, os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from backend.auth import is_logged_in, get_current_user
from utils.database import db, delete_book

def mybooks_page():
    if not is_logged_in(st.session_state):
        st.error("Login required")
        st.session_state.page = "login"
        st.rerun()
        return
    user = get_current_user(st.session_state)
    st.title("📚 My Books")
    mongo = db
    uid = user["user_id"]
    books = list(mongo.books.find({"user_id": uid}).sort("uploaded_at", -1))
    if not books:
        st.info("No books uploaded.")
        return
    for b in books:
        b_id = str(b.get("_id"))
        st.subheader(b.get("title", "Untitled"))
        st.write(f"Status: {b.get('status')}")
        st.write(f"Words: {b.get('word_count', 0)}, Chars: {b.get('char_count', 0)}")
        if st.button("View raw text", key=f"raw_{b_id}"):
            st.text_area("Raw text", value=b.get("raw_text",""), height=300)
        s = db.summaries.find_one({"book_id": b.get("_id")})
        if s:
            st.write("Summary preview:")
            st.write(s.get("summary_text")[:800])
        cols = st.columns([1,1,1])
        if cols[0].button("Generate/Regenerate Summary", key=f"gen_{b_id}"):
            st.session_state._regenerate_book = b_id
            st.experimental_rerun()
        if cols[1].button("Download file", key=f"dl_{b_id}"):
            fp = b.get("file_path")
            if fp and os.path.exists(fp):
                with open(fp, "rb") as fh:
                    st.download_button("Download", fh, file_name=os.path.basename(fp))
        if cols[2].button("Delete", key=f"del_{b_id}"):
            try:
                delete_book(b_id)
                if b.get("file_path") and os.path.exists(b.get("file_path")):
                    os.remove(b.get("file_path"))
                st.success("Deleted")
                st.experimental_rerun()
            except Exception as e:
                st.error(f"Delete failed: {e}")
