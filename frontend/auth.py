# frontend/auth.py
import streamlit as st
import re
import sys, os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from backend.auth import register_user, login_user

def validate_registration(name, email, password, confirm):
    errors = []
    if len(name.strip()) < 2:
        errors.append("Name must be at least 2 characters")
    if not re.match(r"^[A-Za-z\s]+$", name.strip()):
        errors.append("Name must contain only letters")
    if not re.match(r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[A-Za-z]{2,}$", email):
        errors.append("Invalid email format")
    if len(password) < 8:
        errors.append("Password must be at least 8 characters")
    if password != confirm:
        errors.append("Passwords do not match")
    return errors

def setup_page():
    st.set_page_config(page_title="Book Summarizer - Auth", layout="centered")

def login_page():
    setup_page()
    st.title(" Login")
    st.write("Enter your credentials to continue.")
    with st.form("login_form"):
        email = st.text_input("Email", key="login_email")
        password = st.text_input("Password", type="password", key="login_password")
        submit = st.form_submit_button("Login")
    if submit:
        if not email or not password:
            st.error("Please fill both fields.")
        else:
            res = login_user(email, password, identifier=email)
            if res.get("success"):
                user = res["user"]
                st.session_state.logged_in = True
                st.session_state.user_id = user["user_id"]
                st.session_state.user_name = user["name"]
                st.session_state.user_email = user["email"]
                st.session_state.user_role = user["role"]
                st.session_state.page = "dashboard"
                st.success("Login successful!")
                st.rerun()
            else:
                st.error(res.get("message", "Invalid credentials"))

    st.write("---")
    if st.button("Create Account"):
        st.session_state.page = "register"
        st.rerun()

def registration_page():
    setup_page()
    st.title(" Create Account")
    st.write("Register a new account.")
    with st.form("reg_form"):
        name = st.text_input("Full name", key="reg_name")
        email = st.text_input("Email", key="reg_email")
        password = st.text_input("Password", type="password", key="reg_password")
        confirm = st.text_input("Confirm Password", type="password", key="reg_confirm")
        submit = st.form_submit_button("Register")
    if submit:
        errs = validate_registration(name or "", email or "", password or "", confirm or "")
        if errs:
            for e in errs:
                st.error(e)
        else:
            res = register_user(name.strip(), email.strip(), password)
            if res.get("success"):
                st.success("Account created successfully. Please login.")
                st.session_state.page = "login"
                st.rerun()
            else:
                st.error(res.get("message", "Registration failed"))

    st.write("---")
    if st.button("Back to Login"):
        st.session_state.page = "login"
        st.rerun()
