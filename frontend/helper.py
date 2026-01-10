# frontend/helpers.py
import streamlit as st
from datetime import datetime


def is_logged_in():
    """
    Check if user is logged in using Streamlit session state
    """
    return st.session_state.get("logged_in", False)


def get_current_user():
    """
    Get current logged-in user details from session state
    """
    if not is_logged_in():
        return None

    return {
        "user_id": st.session_state.get("user_id"),
        "email": st.session_state.get("email"),   # FIXED
        "name": st.session_state.get("name", "User"),
        "role": st.session_state.get("role", "user"),
        "created_at": st.session_state.get("created_at"),
        "last_activity": st.session_state.get("last_activity", datetime.utcnow())
    }


def set_user_session(user_data):
    """
    Set user session after login / registration
    """
    st.session_state.logged_in = True
    st.session_state.user_id = user_data.get("user_id")
    st.session_state.email = user_data.get("email")
    st.session_state.name = user_data.get("name", "User")
    st.session_state.role = user_data.get("role", "user")
    st.session_state.token = user_data.get("token")
    st.session_state.created_at = user_data.get("created_at", datetime.utcnow())
    st.session_state.last_activity = datetime.utcnow()


def clear_user_session():
    """
    Clear user session safely
    """
    keys_to_remove = [
        "logged_in",
        "user_id",
        "email",
        "name",
        "role",
        "token",
        "created_at",
        "last_activity"
    ]

    for key in keys_to_remove:
        if key in st.session_state:
            del st.session_state[key]

    st.session_state.logged_in = False


def require_login():
    """
    Decorator for pages that require login
    """
    def decorator(func):
        def wrapper(*args, **kwargs):
            if not is_logged_in():
                st.error("🔐 Please login to access this page")
                st.session_state.page = "login"
                st.rerun()
                return
            return func(*args, **kwargs)
        return wrapper
    return decorator
