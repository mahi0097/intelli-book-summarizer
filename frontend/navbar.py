import streamlit as st

def render_sidebar(user_name="User"):
    """
    Render the sidebar navigation menu
    
    Args:
        user_name (str): Name of the logged-in user to display in sidebar
    """
    with st.sidebar:
        # User greeting with styled container
        st.markdown(f"""
        <div style="padding: 1rem 0.5rem;">
            <h3 style="color: white; margin: 0; font-size: 1.3rem;">👋 {user_name}</h3>
        </div>
        """, unsafe_allow_html=True)
        
        st.markdown("---")
        
        # Main navigation buttons
        nav_items = [
            ("📊 Dashboard", "dashboard"),
            ("📤 Upload Book", "upload"),
            ("📚 My Books", "mybooks"),
            ("✨ Generate Summary", "generate_summary"),
            ("📜 All Summaries", "summaries"),
        ]
        
        for label, page in nav_items:
            if st.button(
                label, 
                key=f"sidebar_{page}", 
                use_container_width=True,
                help=f"Navigate to {label}"
            ):
                st.session_state.page = page
                st.rerun()
        
        st.markdown("---")
        st.markdown("### 🔧 Version Management")
        
        # Version management buttons
        version_items = [
            ("📜 Version History", "summary_history"),
            ("🔍 Compare Versions", "compare"),
            ("⭐ Favorite Summaries", "favorites"),
        ]
        
        for label, page in version_items:
            if st.button(
                label, 
                key=f"sidebar_{page}", 
                use_container_width=True,
                help=f"Go to {label}"
            ):
                st.session_state.page = page
                if page == "favorites":
                    st.session_state.show_favorites = True
                st.rerun()
        
        st.markdown("---")
        
        # User settings and logout
        with st.expander("👤 Account Settings", expanded=False):
            if st.button("👤 Profile", key="sidebar_profile", use_container_width=True):
                st.session_state.page = "profile"
                st.rerun()
            
            if st.button("⚙️ Settings", key="sidebar_settings", use_container_width=True):
                st.session_state.page = "settings"
                st.rerun()
        
        # Logout button with different styling
        st.markdown("<br>", unsafe_allow_html=True)
        if st.button(
            "🚪 Logout", 
            key="sidebar_logout", 
            use_container_width=True,
            type="secondary"
        ):
            # Clear session state but keep the page
            for key in list(st.session_state.keys()):
                if key != "page":
                    del st.session_state[key]
            st.session_state.page = "login"
            st.rerun()
        
        # App version info
        st.markdown("---")
        st.markdown("""
        <div style="text-align: center; color: rgba(255,255,255,0.5); font-size: 0.8rem; padding: 1rem 0;">
            📚 Intelligent Book Summarizer<br>
            Version 2.0.0
        </div>
        """, unsafe_allow_html=True)


def get_sidebar_css():
    """
    Returns CSS styling for the sidebar.
    This can be included in your main app's CSS or called separately.
    """
    return """
    <style>
    /* Sidebar Navigation Styling */
    section[data-testid="stSidebar"] {
        min-width: 280px !important;
        background: linear-gradient(180deg, #0f172a, #1e3a8a) !important;
    }
    
    section[data-testid="stSidebar"] > div {
        padding: 2rem 1rem !important;
    }
    
    /* Sidebar text colors */
    section[data-testid="stSidebar"] .stMarkdown,
    section[data-testid="stSidebar"] .stMarkdown h3,
    section[data-testid="stSidebar"] .stMarkdown p {
        color: white !important;
    }
    
    /* Sidebar buttons */
    section[data-testid="stSidebar"] .stButton > button {
        width: 100% !important;
        background: rgba(255, 255, 255, 0.1) !important;
        color: white !important;
        border: 1px solid rgba(255, 255, 255, 0.2) !important;
        border-radius: 12px !important;
        padding: 0.75rem 1rem !important;
        font-weight: 500 !important;
        font-size: 0.95rem !important;
        text-align: left !important;
        margin-bottom: 0.5rem !important;
        transition: all 0.3s ease !important;
        backdrop-filter: blur(10px) !important;
    }
    
    section[data-testid="stSidebar"] .stButton > button:hover {
        background: rgba(255, 255, 255, 0.25) !important;
        border-color: rgba(255, 255, 255, 0.4) !important;
        transform: translateX(5px) !important;
        box-shadow: 0 5px 15px rgba(0, 0, 0, 0.2) !important;
    }
    
    section[data-testid="stSidebar"] .stButton > button:active {
        background: rgba(255, 255, 255, 0.3) !important;
    }
    
    /* Expander in sidebar */
    section[data-testid="stSidebar"] .streamlit-expanderHeader {
        background: rgba(255, 255, 255, 0.1) !important;
        color: white !important;
        border: 1px solid rgba(255, 255, 255, 0.2) !important;
        border-radius: 12px !important;
        font-weight: 500 !important;
    }
    
    section[data-testid="stSidebar"] .streamlit-expanderContent {
        background: rgba(255, 255, 255, 0.05) !important;
        border: 1px solid rgba(255, 255, 255, 0.1) !important;
        border-top: none !important;
        border-radius: 0 0 12px 12px !important;
        padding: 0.5rem !important;
    }
    
    /* Sidebar divider */
    section[data-testid="stSidebar"] hr {
        border-color: rgba(255, 255, 255, 0.2) !important;
        margin: 1rem 0 !important;
    }
    
    /* Custom scrollbar for sidebar */
    section[data-testid="stSidebar"] ::-webkit-scrollbar {
        width: 6px;
    }
    
    section[data-testid="stSidebar"] ::-webkit-scrollbar-track {
        background: rgba(255, 255, 255, 0.1);
    }
    
    section[data-testid="stSidebar"] ::-webkit-scrollbar-thumb {
        background: rgba(255, 255, 255, 0.3);
        border-radius: 3px;
    }
    
    section[data-testid="stSidebar"] ::-webkit-scrollbar-thumb:hover {
        background: rgba(255, 255, 255, 0.4);
    }
    
    /* Make sidebar text always white */
    section[data-testid="stSidebar"] p,
    section[data-testid="stSidebar"] span,
    section[data-testid="stSidebar"] div:not(.stButton) {
        color: white !important;
    }
    </style>
    """


def require_auth():
    """
    Decorator function to check if user is authenticated.
    Can be used at the beginning of each page that requires login.
    """
    from frontend.helper import is_logged_in
    
    if not is_logged_in():
        st.error("⚠️ Please login to access this page")
        st.session_state.page = "login"
        st.stop()
        return False
    return True


def get_user_info():
    """
    Helper function to get current user info
    Returns tuple of (user_name, user_id)
    """
    from frontend.helper import get_current_user
    
    user = get_current_user()
    if isinstance(user, dict):
        user_name = user.get('name', user.get('username', 'User'))
        user_id = user.get('user_id') or user.get('_id')
    else:
        user_name = "User"
        user_id = None
    
    return user_name, user_id