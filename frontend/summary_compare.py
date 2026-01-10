# frontend/summary_compare.py - SIMPLE WORKING VERSION

import streamlit as st
import difflib
from datetime import datetime
from bson import ObjectId
import sys
import os

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from utils.database import (
    get_db,
    get_book_by_id,
    get_summary_by_id,
    set_active_summary_version,
    update_summary_metadata,
    delete_summary,
    restore_summary
)

def show_summary_comparison():
    """Main comparison page - SIMPLE VERSION THAT WORKS"""
    
    # Check authentication
    if not st.session_state.get("logged_in", False):
        st.error("Please login to access this page")
        st.session_state.page = "login"
        st.rerun()
        return
    
    st.title("🔍 Compare Summary Versions")
    
    # Navigation
    col_nav1, col_nav2 = st.columns([3, 1])
    with col_nav1:
        st.caption("Navigate: Dashboard → Summaries → Compare")
    with col_nav2:
        if st.button("⬅ Back to Summaries", use_container_width=True):
            st.session_state.page = "summaries"
            st.rerun()
    
    # ============================================
    # STEP 1: GET BOOK TO COMPARE
    # ============================================
    book_id = st.session_state.get("selected_book_for_comparison")
    
    if not book_id:
        # Show instructions
        st.info("""
        📋 **How to Compare Summary Versions**
        
        1. Go to **Summaries** page
        2. Find a book with multiple versions (v1, v2, etc.)
        3. Click the **"🔍 Compare"** button
        4. You'll be brought here automatically
        
        **OR select a book manually below:**
        """)
        
        # Let user select a book manually
        db = get_db()
        user_id = st.session_state.user_id
        
        # Get user's books
        try:
            if isinstance(user_id, str):
                user_obj_id = ObjectId(user_id)
            else:
                user_obj_id = user_id
            
            # Get books with summaries
            pipeline = [
                {"$match": {"user_id": user_obj_id}},
                {"$lookup": {
                    "from": "summaries",
                    "localField": "_id",
                    "foreignField": "book_id",
                    "as": "book_summaries"
                }},
                {"$addFields": {
                    "summary_count": {"$size": "$book_summaries"}
                }},
                {"$match": {
                    "summary_count": {"$gt": 1}
                }},
                {"$sort": {"title": 1}}
            ]
            
            books_with_versions = list(db.books.aggregate(pipeline))
            
            if books_with_versions:
                st.subheader("📚 Your Books with Multiple Versions")
                
                for book in books_with_versions:
                    col_b1, col_b2 = st.columns([3, 1])
                    
                    with col_b1:
                        book_title = book.get('title', 'Untitled')
                        book_author = book.get('author', 'Unknown')
                        version_count = book['summary_count']
                        st.write(f"**{book_title}** by {book_author}")
                        st.caption(f"{version_count} versions available")
                    
                    with col_b2:
                        if st.button("Select", key=f"select_{book['_id']}", use_container_width=True):
                            st.session_state.selected_book_for_comparison = str(book["_id"])
                            st.rerun()
            else:
                st.warning("""
                No books with multiple versions found.
                
                **To create multiple versions:**
                1. Upload a book from the **Upload Book** page
                2. Generate a summary from the **Generate Summary** page
                3. Generate another summary for the **same book** with different settings
                4. Come back here to compare
                """)
                
        except Exception as e:
            st.error(f"Error loading books: {str(e)}")
        
        return
    
    # ============================================
    # STEP 2: GET BOOK INFO AND SUMMARIES
    # ============================================
    db = get_db()
    user_id = st.session_state.user_id
    
    # Get book info
    try:
        book = get_book_by_id(book_id)
        if book:
            st.success(f"📖 **Comparing versions of:** {book.get('title', 'Untitled Book')}")
            if book.get('author'):
                st.caption(f"by {book['author']}")
    except Exception as e:
        st.error(f"Error loading book: {str(e)}")
    
    # Get all summaries for this book
    try:
        if isinstance(user_id, str):
            try:
                user_obj_id = ObjectId(user_id)
            except:
                user_obj_id = user_id
        else:
            user_obj_id = user_id
        
        if isinstance(book_id, str):
            book_obj_id = ObjectId(book_id)
        else:
            book_obj_id = book_id
        
        summaries = list(db.summaries.find({
            "book_id": book_obj_id,
            "user_id": user_obj_id
        }).sort("version", 1))
        
        # Convert ObjectId to string
        for summary in summaries:
            summary["_id"] = str(summary["_id"])
            summary["book_id"] = str(summary["book_id"])
        
        # Check if we have enough versions
        if len(summaries) < 2:
            st.warning(f"""
            ⚠️ **Only {len(summaries)} version(s) available!**
            
            You need at least **2 versions** to compare.
            
            **To create another version:**
            1. Go to **Generate Summary** page
            2. Select this book
            3. Choose different settings
            4. Generate new summary
            5. Come back here to compare
            """)
            
            col1, col2 = st.columns(2)
            with col1:
                if st.button("✨ Generate New Version", type="primary", use_container_width=True):
                    st.session_state.current_book = book_id
                    st.session_state.page = "generate_summary"
                    st.rerun()
            
            with col_2:
                if st.button("📝 View All Summaries", type="secondary", use_container_width=True):
                    st.session_state.page = "summaries"
                    st.rerun()
            
            return
        
        # ============================================
        # STEP 3: SELECT VERSIONS TO COMPARE
        # ============================================
        st.subheader("📋 Select Versions to Compare")
        
        # Create options for dropdowns
        version_options = []
        for summary in summaries:
            version_num = summary.get("version", 1)
            
            # Format date
            created_at = summary.get("created_at", "")
            if isinstance(created_at, datetime):
                date_str = created_at.strftime("%Y-%m-%d")
            else:
                try:
                    date_str = str(created_at)[:10]
                except:
                    date_str = "Unknown"
            
            # Create label
            label = f"Version {version_num}"
            if summary.get("is_favorite"):
                label += " ⭐"
            if summary.get("is_default") or summary.get("is_active"):
                label += " ✅"
            
            label += f" ({date_str})"
            
            version_options.append({
                "label": label,
                "value": summary["_id"],
                "version": version_num
            })
        
        # Display version selection dropdowns
        col_sel1, col_sel2 = st.columns(2)
        
        with col_sel1:
            if version_options:
                selected_v1 = st.selectbox(
                    "Select First Version:",
                    options=[opt["value"] for opt in version_options],
                    format_func=lambda x: next((opt["label"] for opt in version_options if opt["value"] == x), "Unknown"),
                    key="v1_select"
                )
            else:
                st.error("No versions available")
                return
        
        with col_sel2:
            # Filter out selected version 1
            other_options = [opt for opt in version_options if opt["value"] != selected_v1]
            
            if other_options:
                selected_v2 = st.selectbox(
                    "Select Second Version:",
                    options=[opt["value"] for opt in other_options],
                    format_func=lambda x: next((opt["label"] for opt in other_options if opt["value"] == x), "Unknown"),
                    key="v2_select"
                )
            else:
                st.error("No other versions available")
                return
        
        # ============================================
        # STEP 4: LOAD AND DISPLAY SELECTED SUMMARIES
        # ============================================
        summary1 = get_summary_by_id(selected_v1)
        summary2 = get_summary_by_id(selected_v2)
        
        if not summary1 or not summary2:
            st.error("Could not load summary data")
            return
        
        st.divider()
        
        # Display version info side by side
        col_info1, col_info2 = st.columns(2)
        
        with col_info1:
            st.subheader(f"📄 Version {summary1.get('version', 1)}")
            
            # Format date
            created1 = summary1.get('created_at', '')
            if isinstance(created1, datetime):
                created_str1 = created1.strftime("%Y-%m-%d %H:%M")
            else:
                created_str1 = str(created1)[:16]
            
            st.caption(f"Created: {created_str1}")
            
            # Word count
            text1 = summary1.get('summary_text', '')
            word_count1 = len(text1.split())
            char_count1 = len(text1)
            st.caption(f"Words: {word_count1} • Characters: {char_count1}")
            
            # Status badges
            badges1 = []
            if summary1.get('is_favorite'):
                badges1.append("⭐ Favorite")
            if summary1.get('is_default') or summary1.get('is_active'):
                badges1.append("✅ Default")
            
            if badges1:
                st.info(" • ".join(badges1))
        
        with col_info2:
            st.subheader(f"📄 Version {summary2.get('version', 2)}")
            
            # Format date
            created2 = summary2.get('created_at', '')
            if isinstance(created2, datetime):
                created_str2 = created2.strftime("%Y-%m-%d %H:%M")
            else:
                created_str2 = str(created2)[:16]
            
            st.caption(f"Created: {created_str2}")
            
            # Word count
            text2 = summary2.get('summary_text', '')
            word_count2 = len(text2.split())
            char_count2 = len(text2)
            st.caption(f"Words: {word_count2} • Characters: {char_count2}")
            
            # Status badges
            badges2 = []
            if summary2.get('is_favorite'):
                badges2.append("⭐ Favorite")
            if summary2.get('is_default') or summary2.get('is_active'):
                badges2.append("✅ Default")
            
            if badges2:
                st.info(" • ".join(badges2))
        
        # ============================================
        # STEP 5: SHOW COMPARISON STATISTICS
        # ============================================
        st.divider()
        st.subheader("📊 Comparison Statistics")
        
        # Calculate similarity
        similarity = difflib.SequenceMatcher(None, text1, text2).ratio() * 100
        
        # Show metrics
        col_stat1, col_stat2, col_stat3, col_stat4 = st.columns(4)
        
        with col_stat1:
            st.metric("Similarity", f"{similarity:.1f}%")
        
        with col_stat2:
            diff_words = abs(word_count1 - word_count2)
            st.metric("Word Difference", diff_words)
        
        with col_stat3:
            # Calculate common words
            words1_set = set(text1.lower().split())
            words2_set = set(text2.lower().split())
            common_words = len(words1_set.intersection(words2_set))
            st.metric("Common Words", common_words)
        
        with col_stat4:
            unique_words = len(words1_set.symmetric_difference(words2_set))
            st.metric("Unique Words", unique_words)
        
        # ============================================
        # STEP 6: SIDE-BY-SIDE COMPARISON WITH HIGHLIGHTS
        # ============================================
        st.divider()
        st.subheader("👀 Side-by-Side Comparison")
        
        # Choose comparison view
        view_option = st.radio(
            "Choose view:",
            ["Word Differences", "Full Text", "Sentences"],
            horizontal=True
        )
        
        if view_option == "Word Differences":
            # Simple word diff highlighting
            words1 = text1.split()
            words2 = text2.split()
            
            diff = difflib.ndiff(words1, words2)
            
            left_html = []
            right_html = []
            
            for token in diff:
                if token.startswith("- "):
                    left_html.append(f'<span style="background:#ffcccc; padding:2px; margin:1px; border-radius:3px;">{token[2:]}</span>')
                    right_html.append("")
                elif token.startswith("+ "):
                    left_html.append("")
                    right_html.append(f'<span style="background:#ccffcc; padding:2px; margin:1px; border-radius:3px;">{token[2:]}</span>')
                elif token.startswith("  "):
                    left_html.append(token[2:])
                    right_html.append(token[2:])
            
            col_comp1, col_comp2 = st.columns(2)
            
            with col_comp1:
                st.markdown("### Version 1")
                st.markdown(
                    f'<div style="padding:15px; background:#f8f9fa; border-radius:8px; line-height:1.8;">{" ".join(left_html)}</div>',
                    unsafe_allow_html=True
                )
            
            with col_comp2:
                st.markdown("### Version 2")
                st.markdown(
                    f'<div style="padding:15px; background:#f8f9fa; border-radius:8px; line-height:1.8;">{" ".join(right_html)}</div>',
                    unsafe_allow_html=True
                )
            
            # Legend
            st.caption("""
            **Legend:** 
            <span style="background:#ffcccc; padding:2px;">Removed in Version 2</span> | 
            <span style="background:#ccffcc; padding:2px;">Added in Version 2</span>
            """)
        
        elif view_option == "Full Text":
            # Show full text side by side
            col_text1, col_text2 = st.columns(2)
            
            with col_text1:
                st.markdown("### Version 1")
                st.text_area("", text1, height=300, disabled=True, key="text1_full")
            
            with col_text2:
                st.markdown("### Version 2")
                st.text_area("", text2, height=300, disabled=True, key="text2_full")
        
        else:  # Sentences view
            # Split into sentences
            import re
            
            sentences1 = re.split(r'(?<=[.!?])\s+', text1)
            sentences2 = re.split(r'(?<=[.!?])\s+', text2)
            
            col_sent1, col_sent2 = st.columns(2)
            
            with col_sent1:
                st.markdown("### Version 1 Sentences")
                for i, sentence in enumerate(sentences1):
                    st.write(f"{i+1}. {sentence}")
            
            with col_sent2:
                st.markdown("### Version 2 Sentences")
                for i, sentence in enumerate(sentences2):
                    st.write(f"{i+1}. {sentence}")
        
        # ============================================
        # STEP 7: ACTION BUTTONS
        # ============================================
        st.divider()
        st.subheader("⚡ Actions")
        
        col_act1, col_act2, col_act3 = st.columns(3)
        
        with col_act1:
            if not summary1.get('is_default') and not summary1.get('is_active'):
                if st.button("📌 Set Version 1 as Default", use_container_width=True):
                    try:
                        if set_active_summary_version(book_id, user_id, summary1.get('version', 1)):
                            st.success("✅ Version 1 set as default!")
                            st.rerun()
                    except Exception as e:
                        st.error(f"Error: {str(e)}")
            else:
                st.button("✅ Already Default", disabled=True, use_container_width=True)
        
        with col_act2:
            if not summary2.get('is_default') and not summary2.get('is_active'):
                if st.button("📌 Set Version 2 as Default", use_container_width=True):
                    try:
                        if set_active_summary_version(book_id, user_id, summary2.get('version', 2)):
                            st.success("✅ Version 2 set as default!")
                            st.rerun()
                    except Exception as e:
                        st.error(f"Error: {str(e)}")
            else:
                st.button("✅ Already Default", disabled=True, use_container_width=True)
        
        with col_act3:
            if st.button("📥 Export Comparison", use_container_width=True):
                # Create simple comparison report
                report = f"""COMPARISON REPORT
========================
Book: {book.get('title', 'Unknown') if book else 'Unknown'}
Compared on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

VERSION 1 (v{summary1.get('version', 1)})
----------------------------------------
Created: {created_str1}
Words: {word_count1}
Characters: {char_count1}
Status: {'Default' if summary1.get('is_default') or summary1.get('is_active') else 'Not Default'}

VERSION 2 (v{summary2.get('version', 2)})
----------------------------------------
Created: {created_str2}
Words: {word_count2}
Characters: {char_count2}
Status: {'Default' if summary2.get('is_default') or summary2.get('is_active') else 'Not Default'}

SIMILARITY: {similarity:.1f}%

VERSION 1 TEXT:
---------------
{text1}

VERSION 2 TEXT:
---------------
{text2}
"""
                
                # Download button
                timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                st.download_button(
                    "📄 Download Report",
                    report,
                    f"comparison_{book_id}_{timestamp}.txt",
                    "text/plain"
                )
        
        # ============================================
        # STEP 8: FAVORITE AND ARCHIVE ACTIONS
        # ============================================
        st.divider()
        
        col_fav1, col_fav2, col_arch1, col_arch2 = st.columns(4)
        
        with col_fav1:
            if not summary1.get('is_favorite'):
                if st.button("⭐ Favorite Version 1", use_container_width=True):
                    if update_summary_metadata(selected_v1, user_id, {"is_favorite": True}):
                        st.success("Version 1 added to favorites!")
                        st.rerun()
            else:
                if st.button("★ Unfavorite Version 1", use_container_width=True):
                    if update_summary_metadata(selected_v1, user_id, {"is_favorite": False}):
                        st.success("Version 1 removed from favorites!")
                        st.rerun()
        
        with col_fav2:
            if not summary2.get('is_favorite'):
                if st.button("⭐ Favorite Version 2", use_container_width=True):
                    if update_summary_metadata(selected_v2, user_id, {"is_favorite": True}):
                        st.success("Version 2 added to favorites!")
                        st.rerun()
            else:
                if st.button("★ Unfavorite Version 2", use_container_width=True):
                    if update_summary_metadata(selected_v2, user_id, {"is_favorite": False}):
                        st.success("Version 2 removed from favorites!")
                        st.rerun()
        
        with col_arch1:
            if st.button("📦 Archive Version 1", use_container_width=True, type="secondary"):
                if st.checkbox("Confirm archive Version 1?", key="archive_v1"):
                    if delete_summary(selected_v1, user_id, permanent=False):
                        st.success("Version 1 archived!")
                        st.rerun()
        
        with col_arch2:
            if st.button("📦 Archive Version 2", use_container_width=True, type="secondary"):
                if st.checkbox("Confirm archive Version 2?", key="archive_v2"):
                    if delete_summary(selected_v2, user_id, permanent=False):
                        st.success("Version 2 archived!")
                        st.rerun()
        
        # ============================================
        # STEP 9: BOTTOM NAVIGATION
        # ============================================
        st.divider()
        
        col_bottom1, col_bottom2, col_bottom3 = st.columns(3)
        
        with col_bottom1:
            if st.button("🔄 Compare Different Versions", use_container_width=True):
                # Reset selections
                if 'v1_select' in st.session_state:
                    del st.session_state.v1_select
                if 'v2_select' in st.session_state:
                    del st.session_state.v2_select
                st.rerun()
        
        with col_bottom2:
            if st.button("📝 View All Summaries", use_container_width=True):
                st.session_state.page = "summaries"
                st.rerun()
        
        with col_bottom3:
            if st.button("🏠 Back to Dashboard", use_container_width=True):
                st.session_state.page = "dashboard"
                st.rerun()
    
    except Exception as e:
        st.error(f"Error: {str(e)}")
        st.code(str(e))  # Show error for debugging

# Alias for app.py
def show_summary_compare():
    show_summary_comparison()