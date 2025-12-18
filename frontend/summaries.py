# frontend/summaries.py
import streamlit as st
import sys, os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from backend.auth import is_logged_in, get_current_user
from utils.database import db

def summaries_page():
    if not is_logged_in(st.session_state):
        st.error("Login required")
        st.session_state.page = "login"
        st.rerun()
        return
    user = get_current_user(st.session_state)
    st.title(" Summaries")
    mongo = db
    uid = user["user_id"]
    sums = list(mongo.summaries.find({"user_id": uid}).sort("created_at", -1))
    if not sums:
        st.info("No summaries yet.")
        return
    for s in sums:
        st.subheader(f"Summary of book_id: {s.get('book_id')}")
        st.write(s.get("summary_text"))
        if st.button("Download summary", key=f"dl_{str(s.get('_id'))}"):
            st.download_button("Download summary", s.get("summary_text"), file_name=f"summary_{str(s.get('_id'))}.txt")
