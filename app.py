# app.py
import streamlit as st
import sys, os
sys.path.append(os.path.abspath(os.path.dirname(__file__)))

from frontend.auth import login_page, registration_page
from frontend.dashboard import dashboard_page
from frontend.upload import upload_page
from frontend.mybooks import mybooks_page
from frontend.summaries import summaries_page
from backend.auth import is_logged_in

if "page" not in st.session_state:
    st.session_state.page = "login"
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False

st.set_page_config(page_title="Intelligent Book Summarizer", layout="wide")

def route():
    page = st.session_state.page
    if page == "login":
        login_page()
    elif page == "register":
        registration_page()
    else:
        # private pages
        if not is_logged_in(st.session_state):
            st.session_state.page = "login"
            st.rerun()
        if page == "dashboard":
            dashboard_page()
        elif page == "upload":
            upload_page()
        elif page == "mybooks":
            mybooks_page()
        elif page == "summaries":
            summaries_page()
        else:
            st.error("Page not implemented: " + page)

if __name__ == "__main__":
    route()
