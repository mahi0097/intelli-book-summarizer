import streamlit as st
import re
import sys
import os

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from backend.auth import register_user, login_user


# -------------------------------------------------
# SESSION NAVIGATION
# -------------------------------------------------
if "page" not in st.session_state:
    st.session_state.page = "login"


def go_to(page):
    st.session_state.page = page
    st.rerun()


# -------------------------------------------------
# CUSTOM CSS
# -------------------------------------------------
def add_custom_css():
    st.markdown("""
    <style>
    html, body, [class*="css"] { font-family: 'Inter', sans-serif !important; }
    .stApp { background: linear-gradient(135deg, #eef2f7, #dfe7f3); height: 100vh; }
    .auth-title { text-align: center; font-size: 30px; font-weight: 800; color: #1f2d3d; }
    .auth-subtitle { text-align: center; font-size: 15px; color: #6b7280; margin-bottom: 25px; }
    .stTextInput>div>div>input {
        border-radius: 10px; padding: 12px;
        border: 1px solid #c4c9d1; transition: 0.2s;
    }
    .stTextInput>div>div>input:focus {
        border-color: #4b7bec !important;
        box-shadow: 0 0 0 1px #4b7bec !important;
    }
    .stButton>button {
        width: 100%;
        background: linear-gradient(135deg, #4b7bec, #3867d6);
        color: white; padding: 12px 0;
        border-radius: 10px; border: none;
        font-weight: 600; font-size: 16px;
        transition: 0.25s;
    }
    .stButton>button:hover {
        transform: translateY(-2px);
        box-shadow: 0px 8px 20px rgba(0,0,0,0.15);
    }
    </style>
    """, unsafe_allow_html=True)


add_custom_css()


# -------------------------------------------------
# FRONTEND VALIDATION (extra safety)
# -------------------------------------------------
def validate_registration(name, email, password, confirm_password):
    errors = []

    if not name or len(name) < 2:
        errors.append("Name must be at least 2 characters long.")
    if not re.match(r"^[A-Za-z ]+$", name):
        errors.append("Name must contain only letters and spaces.")

    if not re.match(r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$", email):
        errors.append("Invalid email format.")

    if len(password) < 8:
        errors.append("Password must be at least 8 characters long.")
    if not re.search(r"[A-Z]", password):
        errors.append("Password must contain at least one uppercase letter.")
    if not re.search(r"[a-z]", password):
        errors.append("Password must contain at least one lowercase letter.")
    if not re.search(r"[0-9]", password):
        errors.append("Password must contain at least one number.")
    if not re.search(r"[!@#$%^&*(),.?\":{}|<>]", password):
        errors.append("Password must contain at least one special character.")

    if password != confirm_password:
        errors.append("Passwords do not match.")

    return errors


# -------------------------------------------------
# REGISTRATION PAGE
# -------------------------------------------------
def registration_page():

    st.markdown('<h1 class="auth-title">Create Account</h1>', unsafe_allow_html=True)
    st.markdown('<p class="auth-subtitle">Join the Intelligent Book Summarizer</p>', unsafe_allow_html=True)

    with st.form("register_form"):
        full_name = st.text_input("Full Name")
        email = st.text_input("Email")
        password = st.text_input("Password", type="password")
        confirm_password = st.text_input("Confirm Password", type="password")

        submit_btn = st.form_submit_button("Register")

    if submit_btn:
        errors = validate_registration(full_name, email, password, confirm_password)

        if errors:
            for e in errors:
                st.error(e)
        else:
            with st.spinner("Creating your account..."):
                result = register_user(full_name, email, password)

            if result["success"]:
                st.success("Account created successfully!")
                st.info("Redirecting to login...")
                go_to("login")
            else:
                st.error(result["message"])

    if st.button("Already have an account? Login"):
        go_to("login")


# -------------------------------------------------
# LOGIN PAGE
# -------------------------------------------------
def login_page():

    st.markdown('<h1 class="auth-title">Welcome Back</h1>', unsafe_allow_html=True)
    st.markdown('<p class="auth-subtitle">Login to your Intelligent Book Summarizer</p>', unsafe_allow_html=True)

    with st.form("login_form"):
        email = st.text_input("Email")
        password = st.text_input("Password", type="password")
        remember = st.checkbox("Remember me")
        login_btn = st.form_submit_button("Login")

    if login_btn:
        with st.spinner("Checking credentials..."):
            response = login_user(email, password, identifier=email)

        if response["success"]:
            user = response["user"]

            st.success("Login successful!")

            # Save session state
            st.session_state.logged_in = True
            st.session_state.user_id = user["user_id"]
            st.session_state.user_name = user["name"]
            st.session_state.user_email = user["email"]
            st.session_state.user_role = user["role"]

            # Redirect to dashboard (later)
            # go_to("dashboard")

        else:
            st.error(response["message"])

    if st.button("Create a new account"):
        go_to("register")


if st.session_state.page == "login":
    login_page()
else:
    registration_page()
