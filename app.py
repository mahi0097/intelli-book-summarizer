# app.py - COMPLETE FIXED VERSION WITH EXACT UI MATCH AND PROPER SIDEBAR
import os
import sys
import base64
import builtins
import streamlit as st
from datetime import datetime
from pathlib import Path
from utils.database import create_user


def print(*args, **kwargs):
    """Safe console printing for Windows terminals with limited encodings."""
    sep = kwargs.pop("sep", " ")
    end = kwargs.pop("end", "\n")
    file = kwargs.pop("file", None)
    flush = kwargs.pop("flush", False)
    message = sep.join(str(arg) for arg in args)
    try:
        builtins.print(message, end=end, file=file, flush=flush, **kwargs)
    except UnicodeEncodeError:
        safe_message = message.encode("ascii", "replace").decode("ascii")
        builtins.print(safe_message, end=end, file=file, flush=flush, **kwargs)

# Add project root to Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

# Create necessary directories
os.makedirs('logs', exist_ok=True)
os.makedirs('uploads', exist_ok=True)
os.makedirs('temp', exist_ok=True)
os.makedirs('exports', exist_ok=True)
os.makedirs('image', exist_ok=True)

print("🚀 Starting Book Summarization App...")
print(f"📁 Project root: {project_root}")

# Page config
st.set_page_config(
    page_title="Intelligent Book Summarizer Pro",
    page_icon="📚",
    layout="wide",
    initial_sidebar_state="expanded",
    menu_items={
        'Get Help': 'https://github.com/yourusername/book-summarizer',
        'Report a bug': 'https://github.com/yourusername/book-summarizer/issues',
        'About': '# Intelligent Book Summarizer Pro\nAI-powered book summarization with export capabilities.'
    }
)

# Custom CSS - EXACT MATCH TO IMAGE
def load_global_css():
    st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');

    * {
        font-family: 'Inter', sans-serif;
        margin: 0;
        padding: 0;
        box-sizing: border-box;
    }

    .stApp {
        background: #eef6ff;
    }

    /* Hide Streamlit elements but keep the header so the sidebar toggle stays available */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: visible;}

    .block-container {
        max-width: 1200px;
        padding: 2rem 2rem !important;
        margin: 0 auto;
    }

    /* ===== SIDEBAR STYLING ===== */
    section[data-testid="stSidebar"] {
        background: linear-gradient(180deg, #0f172a 0%, #1e3a8a 100%) !important;
        min-width: 220px !important;
    }

    section[data-testid="stSidebar"] > div {
        padding: 2rem 1rem;
        background: linear-gradient(180deg, #0f172a 0%, #1e3a8a 100%) !important;
    }

    /* Sidebar content styling */
    section[data-testid="stSidebar"] .stMarkdown {
        color: white !important;
    }

    /* Sidebar button styling */
    section[data-testid="stSidebar"] .stButton > button {
        width: 100% !important;
        background: rgba(255, 255, 255, 0.1) !important;
        color: white !important;
        border: 1px solid rgba(255, 255, 255, 0.15) !important;
        border-radius: 12px !important;
        padding: 0.75rem 1rem !important;
        font-weight: 500 !important;
        font-size: 0.95rem !important;
        text-align: left !important;
        margin-bottom: 0.5rem !important;
        transition: all 0.2s ease !important;
        backdrop-filter: blur(10px) !important;
        white-space: normal !important;
        word-break: break-word !important;
        min-height: 44px !important;
        height: auto !important;
        line-height: 1.3 !important;
    }

    section[data-testid="stSidebar"] .stButton > button:hover {
        background: rgba(255, 255, 255, 0.25) !important;
        border-color: rgba(255, 255, 255, 0.3) !important;
        transform: translateX(3px) !important;
    }

    section[data-testid="stSidebar"] .stButton > button:active {
        background: rgba(255, 255, 255, 0.3) !important;
    }

    /* Sidebar divider */
    section[data-testid="stSidebar"] hr {
        border-color: rgba(255, 255, 255, 0.2) !important;
        margin: 1.5rem 0 !important;
    }

    /* User profile card in sidebar */
    section[data-testid="stSidebar"] .sidebar-user-card {
        background: rgba(255, 255, 255, 0.15);
        backdrop-filter: blur(10px);
        border-radius: 16px;
        padding: 1.5rem 1rem;
        margin-bottom: 1.5rem;
        border: 1px solid rgba(255, 255, 255, 0.2);
        text-align: center;
    }

    section[data-testid="stSidebar"] .sidebar-user-avatar {
        width: 60px;
        height: 60px;
        background: white !important;
        border-radius: 50%;
        display: flex;
        align-items: center;
        justify-content: center;
        margin: 0 auto 1rem auto;
        font-size: 30px;
        color: #4776E6 !important;
        font-weight: 700;
    }

    /* Navbar */
    .navbar {
        display: flex;
        justify-content: space-between;
        align-items: center;
        margin-bottom: 80px;
    }

    .logo {
        font-size: 24px;
        font-weight: 600;
        color: #1e293b;
    }

    .nav-buttons {
        display: flex;
        gap: 20px;
    }

    .nav-btn {
        background: none;
        border: none;
        font-size: 16px;
        font-weight: 500;
        color: #64748b;
        cursor: pointer;
        padding: 8px 16px;
        transition: color 0.3s;
    }

    .nav-btn:hover {
        color: #2563eb;
    }

    .logo-container {
        display: flex;
        align-items: center;
        gap: 12px;
    }

    .logo-img {
        width: 120px;
        height: 120px;
        border-radius: 40%;
        object-fit: cover;
    }

    .logo-text {
        font-size: 22px;
        font-weight: 600;
        color: #1e293b;
    }

    /* NAVBAR CAPSULE BUTTONS */
    .navbar-buttons div[data-testid="stButton"] button {
        border-radius: 999px !important;
        padding: 8px 26px !important;
        font-size: 15px !important;
        font-weight: 500 !important;
        transition: all 0.3s ease !important;
        box-shadow: none !important;
    }

    /* Common capsule style */
    div[data-testid="stButton"] button {
        border-radius: 999px !important;
        padding: 10px 30px !important;
        font-size: 16px !important;
        font-weight: 500 !important;
    }

    /* LOGIN BUTTON */
    button[kind="secondary"][data-testid="baseButton-secondary"] {
        background: white !important;
        color: black !important;
        border: 1px solid #cbd5e1 !important;
    }

    /* REGISTER BUTTON */
    button#nav_register {
        background: blue !important;
        color: white !important;
        border: none !important;
        border-radius: 999px !important;
        padding: 10px 28px !important;
        font-weight: 500 !important;
        box-shadow: 0 8px 18px rgba(110,168,254,0.35) !important;
    }

    /* REGISTER HOVER */
    button#nav_register:hover {
        background: linear-gradient(135deg, #8dc0ff, #5c9cff) !important;
        transform: translateY(-2px);
        box-shadow: 0 10px 24px rgba(110,168,254,0.45) !important;
    }

    /* AI BOOK IMAGE STYLE */
    .ai-book-container{
        display:flex;
        justify-content:center;
        align-items:center;
    }

    .ai-book-image{
        width:420px;
        height:320px;
        object-fit:cover;
        border-radius:20px;
        padding:10px;
        background:rgba(255,255,255,0.6);
        backdrop-filter: blur(8px);
        box-shadow:0 15px 35px rgba(0,0,0,0.08);
    }

    /* LOGIN HOVER */
    button#nav_login:hover {
        background: #f1f5f9 !important;
    }

    .navbar-buttons {
        display:flex;
        gap:8px;
    }

    /* LOGIN BUTTON */
    .navbar-buttons div[data-testid="stButton"]:first-child button {
        background: white !important;
        color: #1e293b !important;
        border: 1px solid #cbd5e1 !important;
    }

    .navbar-buttons div[data-testid="stButton"]:first-child button:hover {
        background: #f8fafc !important;
        border-color: #94a3b8 !important;
    }

    /* REGISTER BUTTON */
    .navbar-buttons div[data-testid="stButton"]:last-child button {
        background: #2563eb !important;
        color: white !important;
        border: none !important;
        box-shadow: 0 4px 12px rgba(37, 99, 235, 0.3) !important;
    }

    .navbar-buttons div[data-testid="stButton"]:last-child button:hover {
        background: #1d4ed8 !important;
        transform: translateY(-2px);
        box-shadow: 0 8px 18px rgba(37, 99, 235, 0.4) !important;
    }

    /* GET STARTED BUTTON */
    div[data-testid="stHorizontalBlock"] div[data-testid="stButton"]:nth-child(1) button {
        background: #2563eb !important;
        color: white !important;
        border-radius: 999px !important;
        border: none !important;
        padding: 12px 28px !important;
        box-shadow: 0 4px 12px rgba(37, 99, 235, 0.3) !important;
    }

    div[data-testid="stHorizontalBlock"] div[data-testid="stButton"]:nth-child(1) button:hover {
        background: #1d4ed8 !important;
        transform: translateY(-2px);
        box-shadow: 0 8px 18px rgba(37, 99, 235, 0.4) !important;
    }

    /* TRY DEMO BUTTON (OUTLINE STYLE) */
    div[data-testid="stHorizontalBlock"] div[data-testid="stButton"]:nth-child(2) button {
        background: white !important;
        color: #1e293b !important;
        border: 1px solid #cbd5e1 !important;
        border-radius: 999px !important;
        padding: 12px 28px !important;
    }

    div[data-testid="stHorizontalBlock"] div[data-testid="stButton"]:nth-child(2) button:hover {
        background: #f8fafc !important;
        border-color: #94a3b8 !important;
    }                

    button#get_started:hover {
        background: #1d4ed8 !important;
        transform: translateY(-2px);
    }

    /* Divider */
    .divider {
        border: none;
        height: 2px;
        background: #e2e8f0;
        margin: 60px 0;
    }

    /* Features Section */
    .features-section {
        display: flex;
        gap: 30px;
        margin: 60px 0;
    }

    .feature-card {
        flex: 1;
        background: white;
        padding: 30px;
        border-radius: 16px;
        box-shadow: 0 4px 20px rgba(0, 0, 0, 0.05);
        transition: transform 0.3s ease, box-shadow 0.3s ease;
    }

    .feature-card:hover {
        transform: translateY(-5px);
        box-shadow: 0 8px 30px rgba(37, 99, 235, 0.1);
    }

    .feature-icon {
        font-size: 40px;
        margin-bottom: 20px;
    }

    .feature-card h3 {
        font-size: 20px;
        font-weight: 600;
        color: #0f172a;
        margin-bottom: 10px;
    }

    .feature-card p {
        font-size: 15px;
        color: #64748b;
        line-height: 1.6;
    }

    /* Responsive */
    @media (max-width: 768px) {
        .hero-section {
            flex-direction: column;
            text-align: center;
        }
        
        .features-section {
            flex-direction: column;
        }
        
        .hero-content h1 {
            font-size: 40px;
        }
    }
    </style>
    """, unsafe_allow_html=True)


def apply_theme_mode_css():
    """Apply light/dark theme overrides controlled by session state."""
    dark_mode = st.session_state.get("dark_mode", False)

    if dark_mode:
        theme_css = """
        <style>
        .stApp,
        [data-testid="stAppViewContainer"],
        .main,
        .main .block-container {
            background: #0f172a !important;
            color: #e5e7eb !important;
        }

        [data-testid="stHeader"] {
            background: rgba(15, 23, 42, 0.92) !important;
        }

        section[data-testid="stSidebar"],
        section[data-testid="stSidebar"] > div {
            background: linear-gradient(180deg, #020617 0%, #172554 100%) !important;
        }

        h1, h2, h3, h4, h5, h6,
        p, label, span,
        .stMarkdown, .stText, .stCaption {
            color: #e5e7eb !important;
        }

        [data-testid="stExpander"],
        [data-testid="stMetric"],
        [data-testid="stForm"],
        .summary-box,
        div[data-baseweb="select"] > div,
        .stTextInput input,
        .stTextArea textarea,
        .stNumberInput input,
        .stDateInput input {
            background: #1e293b !important;
            color: #e5e7eb !important;
            border-color: #334155 !important;
        }

        button[data-baseweb="tab"] {
            color: #e5e7eb !important;
        }
        </style>
        """
    else:
        theme_css = """
        <style>
        .stApp,
        [data-testid="stAppViewContainer"],
        .main,
        .main .block-container {
            background: #eef6ff !important;
            color: #0f172a !important;
        }

        [data-testid="stHeader"] {
            background: rgba(255, 255, 255, 0.92) !important;
        }

        h1, h2, h3, h4, h5, h6,
        p, label, span,
        .stMarkdown, .stText, .stCaption {
            color: #0f172a !important;
        }

        [data-testid="stExpander"],
        [data-testid="stMetric"],
        [data-testid="stForm"],
        .summary-box,
        div[data-baseweb="select"] > div,
        .stTextInput input,
        .stTextArea textarea,
        .stNumberInput input,
        .stDateInput input {
            background: #ffffff !important;
            color: #0f172a !important;
            border-color: #cbd5e1 !important;
        }

        button[data-baseweb="tab"] {
            color: #0f172a !important;
        }
        </style>
        """

    st.markdown(theme_css, unsafe_allow_html=True)

# Now import modules
try:
    print("📦 Importing modules...")
    
    # Import database first to check connection
    from utils.database import (
        connect_db, get_user_by_email, verify_password, 
        update_user_last_login, get_user_by_id
    )
    
    # Import frontend modules
    from frontend.auth import show_auth_page
    from frontend.upload import show_upload_page
    
    # Try to import dashboard with multiple names
    try:
        from frontend.dashboard import dashboard_page
        print("✅ dashboard imported")
    except ImportError:
        try:
            from frontend.dashboard import dashboard_page as show_dashboard
            print("✅ dashboard imported as show_dashboard")
        except ImportError as e:
            print(f"❌ Could not import dashboard: {e}")
            def dashboard_page():
                st.title("📊 Dashboard")
                st.info("Welcome to your dashboard!")
                if st.button("Go to Upload"):
                    st.session_state.page = "upload"
                    st.rerun()
    
    # Try to import mybooks
    try:
        from frontend.mybooks import show_my_books
        print("✅ mybooks imported")
    except ImportError:
        try:
            from frontend.mybooks import mybooks_page as show_my_books
            print("✅ mybooks imported as mybooks_page")
        except ImportError as e:
            print(f"❌ Could not import mybooks: {e}")
            def show_my_books():
                st.title("📚 My Books")
                st.warning("My Books module is not available")
    
    # Try to import generate_summary
    try:
        from frontend.generate_summary import summary_generation_page
        print("✅ generate_summary imported")
    except ImportError as e:
        print(f"❌ Could not import generate_summary: {e}")
        def summary_generation_page():
            st.title("✨ Generate Summary")
            st.warning("Generate Summary module is not available")
    
    # Try to import summaries
    try:
        from frontend.summaries import show_summaries_page
        print("✅ summaries imported")
    except ImportError:
        try:
            from frontend.summaries import summaries_page as show_summaries_page
            print("✅ summaries imported as summaries_page")
        except ImportError as e:
            print(f"❌ Could not import summaries: {e}")
            def show_summaries_page():
                st.title("📝 Summaries")
                st.warning("Summaries module is not available")
    
    print("✅ Basic modules imported successfully")
    
    # Try to import optional modules
    try:
        from frontend.SummaryHistory import summary_history_page
        print("✅ summary_history imported")
        HISTORY_AVAILABLE = True
    except ImportError as e:
        print(f"⚠️ Could not import SummaryHistory: {e}")
        HISTORY_AVAILABLE = False
        
        def summary_history_page():
            st.title("📜 Summary Version History")
            st.info("Version history feature will be available soon")
            if st.button("Back to Dashboard"):
                st.session_state.page = "dashboard"
                st.rerun()
    
    try:
        from frontend.summary_compare import show_summary_comparison
        print("✅ summary_compare imported")
        COMPARE_AVAILABLE = True
    except ImportError as e:
        print(f"⚠️ Could not import summary_compare: {e}")
        COMPARE_AVAILABLE = False
        
        def show_summary_comparison():
            st.title("🔍 Compare Summary Versions")
            st.info("Comparison feature will be available soon")
            if st.button("Back to Dashboard"):
                st.session_state.page = "dashboard"
                st.rerun()
    
    try:
        from frontend.admin_dashboard import show_admin_dashboard
        print("✅ admin_dashboard imported")
        ADMIN_AVAILABLE = True
    except ImportError as e:
        print(f"⚠️ Could not import admin_dashboard: {e}")
        ADMIN_AVAILABLE = False
        
        def show_admin_dashboard():
            st.title("👑 Admin Dashboard")
            st.warning("Admin dashboard is not available")
            
            # Show basic stats
            try:
                from utils.database import get_system_stats
                stats = get_system_stats()
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric("Total Users", stats.get('total_users', 0))
                with col2:
                    st.metric("Total Books", stats.get('total_books', 0))
                with col3:
                    st.metric("Total Summaries", stats.get('total_summaries', 0))
            except:
                pass
            
            if st.button("Back to Dashboard"):
                st.session_state.page = "dashboard"
                st.rerun()
    
    print("✅ All modules imported successfully")
    
except ImportError as e:
    st.error(f"❌ Error importing modules: {e}")
    st.stop()

# Initialize session state
def init_session_state():
    """Initialize all session state variables"""
    print("🔄 Initializing session state...")
    
    defaults = {
        "page": "home",
        "logged_in": False,
        "user": None,
        "user_id": None,
        "username": None,
        "role": "user",
        "last_activity": datetime.now(),
        "current_book": None,
        "current_summary": None,
        "show_sidebar": True,
        "dark_mode": False,
        "export_format": "txt",
        "selected_book_for_history": None,
        "selected_book_for_comparison": None,
        "compare_version1": None,
        "compare_version2": None,
        "sidebar_collapsed": False
    }
    
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value
    
    print("✅ Session state initialized")

# Helper functions for authentication
def check_authentication():
    """Check if user is authenticated"""
    if not st.session_state.logged_in:
        return False
    
    # Check session timeout (8 hours)
    if (datetime.now() - st.session_state.last_activity).seconds > 28800:
        st.session_state.logged_in = False
        st.session_state.user = None
        st.info("Session expired. Please login again.")
        return False
    
    return True

def login_user(email, password):
    """Authenticate user"""
    try:
        user = get_user_by_email(email)
        if user and verify_password(user['password_hash'], password):
            st.session_state.logged_in = True
            st.session_state.user = user
            st.session_state.user_id = user['_id']
            st.session_state.username = user.get('name', 'User')
            st.session_state.role = user.get('role', 'user')
            st.session_state.last_activity = datetime.now()
            
            # Update last login
            update_user_last_login(user['_id'])
            
            print(f"✅ User logged in: {email} (Role: {st.session_state.role})")
            return True
        return False
    except Exception as e:
        print(f"❌ Login error: {e}")
        return False

def logout_user():
    """Logout the current user"""
    print(f"👋 User logging out: {st.session_state.username}")
    st.session_state.logged_in = False
    st.session_state.user = None
    st.session_state.user_id = None
    st.session_state.username = None
    st.session_state.role = "user"
    st.session_state.page = "home"
    st.session_state.current_book = None
    st.session_state.current_summary = None
    st.rerun()

def get_base64_of_image(file_path):
    """Convert image to base64 string"""
    try:
        with open(file_path, "rb") as img_file:
            return base64.b64encode(img_file.read()).decode()
    except FileNotFoundError:
        return None

# Create sidebar navigation - IMPROVED VERSION
def create_sidebar():
    """Create the sidebar navigation"""
    with st.sidebar:
        # App logo/title
        st.markdown("""
        <div style="text-align: center; padding: 0.5rem 0 1.5rem 0;">
            <h1 style="color: white; font-size: 2rem; margin: 0;">📚</h1>
            <h3 style="color: white; margin: 0.5rem 0 0 0; font-weight: 600;">
                Book Summarizer Pro
            </h3>
        </div>
        """, unsafe_allow_html=True)
        
        if st.session_state.logged_in and st.session_state.user:
            user = st.session_state.user
            user_role = st.session_state.role
            
            # User profile card
            st.markdown(f"""
            <div class="sidebar-user-card">
                <div class="sidebar-user-avatar">
                    {user.get('name', 'U')[0].upper()}
                </div>
                <div style="font-weight: 600; font-size: 1.1rem; color: white; margin-bottom: 0.25rem;">
                    {user.get('name', 'User')}
                </div>
                <div style="font-size: 0.8rem; color: rgba(255,255,255,0.8); margin-bottom: 0.5rem;">
                    {user.get('email', '')}
                </div>
                {f"<div style='background:rgba(255,215,0,0.2); color:#FFD700; padding:0.25rem 0.5rem; border-radius:20px; font-size:0.75rem; display:inline-block;'>👑 ADMIN</div>" if user_role == 'admin' else ""}
            </div>
            """, unsafe_allow_html=True)
            
            st.markdown("---")
            st.markdown('<p style="color: rgba(255,255,255,0.7); font-size: 0.8rem; margin-bottom: 0.5rem;">MAIN MENU</p>', unsafe_allow_html=True)
            
            # Navigation items
            nav_items = [
                {"name": "📊 Dashboard", "page": "dashboard", "icon": "📊"},
                {"name": "📤 Upload Book", "page": "upload", "icon": "📤"},
                {"name": "📚 My Books", "page": "mybooks", "icon": "📚"},
                {"name": "✨ Generate Summary", "page": "generate_summary", "icon": "✨"},
                {"name": "📝 All Summaries", "page": "summaries", "icon": "📝"},
            ]
            
            # Optional features
            if HISTORY_AVAILABLE:
                nav_items.append({"name": "🕰️ Version History", "page": "history", "icon": "🕰️"})
            
            if COMPARE_AVAILABLE:
                nav_items.append({"name": "🔍 Compare Versions", "page": "compare", "icon": "🔍"})
            
            # Admin section
            if user_role == 'admin' and ADMIN_AVAILABLE:
                st.markdown("---")
                st.markdown('<p style="color: rgba(255,255,255,0.7); font-size: 0.8rem; margin-bottom: 0.5rem;">ADMIN</p>', unsafe_allow_html=True)
                nav_items.append({"name": "👑 Admin Dashboard", "page": "admin", "icon": "👑"})
            
            # Regular navigation buttons
            for item in nav_items:
                if st.button(
                    item['name'],
                    key=f"nav_{item['page']}",
                    use_container_width=True
                ):
                    st.session_state.page = item['page']
                    st.rerun()
            
            st.markdown("---")
            
            # Quick stats
            try:
                from utils.database import get_books_by_user, get_summaries_by_user
                user_id = st.session_state.user_id
                
                books = get_books_by_user(user_id, limit=100)
                summaries = get_summaries_by_user(user_id)
                
                st.markdown('<p style="color: rgba(255,255,255,0.7); font-size: 0.8rem; margin-bottom: 0.5rem;">QUICK STATS</p>', unsafe_allow_html=True)
                
                col1, col2 = st.columns(2)
                with col1:
                    st.markdown(f"""
                    <div style="background:rgba(255,255,255,0.1); padding:0.75rem; border-radius:10px; text-align:center;">
                        <div style="font-size:1.5rem; color:white;">{len(books) if books else 0}</div>
                        <div style="font-size:0.7rem; color:rgba(255,255,255,0.7);">Books</div>
                    </div>
                    """, unsafe_allow_html=True)
                
                with col2:
                    st.markdown(f"""
                    <div style="background:rgba(255,255,255,0.1); padding:0.75rem; border-radius:10px; text-align:center;">
                        <div style="font-size:1.5rem; color:white;">{len(summaries) if summaries else 0}</div>
                        <div style="font-size:0.7rem; color:rgba(255,255,255,0.7);">Summaries</div>
                    </div>
                    """, unsafe_allow_html=True)
            except Exception as e:
                pass
            
            st.markdown("---")
            
            # Settings and Logout
            col1, col2 = st.columns(2)
            
            with col1:
                if st.button("⚙️ Settings", key="nav_settings", use_container_width=True):
                    st.info("Settings page coming soon!")
            
            with col2:
                if st.button("🚪 Logout", key="nav_logout", use_container_width=True):
                    logout_user()
            
            # Dark mode toggle
            toggle_label = "🌙 Dark Mode" if not st.session_state.dark_mode else "☀️ Light Mode"
            dark_mode = st.toggle(toggle_label, value=st.session_state.dark_mode, key="sidebar_dark_mode")
            if dark_mode != st.session_state.dark_mode:
                st.session_state.dark_mode = dark_mode
                st.rerun()
            
        else:
            # Non-authenticated sidebar
            st.markdown("""
            <div style="text-align: center; padding: 2rem 1rem;">
                <h1 style="color: white; font-size: 3rem; margin-bottom: 0.5rem;">📚</h1>
                <h3 style="color: white; margin-bottom: 1rem;">Book Summarizer Pro</h3>
                <p style="color: rgba(255,255,255,0.8); font-size: 0.9rem;">
                    AI-powered book summaries at your fingertips
                </p>
            </div>
            """, unsafe_allow_html=True)
            
            st.markdown("---")
            
            if st.button("🔑 Login", key="nav_login_sidebar", use_container_width=True):
                st.session_state.page = "login"
                st.rerun()
            
            if st.button("📝 Register", key="nav_register_sidebar", use_container_width=True):
                st.session_state.page = "register"
                st.rerun()
        
        # Footer
        st.markdown("---")
        st.markdown("""
        <div style="text-align: center; color: rgba(255,255,255,0.5); font-size: 0.7rem; padding: 0.5rem;">
            📚 Intelligent Book Summarizer Pro<br>
            v2.0.0 • © 2024
        </div>
        """, unsafe_allow_html=True)

# Home page - EXACT MATCH TO IMAGE
def show_home_page():
    # Load CSS
    load_global_css()
    
    # Navbar with login/register
    col1, col2 = st.columns([6, 2])
    with col1:
        # Try to load logo image
        logo_base64 = get_base64_of_image("image/image.png")
        if logo_base64:
            st.markdown(f"""
            <div class="logo-container">
                <img src="data:image/png;base64,{logo_base64}" class="logo-img"/>
                <div class="logo-text">Intelligent Book Summarizer Pro</div>
            </div>
            """, unsafe_allow_html=True)
        else:
            st.markdown("""
            <div class="logo-container">
                <div style="font-size: 48px; margin-right: 10px;">📚</div>
                <div class="logo-text">Intelligent Book Summarizer Pro</div>
            </div>
            """, unsafe_allow_html=True)

    with col2:
        st.markdown('<div class="navbar-buttons">', unsafe_allow_html=True)
        
        # Create two columns for the buttons
        nav_col1, nav_col2 = st.columns(2)
        
        with nav_col1:
            if st.button("Login", key="nav_login", use_container_width=True):
                st.session_state.page = "login"
                st.rerun()
        
        with nav_col2:
            if st.button("Register", key="nav_register", use_container_width=True):
                st.session_state.page = "register"
                st.rerun()
        
        st.markdown('</div>', unsafe_allow_html=True)
    
    # Hero Section
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("""
        <h1 style="font-size: 56px; font-weight: 700; line-height: 1.2; color: #0f172a; margin-bottom: 20px;">
            Summarize Any Book<br>in Seconds with AI
        </h1>
        <p style="font-size: 18px; color: #64748b; line-height: 1.6; margin-bottom: 30px;">
            AI-powered smart summaries to reimagine the millennial elegant illustrations, and more.
        </p>
        """, unsafe_allow_html=True)
        
        # Buttons in hero section
        btn_cols = st.columns(2)
        with btn_cols[0]:
            if st.button("Get Started", key="get_started", use_container_width=True):
                st.session_state.page = "register"
                st.rerun()
        with btn_cols[1]:
            if st.button("Try Demo", key="try_demo", use_container_width=True):
                st.session_state.page = "login"
                st.rerun()
    
    with col2:
        # Try to load book image
        try:
            img_base64 = get_base64_of_image("image/book_image.png")
            if img_base64:
                st.markdown(f"""
                <div class="ai-book-container">
                    <img src="data:image/png;base64,{img_base64}" class="ai-book-image">
                </div>
                """, unsafe_allow_html=True)
            else:
                st.markdown("""
                <div class="ai-book-container">
                    <img src="https://img.icons8.com/fluency/480/book.png" class="ai-book-image">
                </div>
                """, unsafe_allow_html=True)
        except:
            st.image("https://img.icons8.com/fluency/480/book.png", width=400)
    
    # Divider
    st.markdown("<hr style='border: none; height: 2px; background: #e2e8f0; margin: 60px 0;'>", unsafe_allow_html=True)
    
    # Features Section - EXACT MATCH TO IMAGE
    f1, f2, f3 = st.columns(3)
    
    with f1:
        st.markdown("""
        <div style="background: white; padding: 30px; border-radius: 16px; box-shadow: 0 4px 20px rgba(0,0,0,0.05);">
            <div style="font-size: 40px; margin-bottom: 20px;">📤</div>
            <h3 style="font-size: 20px; font-weight: 600; color: #0f172a; margin-bottom: 10px;">Upload PDF</h3>
            <p style="font-size: 15px; color: #64748b; line-height: 1.6;">Upload your PDF and edit any summary type.</p>
        </div>
        """, unsafe_allow_html=True)
    
    with f2:
        st.markdown("""
        <div style="background: white; padding: 30px; border-radius: 16px; box-shadow: 0 4px 20px rgba(0,0,0,0.05);">
            <div style="font-size: 40px; margin-bottom: 20px;">⚙️</div>
            <h3 style="font-size: 20px; font-weight: 600; color: #0f172a; margin-bottom: 10px;">Choose Summary Type</h3>
            <p style="font-size: 15px; color: #64748b; line-height: 1.6;">Choose and wait to choose summary type-essions.</p>
        </div>
        """, unsafe_allow_html=True)
    
    with f3:
        st.markdown("""
        <div style="background: white; padding: 30px; border-radius: 16px; box-shadow: 0 4px 20px rgba(0,0,0,0.05);">
            <div style="font-size: 40px; margin-bottom: 20px;">🤖</div>
            <h3 style="font-size: 20px; font-weight: 600; color: #0f172a; margin-bottom: 10px;">Instant AI Summary</h3>
            <p style="font-size: 15px; color: #64748b; line-height: 1.6;">Instant AI summary and annotation, elegant's and clance.</p>
        </div>
        """, unsafe_allow_html=True)

# Main routing function
def route():
    """Route to the appropriate page"""
    page = st.session_state.page
    
    # Update last activity
    if st.session_state.logged_in:
        st.session_state.last_activity = datetime.now()
    
    # Public pages (no authentication required)
    if page in ["home", "login", "register"]:
        if page == "home":
            show_home_page()
        elif page == "login":
            load_global_css()
            show_auth_page("login")
        elif page == "register":
            load_global_css()
            show_auth_page("register")
        return
    
    # Private pages - require authentication
    if not check_authentication():
        st.session_state.page = "home"
        st.rerun()
        return
    
    # Show sidebar for authenticated users
    create_sidebar()
    
    # Route to appropriate page
    try:
        if page == "dashboard":
            dashboard_page()
        elif page == "upload":
            show_upload_page()
        elif page == "mybooks":
            show_my_books()
        elif page == "generate_summary":
            summary_generation_page()
        elif page == "summaries":
            show_summaries_page()
        elif page == "history":
            summary_history_page()
        elif page == "compare":
            show_summary_comparison()
        elif page == "admin":
            if st.session_state.role != "admin":
                st.error("❌ Admin access required")
                st.session_state.page = "dashboard"
                st.rerun()
                return
            show_admin_dashboard()
        else:
            st.error(f"Page '{page}' not found")
            if st.button("Back to Dashboard"):
                st.session_state.page = "dashboard"
                st.rerun()
    except Exception as e:
        st.error(f"Error loading page: {str(e)}")

# Main app
def main():
    """Main application function"""
    print("🚀 Starting application...")
    
    # Initialize session state
    init_session_state()
    
    # Load global CSS
    load_global_css()
    
    # Route to appropriate page
    route()

    # Apply theme overrides after page-level CSS so the sidebar toggle wins.
    apply_theme_mode_css()

# Run the app
if __name__ == "__main__":
    main()
