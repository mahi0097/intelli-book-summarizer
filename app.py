# app.py
import streamlit as st
import sys
import os
from datetime import datetime

sys.path.append(os.path.abspath(os.path.dirname(__file__)))

from frontend.auth import login_page, registration_page
from frontend.dashboard import dashboard_page
from frontend.upload import upload_page
from frontend.mybooks import mybooks_page
from frontend.generate_summary import summary_generation_page
from backend.auth import is_logged_in, get_current_user

# Initialize session state
def init_session_state():
    """Initialize all session state variables"""
    defaults = {
        "page": "login",
        "logged_in": False,
        "user_id": None,
        "username": None,
        "role": "user",
        "last_activity": datetime.now(),
        "current_book": None,
        "current_summary": None,
        "show_sidebar": True
    }
    
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value

# Apply custom CSS
def apply_custom_css():
    st.markdown("""
    <style>
    /* Main styling */
    .main-header {
        font-size: 2.5rem;
        font-weight: bold;
        color: #1E3A8A;
        margin-bottom: 1rem;
    }
    
    /* Sidebar styling */
    .sidebar .sidebar-content {
        background-color: #f8f9fa;
    }
    
    /* Button styling */
    .stButton > button {
        border-radius: 8px;
        transition: all 0.3s;
    }
    
    .stButton > button:hover {
        transform: translateY(-2px);
        box-shadow: 0 4px 12px rgba(0,0,0,0.1);
    }
    
    /* Hide Streamlit branding */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    </style>
    """, unsafe_allow_html=True)

# Create sidebar navigation
def create_sidebar():
    """Create the sidebar navigation"""
    with st.sidebar:
        # Logo and app name
        st.markdown("""
        <div style="text-align: center; padding: 20px 0;">
            <h2 style="color: #3B82F6; margin-bottom: 5px;">📚</h2>
            <h4 style="color: #1E40AF; margin-top: 0;">Book Summarizer</h4>
        </div>
        """, unsafe_allow_html=True)
        
        # User info if logged in
        if st.session_state.logged_in:
            user = get_current_user(st.session_state)
            st.markdown(f"""
            <div style="background-color: #DBEAFE; padding: 15px; border-radius: 10px; margin-bottom: 20px;">
                <h5 style="margin: 0; color: #1E40AF;">👤 {user.get('name', 'User')}</h5>
                <p style="margin: 5px 0 0 0; color: #4B5563; font-size: 0.8em;">{user.get('email', '')}</p>
            </div>
            """, unsafe_allow_html=True)
        
        st.markdown("---")
        
        # Navigation menu
        st.markdown("### 🧭 Navigation")
        
        # Define navigation items
        nav_items = []
        
        if st.session_state.logged_in:
            nav_items = [
                {"name": "🏠 Dashboard", "page": "dashboard", "icon": ""},
                {"name": "📤 Upload Book", "page": "upload", "icon": ""},
                {"name": "📚 My Books", "page": "mybooks", "icon": ""},
                {"name": "✨ Generate Summary", "page": "generate_summary", "icon": ""},
            ]
            
            # Check if user is admin
            if st.session_state.get("role") == "admin":
                nav_items.append({"name": "👑 Admin", "page": "admin", "icon": "👑"})
            
            nav_items.append({"name": "🚪 Logout", "page": "logout", "icon": ""})
        else:
            nav_items = [
                {"name": "🔐 Login", "page": "login", "icon": "🔐"},
                {"name": "📝 Register", "page": "register", "icon": "📝"},
            ]
        
        # Render navigation items
        current_page = st.session_state.page
        
        for item in nav_items:
            col1, col2 = st.columns([1, 4])
            with col1:
                st.write(item["icon"])
            with col2:
                if st.button(
                    item["name"],
                    key=f"nav_{item['page']}",
                    use_container_width=True,
                    type="primary" if current_page == item["page"] else "secondary"
                ):
                    if item["page"] == "logout":
                        logout_user()
                    else:
                        st.session_state.page = item["page"]
                        st.rerun()
        
        st.markdown("---")
        
        # Quick actions for logged-in users
        if st.session_state.logged_in:
            st.markdown("### ⚡ Quick Actions")
            
            from utils.database import db
            from bson import ObjectId
            
            # Quick summarize recent books
            recent_books = list(db.books.find(
                {"user_id": ObjectId(st.session_state.user_id)}
            ).sort("uploaded_at", -1).limit(3))
            
            if recent_books:
                for book in recent_books:
                    book_title = book.get("title", "Untitled")
                    if len(book_title) > 20:
                        book_title = book_title[:20] + "..."
                    
                    if st.button(
                        f"📝 {book_title}",
                        key=f"quick_{book['_id']}",
                        use_container_width=True,
                        help=f"Generate summary for {book.get('title')}"
                    ):
                        st.session_state.current_book = str(book["_id"])
                        st.session_state.page = "generate_summary"
                        st.rerun()

# Logout function
def logout_user():
    """Logout the current user"""
    st.session_state.logged_in = False
    st.session_state.user_id = None
    st.session_state.username = None
    st.session_state.role = "user"
    st.session_state.page = "login"
    st.success("Logged out successfully!")
    st.rerun()

# Route to the appropriate page
def route():
    page = st.session_state.page
    
    # Public pages
    if page == "login":
        login_page()
    elif page == "register":
        registration_page()
    else:
        # Private pages - require login
        if not is_logged_in(st.session_state):
            st.session_state.page = "login"
            st.rerun()
        
        # Show sidebar for all private pages
        create_sidebar()
        
        # Route to the appropriate page
        if page == "dashboard":
            dashboard_page()
        elif page == "upload":
            upload_page()
        elif page == "mybooks":
            mybooks_page()
        elif page == "generate_summary":
            summary_generation_page()
        elif page == "admin":
            admin_page()
        elif page == "logout":
            logout_user()
        else:
            st.error(f"Page '{page}' not found")
            # Provide a way to go back to dashboard
            if st.button("Back to Dashboard"):
                st.session_state.page = "dashboard"
                st.rerun()

def admin_page():
    """Admin panel"""
    st.title("👑 Admin Panel")
    
    if st.session_state.get("role") != "admin":
        st.error("Admin access required")
        return
    
    from utils.database import db
    
    tab1, tab2 = st.tabs(["📊 Stats", "👥 Users"])
    
    with tab1:
        # System statistics
        col1, col2, col3 = st.columns(3)
        
        with col1:
            total_users = db.users.count_documents({})
            st.metric("Total Users", total_users)
        
        with col2:
            total_books = db.books.count_documents({})
            st.metric("Total Books", total_books)
        
        with col3:
            total_summaries = db.summaries.count_documents({})
            st.metric("Total Summaries", total_summaries)
    
    with tab2:
        # User management
        users = list(db.users.find().sort("created_at", -1).limit(50))
        
        for user in users:
            with st.expander(f"👤 {user.get('name', 'Unknown')} - {user.get('email', '')}"):
                col1, col2 = st.columns(2)
                with col1:
                    st.write(f"**Role:** {user.get('role', 'user')}")
                    st.write(f"**Joined:** {user.get('created_at', 'N/A')}")
                with col2:
                    user_books = db.books.count_documents({"user_id": user["_id"]})
                    st.write(f"**Books:** {user_books}")

# Main app execution
if __name__ == "__main__":
    # Initialize session state
    init_session_state()
    
    # Apply custom CSS
    apply_custom_css()
    
    # Set page config
    st.set_page_config(
        page_title="Intelligent Book Summarizer",
        page_icon="📚",
        layout="wide",
        initial_sidebar_state="expanded"
    )
    
    # Route to appropriate page
    route()