import streamlit as st
from bson import ObjectId
from utils.database import (
    get_user_summaries_with_pagination,
    get_book_summary_versions,
    update_summary_metadata,
    delete_summary,
    restore_summary,
    set_active_summary_version,
    get_summary_by_id
)

def summary_management_page():
    """Summary management interface"""
    st.title("📚 Summary Management")
    
    # Check authentication
    if "user_id" not in st.session_state:
        st.error("Please log in to manage summaries")
        st.session_state.page = "login"
        st.rerun()
        return
    
    user_id = st.session_state["user_id"]
    
    # Sidebar filters
    with st.sidebar:
        st.header("🔍 Filters")
        
        # Book filter
        books = list(db.books.find({"user_id": ObjectId(user_id)}))
        book_options = [{"id": None, "title": "All Books"}]
        book_options.extend([{"id": str(b["_id"]), "title": b.get("title", "Untitled")} for b in books])
        
        selected_book = st.selectbox(
            "Filter by Book",
            options=book_options,
            format_func=lambda x: x["title"]
        )
        
        # Status filter
        status_filter = st.selectbox(
            "Filter by Status",
            options=["All", "Active Only", "Inactive Only"]
        )
        
        # Word count range
        min_words = st.number_input("Min Word Count", min_value=0, value=0)
        max_words = st.number_input("Max Word Count", min_value=0, value=1000)
    
    # Build filters
    filters = {}
    if selected_book["id"]:
        filters["book_id"] = selected_book["id"]
    
    if status_filter == "Active Only":
        filters["is_active"] = True
    elif status_filter == "Inactive Only":
        filters["is_active"] = False
    
    if min_words > 0:
        filters["min_word_count"] = min_words
    if max_words > 0:
        filters["max_word_count"] = max_words
    
    # Pagination
    page = st.number_input("Page", min_value=1, value=1)
    limit = st.selectbox("Items per page", options=[10, 20, 50], index=1)
    
    # Get summaries
    result = get_user_summaries_with_pagination(
        user_id=user_id,
        page=page,
        limit=limit,
        filters=filters
    )
    
    # Display summary count
    st.subheader(f"📊 Found {result['total']} summaries")
    
    # Display summaries
    for summary in result["summaries"]:
        with st.expander(f"📖 {summary.get('book_title', 'Unknown Book')} - Version {summary.get('version', 1)}"):
            col1, col2, col3 = st.columns(3)
            
            with col1:
                st.metric("Words", summary.get("word_count", 0))
            
            with col2:
                status = "✅ Active" if summary.get("is_active") else "❌ Inactive"
                st.write(status)
            
            with col3:
                st.write(f"📅 {summary.get('created_at', '').strftime('%Y-%m-%d')}")
            
            # Display summary text
            st.markdown("#### Summary:")
            st.write(summary.get("summary_text", "")[:500] + "..." if len(summary.get("summary_text", "")) > 500 else summary.get("summary_text", ""))
            
            # Action buttons
            action_col1, action_col2, action_col3 = st.columns(3)
            
            with action_col1:
                if st.button("📝 Edit", key=f"edit_{summary['_id']}"):
                    st.session_state.edit_summary_id = summary["_id"]
                    st.rerun()
            
            with action_col2:
                if st.button("🗑️ Delete", key=f"delete_{summary['_id']}"):
                    if delete_summary(summary["_id"], user_id, permanent=False):
                        st.success("Summary soft deleted")
                        st.rerun()
            
            with action_col3:
                if not summary.get("is_active"):
                    if st.button("🔄 Restore", key=f"restore_{summary['_id']}"):
                        if restore_summary(summary["_id"], user_id):
                            st.success("Summary restored")
                            st.rerun()
    
    # Edit summary modal
    if "edit_summary_id" in st.session_state:
        edit_summary_modal(st.session_state.edit_summary_id, user_id)
    
    # Version management section
    st.markdown("---")
    st.subheader("🔄 Version Management")
    
    # Select book for version management
    version_book = st.selectbox(
        "Select Book to Manage Versions",
        options=books,
        format_func=lambda b: b.get("title", "Untitled"),
        key="version_book"
    )
    
    if version_book:
        versions = get_book_summary_versions(str(version_book["_id"]), user_id)
        
        if versions:
            # Display versions table
            for version in versions:
                col1, col2, col3, col4 = st.columns([3, 2, 2, 1])
                
                with col1:
                    st.write(f"Version {version.get('version', 1)}")
                    if version.get("is_active"):
                        st.success("Active Version")
                
                with col2:
                    st.write(f"{version.get('word_count', 0)} words")
                
                with col3:
                    st.write(version.get("created_at", "").strftime("%Y-%m-%d"))
                
                with col4:
                    if not version.get("is_active"):
                        if st.button("Set Active", key=f"set_active_{version['_id']}"):
                            if set_active_summary_version(str(version_book["_id"]), user_id, version["version"]):
                                st.success(f"Version {version['version']} set as active")
                                st.rerun()
        else:
            st.info("No versions found for this book")

def edit_summary_modal(summary_id, user_id):
    """Modal for editing summary metadata"""
    summary = get_summary_by_id(summary_id)
    
    if not summary:
        st.error("Summary not found")
        return
    
    with st.form(f"edit_form_{summary_id}"):
        st.subheader("Edit Summary Metadata")
        
        # Editable fields
        tags = st.text_input("Tags (comma-separated)", value=",".join(summary.get("tags", [])))
        is_favorite = st.checkbox("Mark as Favorite", value=summary.get("is_favorite", False))
        rating = st.slider("Rating", 1, 5, value=summary.get("rating", 3) or 3)
        feedback = st.text_area("Feedback", value=summary.get("feedback", ""))
        access_level = st.selectbox(
            "Access Level",
            options=["private", "public", "shared"],
            index=["private", "public", "shared"].index(summary.get("access_level", "private"))
        )
        
        submitted = st.form_submit_button("Save Changes")
        
        if submitted:
            updates = {
                "tags": [tag.strip() for tag in tags.split(",") if tag.strip()],
                "is_favorite": is_favorite,
                "rating": rating,
                "feedback": feedback,
                "access_level": access_level
            }
            
            if update_summary_metadata(summary_id, user_id, updates):
                st.success("Summary updated successfully")
                del st.session_state.edit_summary_id
                st.rerun()
            else:
                st.error("Failed to update summary")