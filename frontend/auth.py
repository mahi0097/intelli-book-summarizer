# frontend/auth.py - UPDATED CSS FOR EXACT MATCH TO IMAGES
import streamlit as st
import re
import sys
import os
from datetime import datetime
from utils.error_handler import error_handler, ValidationError, RateLimitError
from utils.validators import InputValidator
from frontend.error_ui import safe_execute, validate_form_inputs

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

# ✅ FIXED: Import from backend, NOT frontend!
try:
    from backend.auth import register_user, login_user
except ImportError as e:
    st.error(f"Backend auth module not found: {e}")
    # Create dummy functions to prevent crashes
    register_user = lambda name, email, password, role="user": {"success": False, "message": "Backend not available"}
    login_user = lambda email, password: {"success": False, "message": "Backend not available"}


# =========================
# 🎨 CLEAN CSS FOR EXACT MATCH TO IMAGES
# =========================
def load_auth_css():
    """Load clean CSS matching the provided images"""
    css = """
    <style>
    /* Main container - clean white background */
    .stApp {
        background: linear-gradient(135deg, #eef2f7, #e6f0ff) !important;
    }
    
    /* Hide Streamlit branding */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    
    /* Center the form - reduced width */
    .main .block-container {
        max-width: 480px !important;
        margin: 80px auto !important;
        padding: 30px 35px !important;
        background: white !important;
        border-radius: 24px !important;
        box-shadow: 0 30px 80px rgba(0,0,0,0.12) !important;
    }
    
    /* App title - now showing properly */
    .app-title {
        text-align: center !important;
        font-size: 1.5rem !important;
        font-weight: 600 !important;
        color: #1e293b !important;
        margin-bottom: 1.5rem !important;
        letter-spacing: -0.3px;
        display: flex !important;
        align-items: center !important;
        justify-content: center !important;
        gap: 8px !important;
    }
    
    /* Page title - "Welcome Back" or "Create Your Account" */
    .page-title {
        text-align: center !important;
        font-size: 1.8rem !important;
        font-weight: 700 !important;
        color: #0f172a !important;
        margin-bottom: 1.8rem !important;
        letter-spacing: -0.5px;
    }
    
    /* Form container - reduced width */
    [data-testid="stForm"] {
        background: transparent !important;
        border: none !important;
        padding: 0 !important;
        box-shadow: none !important;
        max-width: 100% !important;
    }
    
    /* Label styling */
    label {
        color: #334155 !important;
        font-weight: 500 !important;
        font-size: 0.9rem !important;
        margin-bottom: 0.2rem !important;
        display: block !important;
    }
    
    /* FIXED: Input field styling - increased width */
    .stTextInput {
         width: 100% !important;
         margin-bottom: 16px !important;
    }
    .stTextInput input {
        width: 100% !important;
        height: 48px !important;
        padding: 0 32px !important;
        border-radius: 10px !important;
        border: 1px solid #d1d5db !important;
        background: #f9fafb !important;
        font-size: 14px !important;
        box-sizing: border-box !important;
    }

    /* Input focus state */
    .stTextInput input:focus {
         border-color: #4f8df7 !important;
        box-shadow: 0 0 0 2px rgba(79,141,247,0.2) !important;
        outline: none !important;
    }
    
    /* Placeholder text */
    ::placeholder {
        color: #94a3b8 !important;
        opacity: 1 !important;
        font-weight: 400 !important;
        font-size: 14px !important;
    }
    
    /* Forgot Password link */
    .forgot-password {
        text-align: right !important;
        margin: -0.2rem 0 1.2rem 0 !important;
    }
    
    .forgot-password a {
        color: #2563eb !important;
        text-decoration: none !important;
        font-size: 0.85rem !important;
        font-weight: 500 !important;
    }
    
    .forgot-password a:hover {
        text-decoration: underline !important;
        color: #1d4ed8 !important;
    }
    
    /* FIXED: Button styling */
    .stButton {
        display: flex !important;
        justify-content: center !important;
        margin: 0.5rem 0 !important;
    }
    
    /* Target form button specifically */
    div[data-testid="stForm"] > div:last-child button,
    div[data-testid="stFormSubmitButton"] button {
    background: linear-gradient(135deg, #4f8df7, #6ea8fe) !important;
    color: white !important;
    border: none !important;
    border-radius: 999px !important;
    height: 35px !important;
    width: 10% !important;
    padding: 0 30px !important; 
    font-size: 16px !important;
    font-weight: 600 !important;
    box-shadow: 0 10px 25px rgba(79,141,247,0.35) !important;
    transition: all 0.25s ease !important;
    cursor: pointer !important;
}
div[data-testid="stFormSubmitButton"] button:hover {
    background: linear-gradient(135deg, #3b7de8, #5a96f0) !important;
    box-shadow: 0 15px 30px rgba(79,141,247,0.45) !important;
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
    /* Hover effect */
    div[data-testid="stForm"] button:hover {
        transform: translateY(-2px) !important;
        box-shadow: 0 15px 30px rgba(79,141,247,0.45) !important;
    }
    div[data-baseweb="input"] button:hover {
    background: rgba(0,0,0,0.05) !important;
    box-shadow: none !important;
     transform: none !important;
     }

     div[data-baseweb="input"] button svg {
    width: 18px !important;
    height: 18px !important;
}

    /* Switch between login/signup */
    .auth-switch {
        text-align: center !important;
        color: #64748b !important;
        font-size: 0.9rem !important;
        margin-top: 1.5rem !important;
    }
    
    .auth-switch a {
        color: #2563eb !important;
        text-decoration: none !important;
        font-weight: 600 !important;
        margin-left: 0.25rem !important;
        cursor: pointer !important;
    }
    
    .auth-switch a:hover {
        text-decoration: underline !important;
    }
    
    /* Error/Success messages */
    .stAlert {
        border-radius: 999px !important;
        padding: 0.6rem 1rem !important;
        margin: 0.8rem 0 !important;
        font-size: 0.85rem !important;
        text-align: center !important;
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
    
    /* ===== INPUT FIELDS - COMPLETE FIX ===== */

/* Wrapper */
div[data-baseweb="input"] {
    border-radius: 12px !important;
    border: 1.5px solid #e2e8f0 !important;
    background: #f8fafc !important;
    overflow: visible !important;   /* ← CRITICAL: was 'hidden', caused eye icon bleed */
    position: relative !important;
}

/* All inputs — text AND password */
div[data-baseweb="input"] input {
   background: transparent !important;
    color: #1e293b !important;
    font-size: 15px !important;
    padding: 0 48px 0 16px !important;
    height: 48px !important;
    border: none !important;
    outline: none !important;
    box-shadow: none !important;
    width: 100% !important;
    box-sizing: border-box !important;
    caret-color: #2563eb !important;
}

/* Remove red border on empty/untouched fields */
div[data-baseweb="input"]:not(:focus-within) {
    border-color: #e2e8f0 !important;
    box-shadow: none !important;
}

/* Focus state */
div[data-baseweb="input"]:focus-within {
     border-color: #4f8df7 !important;
    box-shadow: 0 0 0 3px rgba(79,141,247,0.15) !important;
    background: white !important;
}

/* Fix Streamlit's default red/error border */
div[data-baseweb="input"] > div {
    background: transparent !important;
    border: none !important;
    box-shadow: none !important;
    width: 100% !important;
}

/* Placeholder */
div[data-baseweb="input"] input::placeholder {
   color: #94a3b8 !important;
    font-size: 14px !important;
}

/* Remove Streamlit's own border on the inner wrapper */
[data-testid="stTextInput"] > div > div {
    border: none !important;
    box-shadow: none !important;
    background: transparent !important;
}

/* Hide the "Press Enter to submit" tooltip */
[data-testid="InputInstructions"] {
    display: none !important;
}
    
    
    
    
    
    
   
    
    /* Spinner styling */
    .stSpinner {
        text-align: center !important;
    }
    
    .stSpinner > div {
        border-color: #2563eb !important;
    }
    
    /* Logo center styling */
    .logo-center {
        text-align: center;
        margin-bottom: 15px;
    }

    .logo-center img {
        width: 100px;
        height: 100px;
        border-radius: 50%;
        object-fit: cover;
    }
    </style>
    """
    
    st.markdown(css, unsafe_allow_html=True)


# =========================
# VALIDATION FUNCTIONS
# =========================
def validate_registration(name, email, password, confirm):
    """Validate registration inputs"""
    errors = []
    if len(name.strip()) < 2:
        errors.append("Name must be at least 2 characters")
    if not re.match(r"^[A-Za-z\s\-']+$", name.strip()):
        errors.append("Name must contain only letters, spaces, hyphens, and apostrophes")
    if not re.match(r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[A-Za-z]{2,}$", email):
        errors.append("Invalid email format")
    if len(password) < 8:
        errors.append("Password must be at least 8 characters")
    if password != confirm:
        errors.append("Passwords do not match")
    return errors


# =========================
# AUTHENTICATION FUNCTIONS
# =========================
def perform_registration(name, email, password):
    """Perform user registration with error handling"""
    try:
        if register_user is None:
            st.error("Registration service unavailable")
            return {"success": False, "message": "Service unavailable"}
        
        result = register_user(name.strip(), email, password)
        
        if result.get("success"):
            # Log successful registration
            from utils.error_handler import ErrorLogger
            ErrorLogger.log_user_action(
                "user_registration",
                user_email=email,
                success=True
            )
        
        return result
        
    except Exception as e:
        return {"success": False, "message": f"Registration error: {str(e)}"}

def show_auth_page(mode="login"):
    """
    Central auth router used by app.py
    """
    if mode == "login":
        login_page()
    elif mode == "register":
        registration_page()
    else:
        login_page()

def perform_login(email, password):
    """Perform login with error handling"""
    try:
        if login_user is None:
            st.error("Login service unavailable")
            return {"success": False, "message": "Service unavailable"}
        
        result = login_user(email, password)
        
        if result.get("success"):
            user = result["user"]
            
            # Set session state
            st.session_state.logged_in = True
            st.session_state.user = user
            st.session_state.user_id = user.get("user_id") or user.get("id")
            st.session_state.username = user.get("name", "User")
            st.session_state.email = user.get("email", "")
            st.session_state.role = user.get("role", "user")
            st.session_state.page = "dashboard"
            st.session_state.last_activity = datetime.utcnow()
            
            # Log successful login
            from utils.error_handler import ErrorLogger
            ErrorLogger.log_user_action(
                "user_login",
                user_id=user.get("user_id"),
                success=True
            )
            st.rerun()
        
        return result
        
    except Exception as e:
        return {"success": False, "message": f"Login error: {str(e)}"}

import base64

def get_base64_image(path):
    with open(path, "rb") as f:
        return base64.b64encode(f.read()).decode()
        
# =========================
# LOGIN PAGE - EXACT MATCH TO IMAGE
# =========================
def login_page():
    """Login page matching the provided image"""
    load_auth_css()
    
    # Logo at the top
    try:
        logo = get_base64_image("image/image.png")
        st.markdown(f"""
        <div class="logo-center">
            <img src="data:image/png;base64,{logo}">
        </div>
        """, unsafe_allow_html=True)
    except:
        st.markdown('<div class="app-title">📚 Intelligent Book Summarizer Pro</div>', unsafe_allow_html=True)
    
    # Page title - "Welcome Back" as in image
    st.markdown('<div class="page-title">Welcome Back</div>', unsafe_allow_html=True)
    
    # Login form
    with st.form("login_form", clear_on_submit=True):
        # Email field with placeholder exactly as in image
        email = st.text_input("Email Address", placeholder="you@example.com", key="login_email")
        
        # Password field
        password = st.text_input("Password", type="password", placeholder="Enter your password", key="login_password")
        
        # Forgot Password link as in image
        st.markdown(
            '<div class="forgot-password">'
            '<a href="#" onclick="alert(\'Password reset feature coming soon!\')">Forgot Password?</a>'
            '</div>',
            unsafe_allow_html=True
        )
        
        # Login button - full width as in image
        submit = st.form_submit_button("Login", use_container_width=True)
    
    if submit:
        if not email or not password:
            st.error("Please fill in all fields")
            return
        
        with st.spinner("Logging in..."):
            result = perform_login(email, password)
            
            if result.get("success"):
                st.success("✅ Login successful!")
                st.session_state.page = "dashboard"
                st.rerun()
            else:
                st.error(f"❌ {result.get('message', 'Login failed')}")
    
    # Switch to signup - FIXED: Now properly links to register page
    st.markdown(
        '<div class="auth-switch">'
        'Don\'t have an account? '
        '<a href="#" onclick="window.location.href=\'/?page=register\'">Sign up</a>'
        '</div>',
        unsafe_allow_html=True
    )


# =========================
# REGISTRATION PAGE - EXACT MATCH TO IMAGE
# =========================
def registration_page():
    """Registration page matching the provided image"""
    load_auth_css()
    
    # Logo at the top
    try:
        logo = get_base64_image("image/image.png")
        st.markdown(f"""
        <div class="logo-center">
            <img src="data:image/png;base64,{logo}">
        </div>
        """, unsafe_allow_html=True)
    except:
        st.markdown('<div class="app-title">📚 Intelligent Book Summarizer Pro</div>', unsafe_allow_html=True)
    
    # Page title - "Create Your Account" as in image
    st.markdown('<div class="page-title">Create Your Account</div>', unsafe_allow_html=True)
    
    # Registration form
    with st.form("register_form", clear_on_submit=True):
        # Full Name field - exactly as in image
        name = st.text_input("Full Name", placeholder="John Doe", key="reg_name")
        
        # Email field - exactly as in image
        email = st.text_input("Email Address", placeholder="you@example.com", key="reg_email")
        
        # Password field
        password = st.text_input("Password", type="password", placeholder="●●●●●●●●●", key="reg_password")
        
        # Confirm Password field
        confirm = st.text_input("Confirm Password", type="password", placeholder="●●●●●●●●●", key="reg_confirm")
        
        # Sign Up button - full width
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
                st.success("✅ Account created successfully!")
                # Change page to login
                if 'page' in st.session_state:
                    st.session_state.page = "login"
                st.rerun()
            else:
                st.error(f"❌ {result.get('message', 'Registration failed')}")
    
    # Switch to login - FIXED: Now properly links to login page
    st.markdown(
        '<div class="auth-switch">'
        'Already have an account? '
        '<a href="#" onclick="window.location.href=\'/?page=login\'">Sign in</a>'
        '</div>',
        unsafe_allow_html=True
    )


# =========================
# AUTHENTICATION CHECK
# =========================
def check_auth():
    """Check if user is authenticated"""
    # Initialize session state if not exists
    if 'logged_in' not in st.session_state:
        st.session_state.logged_in = False
    if 'page' not in st.session_state:
        st.session_state.page = 'login'
    
    # Check session timeout (8 hours)
    if st.session_state.get("logged_in") and st.session_state.get("last_activity"):
        try:
            last_activity = st.session_state.last_activity
            if isinstance(last_activity, str):
                last_activity = datetime.fromisoformat(last_activity.replace('Z', '+00:00'))
            
            time_diff = (datetime.utcnow() - last_activity).total_seconds()
            if time_diff > 8 * 3600:  # 8 hours timeout
                logout_user()
                return False
        except:
            pass
    
    return st.session_state.get("logged_in", False)


def logout_user():
    """Logout current user"""
    try:
        from utils.error_handler import ErrorLogger
        user_id = st.session_state.get("user_id")
        if user_id:
            ErrorLogger.log_user_action("user_logout", user_id=user_id, success=True)
    except:
        pass
    
    # Clear session state
    keys_to_clear = ["logged_in", "user_id", "username", "email", "role", "user", "last_activity"]
    for key in keys_to_clear:
        if key in st.session_state:
            del st.session_state[key]
    
    st.session_state.logged_in = False
    st.session_state.page = "login"
    st.rerun()


# =========================
# BACKUP: SIMPLE AUTH PAGE
# =========================
def simple_auth_page():
    """Simple unified auth page"""
    load_auth_css()
    
    # Determine mode from query params
    query_params = st.query_params if hasattr(st, 'query_params') else st.experimental_get_query_params()
    mode = query_params.get("mode", ["login"])[0]
    
    if mode not in ["login", "register"]:
        mode = "login"
    
    # Show appropriate page
    if mode == "login":
        login_page()
    else:
        registration_page()