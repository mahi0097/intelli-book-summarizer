import base64
import os
import re
import sys
from datetime import datetime
from pathlib import Path

import requests
import streamlit as st

from frontend.api_config import API_BASE_URL, LOGIN_ENDPOINTS, REGISTER_ENDPOINTS

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
LOCAL_AUTH_IMPORT_ERROR = None

try:
    from backend.auth import register_user, login_user
except ImportError as e:
    LOCAL_AUTH_IMPORT_ERROR = str(e)
    register_user = None
    login_user = None


def _post_to_backend(candidate_paths, payload):
    """Try posting to the deployed backend using a list of candidate endpoints."""
    last_error = None

    for path in candidate_paths:
        url = f"{API_BASE_URL.rstrip('/')}{path}"
        try:
            response = requests.post(url, json=payload, timeout=15)
            if response.ok:
                return response.json()

            # If the endpoint exists but rejected the request, surface that message.
            if response.status_code not in (404, 405):
                try:
                    error_data = response.json()
                    message = error_data.get("message") or error_data.get("detail") or response.text
                except Exception:
                    message = response.text or f"HTTP {response.status_code}"

                lowered_message = str(message).lower()
                content_type = response.headers.get("content-type", "").lower()
                is_html_error = (
                    "text/html" in content_type
                    or "<html" in lowered_message
                    or "<title>" in lowered_message
                )

                # Some hosted backends return generic HTML 403/401 pages for blocked
                # requests. Treat those as an unavailable remote auth backend so the
                # app can fall back to the local auth implementation.
                if response.status_code in (401, 403) and is_html_error:
                    last_error = f"Remote auth blocked request with HTTP {response.status_code}"
                    continue

                return {"success": False, "message": message}
        except requests.RequestException as exc:
            last_error = str(exc)

    if last_error:
        return {"success": False, "message": f"Remote backend unavailable: {last_error}"}
    return {"success": False, "message": "No matching auth endpoint found on deployed backend"}


def _local_auth_unavailable_response():
    """Return a stable fallback message when frontend cannot import local auth."""
    message = "Backend auth is not available in this deployment."
    if LOCAL_AUTH_IMPORT_ERROR:
        message = f"{message} Missing dependency: {LOCAL_AUTH_IMPORT_ERROR}"
    return {"success": False, "message": message}


def load_auth_css():
    """Load polished styling for login and signup pages."""
    css = """
    <style>
    .stApp {
        background:
            radial-gradient(circle at top left, rgba(59, 130, 246, 0.20), transparent 28%),
            radial-gradient(circle at bottom right, rgba(14, 165, 233, 0.18), transparent 26%),
            linear-gradient(135deg, #eef4ff 0%, #f8fbff 46%, #edf6ff 100%) !important;
    }

    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}

    .main .block-container {
        max-width: 520px !important;
        margin: 42px auto !important;
        padding: 40px 38px 32px !important;
        background: rgba(255, 255, 255, 0.9) !important;
        border: 1px solid rgba(148, 163, 184, 0.22) !important;
        border-radius: 28px !important;
        box-shadow: 0 28px 70px rgba(15, 23, 42, 0.12) !important;
        backdrop-filter: blur(14px) !important;
    }

    .auth-badge {
        display: inline-flex !important;
        align-items: center !important;
        justify-content: center !important;
        padding: 8px 14px !important;
        margin: 0 auto 1rem auto !important;
        border-radius: 999px !important;
        background: rgba(37, 99, 235, 0.08) !important;
        color: #1d4ed8 !important;
        font-size: 0.82rem !important;
        font-weight: 700 !important;
        letter-spacing: 0.02em !important;
        width: fit-content !important;
    }

    .app-title {
        text-align: center !important;
        font-size: 1.35rem !important;
        font-weight: 700 !important;
        color: #1e293b !important;
        margin-bottom: 0.35rem !important;
        display: flex !important;
        align-items: center !important;
        justify-content: center !important;
        gap: 8px !important;
    }

    .page-title {
        text-align: center !important;
        font-size: 2rem !important;
        font-weight: 800 !important;
        color: #0f172a !important;
        margin-bottom: 0.45rem !important;
        letter-spacing: -0.03em !important;
    }

    .auth-subtitle {
        text-align: center !important;
        color: #64748b !important;
        font-size: 0.98rem !important;
        line-height: 1.55 !important;
        margin: 0 auto 1.7rem auto !important;
        max-width: 360px !important;
    }

    [data-testid="stForm"] {
        background: transparent !important;
        border: none !important;
        padding: 0 !important;
        box-shadow: none !important;
        max-width: 100% !important;
    }

    label {
        color: #334155 !important;
        font-weight: 600 !important;
        font-size: 0.9rem !important;
        margin-bottom: 0.28rem !important;
        display: block !important;
    }

    .stTextInput {
        width: 100% !important;
        margin-bottom: 0.8rem !important;
    }

    div[data-baseweb="input"] {
        border-radius: 14px !important;
        border: 1.5px solid #dbe3f0 !important;
        background: #f8fbff !important;
        overflow: visible !important;
        position: relative !important;
    }

    div[data-baseweb="input"]:focus-within {
        border-color: #4f8df7 !important;
        box-shadow: 0 0 0 3px rgba(79, 141, 247, 0.15) !important;
        background: #ffffff !important;
    }

    div[data-baseweb="input"] > div,
    [data-testid="stTextInput"] > div > div {
        background: transparent !important;
        border: none !important;
        box-shadow: none !important;
    }

    div[data-baseweb="input"] input,
    .stTextInput input {
        width: 100% !important;
        height: 50px !important;
        padding: 0 46px 0 16px !important;
        border: none !important;
        background: transparent !important;
        color: #0f172a !important;
        font-size: 15px !important;
        box-sizing: border-box !important;
        caret-color: #2563eb !important;
    }

    .stTextInput input::placeholder,
    div[data-baseweb="input"] input::placeholder,
    ::placeholder {
        color: #94a3b8 !important;
        opacity: 1 !important;
        font-size: 14px !important;
    }

    div[data-baseweb="input"] button {
        width: 36px !important;
        height: 36px !important;
        min-width: 36px !important;
        padding: 0 !important;
        background: transparent !important;
        border: none !important;
        box-shadow: none !important;
        display: flex !important;
        align-items: center !important;
        justify-content: center !important;
        flex-shrink: 0 !important;
    }

    div[data-baseweb="input"] button:hover {
        background: rgba(0, 0, 0, 0.05) !important;
        transform: none !important;
        box-shadow: none !important;
    }

    div[data-baseweb="input"] button svg {
        width: 18px !important;
        height: 18px !important;
    }

    [data-testid="InputInstructions"] {
        display: none !important;
    }

    .forgot-password {
        text-align: right !important;
        margin: -0.15rem 0 1.05rem 0 !important;
    }

    .forgot-password a {
        color: #2563eb !important;
        text-decoration: none !important;
        font-size: 0.85rem !important;
        font-weight: 600 !important;
    }

    .forgot-password a:hover {
        color: #1d4ed8 !important;
        text-decoration: underline !important;
    }

    .stButton {
        display: flex !important;
        justify-content: center !important;
        margin: 0.3rem 0 !important;
    }

    div[data-testid="stFormSubmitButton"] button {
        background: linear-gradient(135deg, #2563eb, #38bdf8) !important;
        color: #ffffff !important;
        border: none !important;
        border-radius: 16px !important;
        min-height: 50px !important;
        width: 100% !important;
        padding: 0 20px !important;
        font-size: 16px !important;
        font-weight: 700 !important;
        box-shadow: 0 16px 30px rgba(37, 99, 235, 0.25) !important;
        transition: all 0.25s ease !important;
        cursor: pointer !important;
    }

    div[data-testid="stFormSubmitButton"] button:hover {
        background: linear-gradient(135deg, #1d4ed8, #0ea5e9) !important;
        transform: translateY(-2px) !important;
        box-shadow: 0 18px 34px rgba(37, 99, 235, 0.32) !important;
    }

    .auth-switch {
        color: #64748b !important;
        font-size: 0.92rem !important;
        line-height: 2.2 !important;
        margin-top: 1.15rem !important;
    }

    .auth-footer-button button {
        background: transparent !important;
        color: #2563eb !important;
        border: none !important;
        padding: 0 !important;
        min-height: auto !important;
        width: auto !important;
        box-shadow: none !important;
        font-size: 0.95rem !important;
        font-weight: 700 !important;
    }

    .auth-footer-button button:hover {
        color: #1d4ed8 !important;
        text-decoration: underline !important;
        transform: none !important;
        box-shadow: none !important;
    }

    .stAlert {
        border-radius: 16px !important;
        padding: 0.8rem 1rem !important;
        margin: 0.8rem 0 !important;
        font-size: 0.9rem !important;
    }

    [data-testid="stAlert"] {
        background: #fee2e2 !important;
        color: #991b1b !important;
        border: 1px solid #fecaca !important;
    }

    [data-testid="stSuccess"] {
        background: #dcfce7 !important;
        color: #166534 !important;
        border: 1px solid #bbf7d0 !important;
    }

    .stSpinner {
        text-align: center !important;
    }

    .stSpinner > div {
        border-color: #2563eb !important;
    }

    .logo-center {
        text-align: center;
        margin-bottom: 14px;
    }

    .logo-center img {
        width: 88px;
        height: 88px;
        border-radius: 24px;
        object-fit: cover;
        box-shadow: 0 14px 30px rgba(37, 99, 235, 0.15);
    }

    @media (max-width: 640px) {
        .main .block-container {
            margin: 22px 12px !important;
            padding: 28px 20px 22px !important;
        }

        .page-title {
            font-size: 1.7rem !important;
        }

        .auth-subtitle {
            font-size: 0.92rem !important;
        }
    }
    </style>
    """
    st.markdown(css, unsafe_allow_html=True)


def validate_registration(name, email, password, confirm):
    """Validate registration inputs."""
    errors = []
    clean_name = name.strip()
    clean_email = email.strip().lower()

    if len(clean_name) < 2:
        errors.append("Name must be at least 2 characters")
    if not re.match(r"^[A-Za-z\s\-']+$", clean_name):
        errors.append("Name must contain only letters, spaces, hyphens, and apostrophes")
    if not re.fullmatch(r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[A-Za-z]{2,}", clean_email):
        errors.append("Invalid email format")
    if len(password) < 8:
        errors.append("Password must be at least 8 characters")
    if password != confirm:
        errors.append("Passwords do not match")
    return errors


def perform_registration(name, email, password):
    """Perform user registration with error handling."""
    try:
        remote_result = _post_to_backend(
            REGISTER_ENDPOINTS,
            {
                "name": name.strip(),
                "email": email,
                "password": password,
            },
        )

        if remote_result.get("success"):
            result = remote_result
        elif "No matching auth endpoint found" in remote_result.get("message", "") or "Remote backend unavailable" in remote_result.get("message", ""):
            if register_user is None:
                return _local_auth_unavailable_response()
            result = register_user(name.strip(), email, password)
        else:
            result = remote_result

        if result.get("success"):
            from utils.error_handler import ErrorLogger
            ErrorLogger.log_user_action(
                "user_registration",
                user_email=email,
                success=True,
            )

        return result
    except Exception as e:
        return {"success": False, "message": f"Registration error: {str(e)}"}


def show_auth_page(mode="login"):
    """Central auth router used by app.py."""
    if mode == "login":
        login_page()
    elif mode == "register":
        registration_page()
    else:
        login_page()


def perform_login(email, password):
    """Perform login with error handling."""
    try:
        remote_result = _post_to_backend(
            LOGIN_ENDPOINTS,
            {
                "email": email,
                "password": password,
            },
        )

        if remote_result.get("success"):
            result = remote_result
        elif "No matching auth endpoint found" in remote_result.get("message", "") or "Remote backend unavailable" in remote_result.get("message", ""):
            if login_user is None:
                return _local_auth_unavailable_response()
            result = login_user(email, password)
        else:
            result = remote_result

        if result.get("success"):
            user = result["user"]
            st.session_state.logged_in = True
            st.session_state.user = user
            st.session_state.user_id = user.get("user_id") or user.get("id")
            st.session_state.username = user.get("name", "User")
            st.session_state.email = user.get("email", "")
            st.session_state.role = user.get("role", "user")
            st.session_state.page = "dashboard"
            st.session_state.last_activity = datetime.utcnow()

            from utils.error_handler import ErrorLogger
            ErrorLogger.log_user_action(
                "user_login",
                user_id=user.get("user_id"),
                success=True,
            )
            st.rerun()

        return result
    except Exception as e:
        return {"success": False, "message": f"Login error: {str(e)}"}


def get_base64_image(path):
    project_root = Path(__file__).resolve().parent.parent
    image_dir = project_root / "Image"
    image_name = Path(path).name
    candidate_paths = [
        Path(path),
        project_root / path,
        image_dir / image_name,
    ]

    for candidate in candidate_paths:
        if candidate.exists():
            with open(candidate, "rb") as f:
                return base64.b64encode(f.read()).decode()

    raise FileNotFoundError(path)


def navigate_auth(target_page):
    """Switch between login and registration routes."""
    st.session_state.page = target_page
    st.rerun()


def render_auth_header(title, subtitle, badge_text):
    """Render shared auth header content."""
    st.markdown(f'<div class="auth-badge">{badge_text}</div>', unsafe_allow_html=True)
    st.markdown(f'<div class="page-title">{title}</div>', unsafe_allow_html=True)
    st.markdown(f'<div class="auth-subtitle">{subtitle}</div>', unsafe_allow_html=True)


def render_auth_footer(prompt_text, button_text, target_page, key_prefix):
    """Render footer prompt with a working Streamlit navigation button."""
    left, middle, right = st.columns([3.1, 1.5, 3.4])
    with left:
        st.markdown(
            f'<div class="auth-switch" style="text-align:right;">{prompt_text}</div>',
            unsafe_allow_html=True,
        )
    with middle:
        st.markdown('<div class="auth-footer-button">', unsafe_allow_html=True)
        if st.button(button_text, key=f"{key_prefix}_switch"):
            navigate_auth(target_page)
        st.markdown("</div>", unsafe_allow_html=True)
    with right:
        st.markdown('<div class="auth-switch"></div>', unsafe_allow_html=True)


def render_auth_logo():
    """Render the auth logo if available."""
    try:
        logo = get_base64_image("Image/image.png")
        st.markdown(
            f"""
            <div class="logo-center">
                <img src="data:image/png;base64,{logo}" alt="Book Summarizer logo">
            </div>
            <div class="app-title">Intelligent Book Summarizer Pro</div>
            """,
            unsafe_allow_html=True,
        )
    except Exception:
        st.markdown('<div class="app-title">Intelligent Book Summarizer Pro</div>', unsafe_allow_html=True)


def login_page():
    """Render the login page."""
    load_auth_css()
    render_auth_logo()
    render_auth_header(
        "Welcome Back",
        "Sign in to continue managing your books, summaries, and reading workflow in one clean workspace.",
        "Secure access",
    )

    with st.form("login_form", clear_on_submit=True):
        email = st.text_input("Email Address", placeholder="you@example.com", key="login_email")
        password = st.text_input("Password", type="password", placeholder="Enter your password", key="login_password")
        st.markdown(
            '<div class="forgot-password"><a href="#">Forgot Password?</a></div>',
            unsafe_allow_html=True,
        )
        submit = st.form_submit_button("Login", use_container_width=True)

    if submit:
        if not email or not password:
            st.error("Please fill in all fields")
            return

        with st.spinner("Logging in..."):
            result = perform_login(email, password)
            if result.get("success"):
                st.success("Login successful!")
                st.session_state.page = "dashboard"
                st.rerun()
            else:
                st.error(result.get("message", "Login failed"))

    render_auth_footer("Don't have an account?", "Sign up", "register", "login")


def registration_page():
    """Render the registration page."""
    load_auth_css()
    render_auth_logo()
    render_auth_header(
        "Create Your Account",
        "Create a profile to upload books, generate summaries, and keep your reading notes organized.",
        "Start free",
    )

    with st.form("register_form", clear_on_submit=True):
        name = st.text_input("Full Name", placeholder="John Doe", key="reg_name")
        email = st.text_input("Email Address", placeholder="you@example.com", key="reg_email")
        password = st.text_input("Password", type="password", placeholder="Create a strong password", key="reg_password")
        confirm = st.text_input("Confirm Password", type="password", placeholder="Re-enter your password", key="reg_confirm")
        submit = st.form_submit_button("Sign Up", use_container_width=True)

    if submit:
        if not all([name, email, password, confirm]):
            st.error("Please fill in all fields")
            return

        errors = validate_registration(name, email, password, confirm)
        if errors:
            for err in errors:
                st.error(err)
            return

        with st.spinner("Creating account..."):
            result = perform_registration(name.strip(), email.strip(), password)
            if result.get("success"):
                st.success("Account created successfully!")
                st.session_state.page = "login"
                st.rerun()
            else:
                st.error(result.get("message", "Registration failed"))

    render_auth_footer("Already have an account?", "Sign in", "login", "register")


def check_auth():
    """Check if user is authenticated."""
    if "logged_in" not in st.session_state:
        st.session_state.logged_in = False
    if "page" not in st.session_state:
        st.session_state.page = "login"

    if st.session_state.get("logged_in") and st.session_state.get("last_activity"):
        try:
            last_activity = st.session_state.last_activity
            if isinstance(last_activity, str):
                last_activity = datetime.fromisoformat(last_activity.replace("Z", "+00:00"))

            time_diff = (datetime.utcnow() - last_activity).total_seconds()
            if time_diff > 8 * 3600:
                logout_user()
                return False
        except Exception:
            pass

    return st.session_state.get("logged_in", False)


def logout_user():
    """Logout current user."""
    try:
        from utils.error_handler import ErrorLogger
        user_id = st.session_state.get("user_id")
        if user_id:
            ErrorLogger.log_user_action("user_logout", user_id=user_id, success=True)
    except Exception:
        pass

    keys_to_clear = ["logged_in", "user_id", "username", "email", "role", "user", "last_activity"]
    for key in keys_to_clear:
        if key in st.session_state:
            del st.session_state[key]

    st.session_state.logged_in = False
    st.session_state.page = "login"
    st.rerun()


def simple_auth_page():
    """Simple unified auth page."""
    load_auth_css()
    query_params = st.query_params if hasattr(st, "query_params") else st.experimental_get_query_params()
    mode = query_params.get("mode", ["login"])[0]

    if mode not in ["login", "register"]:
        mode = "login"

    if mode == "login":
        login_page()
    else:
        registration_page()
