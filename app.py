# app.py - COMPLETE FIXED VERSION
import os
import sys
import streamlit as st
from datetime import datetime
from pathlib import Path
from utils.database import create_user

# Add project root to Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

# Create necessary directories
os.makedirs('logs', exist_ok=True)
os.makedirs('uploads', exist_ok=True)
os.makedirs('temp', exist_ok=True)
os.makedirs('exports', exist_ok=True)

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

# Custom CSS
st.markdown("""
<style>
    /* Main styling */
    .main-header {
        font-size: 2.5rem;
        font-weight: bold;
        color: #1E3A8A;
        margin-bottom: 1rem;
        text-align: center;
    }
    
    .sub-header {
        font-size: 1.8rem;
        color: #374151;
        margin-bottom: 1rem;
    }
    
    /* Card styling */
    .card {
        padding: 1.5rem;
        border-radius: 10px;
        background: white;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
        margin-bottom: 1rem;
        border: 1px solid #e5e7eb;
    }
    
    /* Button styling */
    .stButton > button {
        border-radius: 8px;
        transition: all 0.3s;
        font-weight: 500;
    }
    
    .stButton > button:hover {
        transform: translateY(-2px);
        box-shadow: 0 4px 12px rgba(0,0,0,0.15);
    }
    
    /* Sidebar styling */
    .sidebar .sidebar-content {
        background-color: #f8fafc;
    }
    
    /* Status badges */
    .status-badge {
        display: inline-block;
        padding: 4px 12px;
        border-radius: 20px;
        font-size: 0.85rem;
        font-weight: 600;
    }
    
    .status-uploaded { background-color: #dbeafe; color: #1e40af; }
    .status-processing { background-color: #fef3c7; color: #92400e; }
    .status-completed { background-color: #d1fae5; color: #065f46; }
    .status-error { background-color: #fee2e2; color: #991b1b; }
    
    /* Progress bar */
    .stProgress > div > div {
        background-color: #3b82f6;
    }
    
    /* Hide Streamlit branding */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    
    /* Toast notification */
    .toast-success {
        background-color: #10b981;
        color: white;
        padding: 12px 20px;
        border-radius: 8px;
        position: fixed;
        top: 20px;
        right: 20px;
        z-index: 1000;
        animation: fadeInOut 3s;
    }
    
    @keyframes fadeInOut {
        0% { opacity: 0; transform: translateY(-20px); }
        10% { opacity: 1; transform: translateY(0); }
        90% { opacity: 1; transform: translateY(0); }
        100% { opacity: 0; transform: translateY(-20px); }
    }
    
    /* Summary box */
    .summary-box {
        background-color: #f8fafc;
        border-left: 4px solid #3b82f6;
        padding: 1.5rem;
        border-radius: 8px;
        margin: 1rem 0;
        line-height: 1.6;
    }
    
    /* Export buttons */
    .export-btn {
        margin: 5px;
        padding: 8px 16px;
        border-radius: 6px;
        border: none;
        cursor: pointer;
        font-weight: 500;
        transition: all 0.3s;
    }
    
    .export-txt { background-color: #3b82f6; color: white; }
    .export-pdf { background-color: #ef4444; color: white; }
    .export-copy { background-color: #10b981; color: white; }
    
    .export-btn:hover {
        opacity: 0.9;
        transform: scale(1.05);
    }
    
    /* Dark mode support */
    @media (prefers-color-scheme: dark) {
        .card {
            background-color: #1f2937;
            border-color: #374151;
        }
        
        .summary-box {
            background-color: #111827;
        }
    }
</style>
""", unsafe_allow_html=True)

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
        from frontend.dashboard import show_dashboard
        print("✅ dashboard imported as show_dashboard")
    except ImportError:
        try:
            from frontend.dashboard import dashboard_page as show_dashboard
            print("✅ dashboard imported as dashboard_page")
        except ImportError as e:
            print(f"❌ Could not import dashboard: {e}")
            def show_dashboard():
                st.title("📊 Dashboard")
                st.info("Welcome to your dashboard!")
                if st.button("Go to Upload"):
                    st.session_state.page = "upload"
                    st.rerun()
    
    # Try to import mybooks
    try:
        from frontend.mybooks import show_my_books
        print("✅ mybooks imported as show_my_books")
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
        print("✅ summaries imported as show_summaries_page")
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
        "role": "user",  # ✅ Default role
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
            st.session_state.role = user.get('role', 'user')  # ✅ Role set करें
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

# Create sidebar navigation - FIXED VERSION
def create_sidebar():
    """Create the sidebar navigation"""
    with st.sidebar:
        # App header
        st.markdown("""
        <div style="text-align: center; padding: 20px 0;">
            <h2 style="color: #3B82F6; margin-bottom: 5px;">📚</h2>
            <h4 style="color: #1E40AF; margin-top: 0; font-weight: 700;">
                Book Summarizer Pro
            </h4>
        </div>
        """, unsafe_allow_html=True)
        
        # User info if logged in
        if st.session_state.logged_in and st.session_state.user:
            user = st.session_state.user
            user_role = user.get('role', 'user')
            
            # User card
            st.markdown(f"""
            <div style="
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                color: white;
                padding: 15px;
                border-radius: 10px;
                margin-bottom: 20px;
            ">
                <div style="display: flex; align-items: center; margin-bottom: 10px;">
                    <div style="
                        width: 40px;
                        height: 40px;
                        background-color: white;
                        border-radius: 50%;
                        display: flex;
                        align-items: center;
                        justify-content: center;
                        margin-right: 10px;
                        color: #667eea;
                        font-size: 20px;
                    ">
                        👤
                    </div>
                    <div>
                        <h5 style="margin: 0; color: white; font-weight: 600;">
                            {user.get('name', 'User')}
                        </h5>
                        <p style="margin: 2px 0 0 0; font-size: 0.8em; opacity: 0.9;">
                            {user.get('email', '')}
                        </p>
                    </div>
                </div>
                {"<div style='background: rgba(255,255,255,0.2); padding: 2px 8px; border-radius: 12px; display: inline-block; font-size: 0.7em; font-weight: bold;'>👑 ADMIN</div>" if user_role == 'admin' else ""}
            </div>
            """, unsafe_allow_html=True)
        
        st.markdown("---")
        
        # Navigation menu
        st.markdown("### 🧭 Navigation")
        
        # Define navigation items based on login status
        if st.session_state.logged_in:
            # ✅ FIX: Get user_role from session state
            user_role = st.session_state.role
            
            nav_items = [
                {"name": "🏠 Dashboard", "page": "dashboard", "icon": "🏠"},
                {"name": "📤 Upload Book", "page": "upload", "icon": "📤"},
                {"name": "📚 My Books", "page": "mybooks", "icon": "📚"},
                {"name": "✨ Generate Summary", "page": "generate_summary", "icon": "✨"},
                {"name": "📝 All Summaries", "page": "summaries", "icon": "📝"},
            ]
            
            # Add advanced features if available
            if HISTORY_AVAILABLE:
                nav_items.append({"name": "🕰️ Version History", "page": "history", "icon": "🕰️"})
            
            if COMPARE_AVAILABLE:
                nav_items.append({"name": "🔍 Compare", "page": "compare", "icon": "🔍"})
            
            # Add admin dashboard if user is admin
            if user_role == 'admin' and ADMIN_AVAILABLE:
                nav_items.append({"name": "👑 Admin Dashboard", "page": "admin", "icon": "👑"})
            
            nav_items.append({"name": "🚪 Logout", "page": "logout", "icon": "🚪"})
        else:
            nav_items = [
                {"name": "🏠 Home", "page": "home", "icon": "🏠"},
                {"name": "🔐 Login", "page": "login", "icon": "🔐"},
                {"name": "📝 Register", "page": "register", "icon": "📝"},
            ]
        
        # Render navigation items
        current_page = st.session_state.page
        
        for item in nav_items:
            if st.button(
                f"{item['icon']} {item['name']}",
                key=f"nav_{item['page']}",
                use_container_width=True,
                type="primary" if current_page == item['page'] else "secondary"
            ):
                if item['page'] == "logout":
                    logout_user()
                else:
                    st.session_state.page = item['page']
                    st.rerun()
        
        st.markdown("---")
        
        # Quick stats
        if st.session_state.logged_in:
            try:
                from utils.database import get_books_by_user, get_summaries_by_user
                user_id = st.session_state.user_id
                
                books = get_books_by_user(user_id, limit=5)
                summaries = get_summaries_by_user(user_id)
                
                st.markdown("### 📊 Quick Stats")
                col1, col2 = st.columns(2)
                with col1:
                    st.metric("Books", len(books) if books else 0)
                with col2:
                    st.metric("Summaries", len(summaries) if summaries else 0)
            except Exception as e:
                print(f"Stats error: {e}")
                pass
        
        # Dark mode toggle
        st.markdown("---")
        dark_mode = st.toggle("🌙 Dark Mode", value=st.session_state.dark_mode)
        if dark_mode != st.session_state.dark_mode:
            st.session_state.dark_mode = dark_mode
            st.rerun()
        
        # App info
        st.markdown("---")
        st.caption("v2.0.0 • 📚 Intelligent Book Summarizer")
        st.caption("© 2024 All rights reserved")

# Home page
def show_home_page():
    """Show home page for non-authenticated users"""
    st.markdown('<h1 class="main-header">📚 Intelligent Book Summarizer Pro</h1>', unsafe_allow_html=True)
    st.markdown('<h3 class="sub-header" style="text-align: center; color: #6B7280;">AI-Powered Book Summarization Made Simple</h3>', unsafe_allow_html=True)
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.markdown("""
        <div class="card">
            <h3>🚀 Transform Your Reading Experience</h3>
            <p>Upload PDF, DOCX, or TXT books and get intelligent 
            summaries using advanced AI technology.</p>
            
            <h4>✨ Key Features:</h4>
            <ul>
            <li><strong>⚡ Instant AI Summaries</strong> - Get concise summaries in seconds</li>
            <li><strong>📁 Multi-Format Support</strong> - PDF, DOCX, TXT files</li>
            <li><strong>🔄 Version Control</strong> - Track and compare summary versions</li>
            <li><strong>📊 Analytics Dashboard</strong> - Monitor your reading patterns</li>
            <li><strong>📤 Export Options</strong> - TXT, PDF, and clipboard support</li>
            <li><strong>🔒 Secure & Private</strong> - Your data stays with you</li>
            </ul>
            
            <div style="margin-top: 2rem;">
            <p><strong>Ready to get started?</strong> Login or register for free!</p>
            </div>
        </div>
        """, unsafe_allow_html=True)
        
        col_a, col_b = st.columns(2)
        with col_a:
            if st.button("🔐 Login", use_container_width=True, type="primary"):
                st.session_state.page = "login"
                st.rerun()
        with col_b:
            if st.button("📝 Register", use_container_width=True):
                st.session_state.page = "register"
                st.rerun()
    
    with col2:
        st.image("https://img.icons8.com/clouds/300/000000/book-reading.png", use_column_width=True)
        
        # Quick demo
        st.markdown("""
        <div class="card">
            <h4>🎯 Try It Now</h4>
            <p>Experience the power of AI summarization:</p>
            <ol>
            <li>Upload any book file</li>
            <li>Choose summary length</li>
            <li>Get instant AI summary</li>
            <li>Export or save for later</li>
            </ol>
        </div>
        """, unsafe_allow_html=True)
    
    # Feature highlights
    st.markdown("---")
    st.subheader("🌟 Why Choose Our Summarizer?")
    
    features = st.columns(3)
    
    with features[0]:
        st.markdown("""
        <div class="card">
            <h4>🤖 Advanced AI</h4>
            <p>Uses state-of-the-art NLP models for accurate and coherent summaries.</p>
        </div>
        """, unsafe_allow_html=True)
    
    with features[1]:
        st.markdown("""
        <div class="card">
            <h4>⚡ Speed & Efficiency</h4>
            <p>Process large books quickly with our optimized pipeline.</p>
        </div>
        """, unsafe_allow_html=True)
    
    with features[2]:
        st.markdown("""
        <div class="card">
            <h4>🔧 Complete Toolset</h4>
            <p>Everything you need for book analysis in one place.</p>
        </div>
        """, unsafe_allow_html=True)

# Main routing function
# In your app.py, update the route function:
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
            show_auth_page("login")
        elif page == "register":
            show_auth_page("register")
        return
    
    # Private pages - require authentication
    if not check_authentication():
        st.session_state.page = "home"
        st.rerun()
        return
    
    # Show sidebar for authenticated users
    create_sidebar()
    
    # Route to appropriate page - FIXED FUNCTION CALLS
    try:
        if page == "dashboard":
            show_dashboard()
        elif page == "upload":
            show_upload_page()
        elif page == "mybooks":
            show_my_books()
        elif page == "generate_summary":
            summary_generation_page()
        elif page == "summaries":
            from frontend.summaries import show_summaries_page
            show_summaries_page()
        elif page == "history":
            from frontend.SummaryHistory import summary_history_page_wrapper
            summary_history_page_wrapper()  
        elif page == "compare":
            from frontend.summary_compare import show_summary_comparison
            show_summary_comparison()
        elif page == "admin":
            # Check admin permissions
            if st.session_state.role != "admin":
                st.error("❌ Admin access required")
                st.session_state.page = "dashboard"
                st.rerun()
                return
            show_admin_dashboard()
        elif page == "logout":
            logout_user()
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
    
    # Apply dark mode if enabled
    if st.session_state.dark_mode:
        st.markdown("""
        <style>
        .stApp {
            background-color: #0f172a;
            color: #f8fafc;
        }
        
        .card {
            background-color: #1e293b;
            border-color: #334155;
        }
        
        .summary-box {
            background-color: #1e293b;
        }
        </style>
        """, unsafe_allow_html=True)
    
    # Show header only on home page
    if st.session_state.page == "home" and not st.session_state.logged_in:
        pass  # Header already in home page
    else:
        # Small header for other pages
        if st.session_state.logged_in:
            st.markdown(f"### 📚 Welcome back, {st.session_state.username}!")
        else:
            st.markdown("### 📚 Book Summarizer Pro")
    
    # Route to appropriate page
    route()

# Run the app
if __name__ == "__main__":
    main()