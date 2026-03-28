import streamlit as st


def render_sidebar(user_name="User"):
    """
    Render the sidebar navigation menu.

    Args:
        user_name (str): Name of the logged-in user to display in sidebar.
    """
    safe_user_name = str(user_name or "User").strip() or "User"

    with st.sidebar:
        st.markdown(
            f"""
            <div class="sidebar-brand-card">
                <div class="sidebar-brand-eyebrow">Workspace</div>
                <h3 class="sidebar-brand-title">Intelligent Book Summarizer</h3>
                <p class="sidebar-brand-subtitle">Welcome back, {safe_user_name}</p>
            </div>
            """,
            unsafe_allow_html=True,
        )

        st.markdown('<div class="sidebar-section-label">Main Menu</div>', unsafe_allow_html=True)

        nav_items = [
            ("Dashboard", "dashboard"),
            ("Upload Book", "upload"),
            ("My Books", "mybooks"),
            ("Generate Summary", "generate_summary"),
            ("All Summaries", "summaries"),
        ]

        for label, page in nav_items:
            if st.button(
                label,
                key=f"sidebar_{page}",
                use_container_width=True,
                help=f"Navigate to {label}",
            ):
                st.session_state.page = page
                st.rerun()

        st.markdown(
            '<div class="sidebar-section-label">Version Management</div>',
            unsafe_allow_html=True,
        )

        version_items = [
            ("Version History", "summary_history"),
            ("Compare Versions", "compare"),
            ("Favorite Summaries", "favorites"),
        ]

        for label, page in version_items:
            if st.button(
                label,
                key=f"sidebar_{page}",
                use_container_width=True,
                help=f"Go to {label}",
            ):
                st.session_state.page = page
                if page == "favorites":
                    st.session_state.show_favorites = True
                st.rerun()

        st.markdown('<div class="sidebar-section-label">Account</div>', unsafe_allow_html=True)

        with st.expander("Account Settings", expanded=False):
            if st.button("Profile", key="sidebar_profile", use_container_width=True):
                st.session_state.page = "profile"
                st.rerun()

            if st.button("Settings", key="sidebar_settings", use_container_width=True):
                st.session_state.page = "settings"
                st.rerun()

        st.markdown("<br>", unsafe_allow_html=True)
        if st.button(
            "Logout",
            key="sidebar_logout",
            use_container_width=True,
            type="secondary",
        ):
            for key in list(st.session_state.keys()):
                if key != "page":
                    del st.session_state[key]
            st.session_state.page = "login"
            st.rerun()

        st.markdown(
            """
            <div class="sidebar-footer-card">
                <div class="sidebar-footer-title">Intelligent Book Summarizer</div>
                <div class="sidebar-footer-version">Version 2.0.0</div>
            </div>
            """,
            unsafe_allow_html=True,
        )


def get_sidebar_css():
    """
    Return CSS styling for the sidebar.

    This can be included in the main app CSS or injected separately.
    """
    return """
    <style>
    section[data-testid="stSidebar"] {
        min-width: 280px !important;
        background:
            radial-gradient(circle at top, rgba(255, 255, 255, 0.08), transparent 28%),
            linear-gradient(180deg, #0f172a 0%, #102a43 48%, #0b132b 100%) !important;
    }

    section[data-testid="stSidebar"] > div {
        padding: 1.4rem 1rem 1rem !important;
    }

    section[data-testid="stSidebar"] * {
        font-family: "Segoe UI", "Inter", sans-serif !important;
    }

    .sidebar-brand-card {
        padding: 1.1rem 1rem;
        margin-bottom: 1rem;
        background: linear-gradient(180deg, rgba(255, 255, 255, 0.18), rgba(255, 255, 255, 0.08));
        border: 1px solid rgba(191, 219, 254, 0.24);
        border-radius: 18px;
        box-shadow: 0 16px 40px rgba(8, 15, 35, 0.28);
        backdrop-filter: blur(12px);
    }

    .sidebar-brand-eyebrow {
        color: #93c5fd !important;
        font-size: 0.72rem;
        font-weight: 700;
        letter-spacing: 0.08em;
        text-transform: uppercase;
        margin-bottom: 0.4rem;
    }

    .sidebar-brand-title {
        color: #f8fafc !important;
        margin: 0 !important;
        font-size: 1.1rem !important;
        line-height: 1.35 !important;
        font-weight: 700 !important;
    }

    .sidebar-brand-subtitle {
        color: #dbeafe !important;
        margin: 0.45rem 0 0 !important;
        font-size: 0.92rem !important;
        line-height: 1.45 !important;
    }

    .sidebar-section-label {
        color: #bfdbfe !important;
        font-size: 0.76rem;
        font-weight: 700;
        letter-spacing: 0.08em;
        text-transform: uppercase;
        margin: 1rem 0 0.65rem;
        padding-left: 0.35rem;
    }

    section[data-testid="stSidebar"] .stButton > button {
        width: 100% !important;
        background: rgba(248, 250, 252, 0.08) !important;
        color: #e2e8f0 !important;
        border: 1px solid rgba(148, 163, 184, 0.18) !important;
        border-radius: 14px !important;
        padding: 0.8rem 0.95rem !important;
        font-weight: 600 !important;
        font-size: 0.95rem !important;
        text-align: left !important;
        margin-bottom: 0.45rem !important;
        transition: all 0.22s ease !important;
        backdrop-filter: blur(10px) !important;
        box-shadow: none !important;
    }

    section[data-testid="stSidebar"] .stButton > button:hover {
        background: linear-gradient(90deg, rgba(59, 130, 246, 0.26), rgba(14, 165, 233, 0.18)) !important;
        color: #f8fafc !important;
        border-color: rgba(147, 197, 253, 0.45) !important;
        transform: translateX(3px) !important;
        box-shadow: 0 10px 24px rgba(15, 23, 42, 0.24) !important;
    }

    section[data-testid="stSidebar"] .stButton > button:active {
        background: rgba(37, 99, 235, 0.28) !important;
    }

    section[data-testid="stSidebar"] .stButton > button:focus,
    section[data-testid="stSidebar"] .stButton > button:focus-visible {
        color: #f8fafc !important;
        border-color: rgba(191, 219, 254, 0.8) !important;
        box-shadow: 0 0 0 0.18rem rgba(96, 165, 250, 0.24) !important;
    }

    section[data-testid="stSidebar"] .streamlit-expanderHeader {
        background: rgba(248, 250, 252, 0.08) !important;
        color: #e2e8f0 !important;
        border: 1px solid rgba(148, 163, 184, 0.18) !important;
        border-radius: 14px !important;
        font-weight: 600 !important;
    }

    section[data-testid="stSidebar"] .streamlit-expanderContent {
        background: rgba(15, 23, 42, 0.24) !important;
        border: 1px solid rgba(148, 163, 184, 0.14) !important;
        border-top: none !important;
        border-radius: 0 0 14px 14px !important;
        padding: 0.55rem !important;
    }

    section[data-testid="stSidebar"] [data-testid="stMarkdownContainer"] p,
    section[data-testid="stSidebar"] [data-testid="stMarkdownContainer"] span,
    section[data-testid="stSidebar"] label,
    section[data-testid="stSidebar"] small {
        color: #dbeafe !important;
    }

    section[data-testid="stSidebar"] ::-webkit-scrollbar {
        width: 6px;
    }

    section[data-testid="stSidebar"] ::-webkit-scrollbar-track {
        background: rgba(255, 255, 255, 0.08);
    }

    section[data-testid="stSidebar"] ::-webkit-scrollbar-thumb {
        background: rgba(148, 163, 184, 0.45);
        border-radius: 999px;
    }

    section[data-testid="stSidebar"] ::-webkit-scrollbar-thumb:hover {
        background: rgba(191, 219, 254, 0.55);
    }

    .sidebar-footer-card {
        margin-top: 1.2rem;
        padding: 0.95rem 0.85rem;
        border-radius: 16px;
        background: rgba(15, 23, 42, 0.3);
        border: 1px solid rgba(148, 163, 184, 0.14);
        text-align: center;
    }

    .sidebar-footer-title {
        color: #e2e8f0 !important;
        font-size: 0.84rem;
        font-weight: 600;
    }

    .sidebar-footer-version {
        color: #93c5fd !important;
        font-size: 0.76rem;
        margin-top: 0.22rem;
    }
    </style>
    """


def require_auth():
    """
    Check whether the current user is authenticated.

    Returns:
        bool: True if the user is logged in, otherwise stops the page.
    """
    from frontend.helper import is_logged_in

    if not is_logged_in():
        st.error("Please log in to access this page.")
        st.session_state.page = "login"
        st.stop()
        return False
    return True


def get_user_info():
    """
    Get current user information.

    Returns:
        tuple[str, str | None]: The user display name and user id.
    """
    from frontend.helper import get_current_user

    user = get_current_user()
    if isinstance(user, dict):
        user_name = user.get("name", user.get("username", "User"))
        user_id = user.get("user_id") or user.get("_id")
    else:
        user_name = "User"
        user_id = None

    return user_name, user_id
