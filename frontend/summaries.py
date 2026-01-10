# frontend/summaries.py - UPDATED VERSION

import streamlit as st
import sys
import os
from datetime import datetime
from bson import ObjectId

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from utils.database import get_db
from frontend.helper import get_current_user, is_logged_in

def show_summaries_page():
    """Display all user summaries with comparison option"""
    if not is_logged_in():
        st.error("Login required")
        st.session_state.page = "login"
        st.rerun()
        return
    
    user = get_current_user()
    if not user or "user_id" not in user:
        st.error("Invalid session. Please login again.")
        st.session_state.page = "login"
        st.rerun()
        return
    
    st.title("📚 My Summaries")
    
    # Add helpful instructions
    with st.expander("📋 How to compare summary versions", expanded=True):
        st.markdown("""
        ### 🔍 To compare summary versions:
        
        1. **Find a book with multiple versions** below
        2. **Click the "🔍 Compare" button** on any version
        3. **Select two versions** to compare
        4. **View differences** highlighted in color
        
        **Tip:** Create multiple versions by generating summaries with different settings.
        """)
    
    # Normalize user_id
    user_id = user["user_id"]
    try:
        if isinstance(user_id, str):
            user_obj_id = ObjectId(user_id)
        else:
            user_obj_id = user_id
    except:
        st.error("Invalid user ID format")
        return
    
    # Get user's summaries
    db = get_db()
    try:
        summaries = list(db.summaries.find({
            "user_id": user_obj_id
        }).sort("created_at", -1))
    except Exception as e:
        st.error(f"Error loading summaries: {str(e)}")
        summaries = []
    
    if not summaries:
        st.info("""
        📭 **No summaries generated yet.**
        
        **To get started:**
        1. Upload a book from the **Upload Book** page
        2. Generate a summary from the **Generate Summary** page
        3. Create another summary for the same book with different settings
        4. Come back here to compare them!
        """)
        
        col1, col2 = st.columns(2)
        with col1:
            if st.button("📤 Upload Book", use_container_width=True):
                st.session_state.page = "upload"
                st.rerun()
        with col2:
            if st.button("✨ Generate Summary", use_container_width=True):
                st.session_state.page = "generate_summary"
                st.rerun()
        return
    
    # Group summaries by book
    books_dict = {}
    for summary in summaries:
        book_id = str(summary.get("book_id", ""))
        if book_id not in books_dict:
            # Get book info
            try:
                book = db.books.find_one({"_id": ObjectId(book_id)})
            except:
                book = None
            books_dict[book_id] = {
                "book_info": book,
                "summaries": []
            }
        books_dict[book_id]["summaries"].append(summary)
    
    # Display summaries by book
    for book_id, data in books_dict.items():
        book = data["book_info"]
        book_summaries = data["summaries"]
        
        # Sort by version (newest first)
        book_summaries.sort(key=lambda x: x.get("version", 0), reverse=True)
        
        # Display book header
        st.markdown("---")
        
        if book:
            book_title = book.get("title", "Untitled Book")
            author = book.get("author", "Unknown Author")
            version_count = len(book_summaries)
            
            col_header1, col_header2 = st.columns([3, 1])
            
            with col_header1:
                st.subheader(f"📘 {book_title}")
                if author and author != "Unknown Author":
                    st.caption(f"by {author}")
                st.caption(f"{version_count} version{'s' if version_count != 1 else ''}")
            
            with col_header2:
                # Show compare button if multiple versions
                if version_count > 1:
                    if st.button("🔍 Compare All", 
                               key=f"compare_all_{book_id}", 
                               use_container_width=True,
                               type="primary"):
                        st.session_state.selected_book_for_comparison = book_id
                        st.session_state.page = "compare"
                        st.rerun()
        
        # Display each summary version
        for summary in book_summaries:
            summary_id = str(summary.get("_id", ""))
            
            with st.expander(f"📄 Version {summary.get('version', 1)}", expanded=False):
                col_sum1, col_sum2 = st.columns([3, 1])
                
                with col_sum1:
                    # Summary metadata
                    created_at = summary.get("created_at", "")
                    if isinstance(created_at, datetime):
                        created_str = created_at.strftime("%Y-%m-%d %H:%M")
                    else:
                        created_str = str(created_at)[:16]
                    
                    # Show badges
                    badges = []
                    if summary.get("is_favorite"):
                        badges.append("⭐ Favorite")
                    if summary.get("is_default") or summary.get("is_active"):
                        badges.append("✅ Default")
                    
                    st.caption(f"Created: {created_str}")
                    if badges:
                        st.caption(" • ".join(badges))
                    
                    # Summary text (truncated)
                    summary_text = summary.get("summary_text", "No content")
                    word_count = len(summary_text.split())
                    
                    if len(summary_text) > 300:
                        st.write(f"{summary_text[:300]}...")
                        st.caption(f"{word_count} words (truncated)")
                        if st.button("📖 Read Full", key=f"read_{summary_id}"):
                            st.text_area("Full Summary", 
                                       value=summary_text, 
                                       height=200,
                                       key=f"full_{summary_id}")
                    else:
                        st.write(summary_text)
                        st.caption(f"{word_count} words")
                
                with col_sum2:
                    # Action buttons in a vertical layout
                    if st.button("⭐" if not summary.get("is_favorite") else "★", 
                               key=f"fav_{summary_id}",
                               help="Toggle favorite"):
                        # Toggle favorite
                        new_status = not summary.get("is_favorite", False)
                        db.summaries.update_one(
                            {"_id": ObjectId(summary_id)},
                            {"$set": {"is_favorite": new_status}}
                        )
                        st.success("Favorite status updated!")
                        st.rerun()
                    
                    if not summary.get("is_default") and not summary.get("is_active"):
                        if st.button("📌", 
                                   key=f"default_{summary_id}",
                                   help="Set as default"):
                            # Set as default
                            try:
                                # First, set all summaries for this book as not default
                                db.summaries.update_many(
                                    {"book_id": ObjectId(book_id), "user_id": user_obj_id},
                                    {"$set": {"is_default": False, "is_active": False}}
                                )
                                
                                # Then set this as default
                                db.summaries.update_one(
                                    {"_id": ObjectId(summary_id)},
                                    {"$set": {"is_default": True, "is_active": True}}
                                )
                                
                                st.success("Set as default version!")
                                st.rerun()
                            except Exception as e:
                                st.error(f"Error: {str(e)}")
                
                # Compare button (only show if multiple versions)
                if len(book_summaries) > 1:
                    st.markdown("---")
                    if st.button("🔍 Compare with other versions", 
                               key=f"compare_{summary_id}",
                               use_container_width=True):
                        st.session_state.selected_book_for_comparison = book_id
                        st.session_state.selected_summary = summary_id
                        st.session_state.page = "compare"
                        st.rerun()
    
    # Statistics at bottom
    st.markdown("---")
    st.subheader("📊 Summary Statistics")
    
    total_summaries = len(summaries)
    total_books = len(books_dict)
    favorite_count = sum(1 for s in summaries if s.get("is_favorite"))
    default_count = sum(1 for s in summaries if s.get("is_default") or s.get("is_active"))
    
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Total Summaries", total_summaries)
    with col2:
        st.metric("Books with Summaries", total_books)
    with col3:
        st.metric("Favorite Summaries", favorite_count)
    with col4:
        st.metric("Default Summaries", default_count)

# Alias for app.py
def summaries_page():
    show_summaries_page()