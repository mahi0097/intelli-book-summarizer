# frontend/auth.py
import streamlit as st
import re
import sys, os
from utils.error_handler import error_handler, ValidationError, RateLimitError
from utils.validators import InputValidator
from frontend.error_ui import safe_execute, validate_form_inputs
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


def login_page():
    st.subheader("🔐 Login")

    with st.form("login_form"):
        email = st.text_input("Email")
        password = st.text_input("Password", type="password")
        submit = st.form_submit_button("Login")

    if submit:
        res = login_user(email, password)

        if not res.get("success"):
            st.error(res.get("message", "Invalid credentials"))
            return

        user = res["user"]
        st.session_state.logged_in = True
        st.session_state.user_id = user["user_id"]
        st.session_state.username = user["name"]
        st.session_state.email = user["email"]
        st.session_state.role = user.get("role", "user")
        st.session_state.page = "dashboard"

        st.success("Login successful!")
        st.rerun()


def registration_page():
    st.subheader("📝 Create Account")

    with st.form("register_form"):
        name = st.text_input("Full Name")
        email = st.text_input("Email")
        password = st.text_input("Password", type="password")
        confirm = st.text_input("Confirm Password", type="password")
        submit = st.form_submit_button("Register")

    if submit:
        errors = validate_registration(name, email, password, confirm)
        if errors:
            for err in errors:
                st.error(err)
            return

        res = register_user(name.strip(), email.strip(), password)
        if res.get("success"):
            st.success("Account created successfully. Please login.")
            st.session_state.page = "login"
            st.rerun()
        else:
            st.error(res.get("message", "Registration failed"))


# ✅ THIS FUNCTION WAS MISSING
@error_handler
def show_auth_page(mode="login"):
    """Authentication page with validation"""
    
    st.title("🔐 " + ("Login" if mode == "login" else "Register"))
    
    # Check rate limiting
    from utils.error_handler import api_limiter
    ip_address = st.experimental_get_query_params().get("ip", ["unknown"])[0]
    
    if not api_limiter.is_allowed(ip_address):
        retry_after = api_limiter.get_retry_after(ip_address)
        raise RateLimitError(
            "Too many authentication attempts",
            retry_after
        )
    
    # Create form
    with st.form("auth_form"):
        if mode == "register":
            name = st.text_input("Full Name", placeholder="Enter your name")
        
        email = st.text_input("Email Address", placeholder="you@example.com")
        password = st.text_input("Password", type="password")
        
        if mode == "register":
            confirm_password = st.text_input("Confirm Password", type="password")
        
        submitted = st.form_submit_button(
            "Login" if mode == "login" else "Register",
            type="primary",
            use_container_width=True
        )
    
    if submitted:
        # Validate inputs
        form_data = {"email": email, "password": password}
        if mode == "register":
            form_data["name"] = name
            form_data["confirm_password"] = confirm_password
        
        is_valid, errors = validate_form_inputs(form_data)
        
        if not is_valid:
            for field, error in errors.items():
                st.error(f"{field}: {error}")
            return
        
        # Additional validations
        if mode == "register":
            if password != confirm_password:
                st.error("Passwords do not match")
                return
            
            if not name.strip():
                st.error("Name is required")
                return
        
        # Execute authentication
        if mode == "login":
            safe_execute(
                lambda: perform_login(email, password),
                success_message="✅ Login successful!"
            )
        else:
            safe_execute(
                lambda: perform_registration(name, email, password),
                success_message="✅ Registration successful! Please login."
            )

@error_handler
def perform_login(email, password):
    """Perform login with error handling"""
    from utils.database import get_user_by_email, verify_password
    
    # Validate email format
    is_valid, error_msg = InputValidator.validate_email(email)
    if not is_valid:
        raise ValidationError(error_msg, field="email")
    
    # Get user
    user = get_user_by_email(email)
    if not user:
        raise ValidationError("Invalid email or password", field="email")
    
    # Check if account is active
    if not user.get('is_active', True):
        raise ValidationError("Account is deactivated. Contact support.", field="email")
    
    # Verify password
    if not verify_password(user['password_hash'], password):
        raise ValidationError("Invalid email or password", field="password")
    
    # Set session state
    st.session_state.logged_in = True
    st.session_state.user = user
    st.session_state.user_id = user['_id']
    st.session_state.username = user.get('name', 'User')
    st.session_state.role = user.get('role', 'user')
    st.session_state.page = "dashboard"
    
    # Log successful login
    from utils.error_handler import ErrorLogger
    ErrorLogger.log_user_action(
        "user_login",
        user_id=user['_id'],
        success=True
    )