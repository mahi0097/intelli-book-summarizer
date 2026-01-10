# frontend/mybooks.py
import streamlit as st
import sys
import os
from datetime import datetime
from bson import ObjectId

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from frontend.helper import is_logged_in, get_current_user
from utils.database import db, delete_book_and_summary
from backend.summary_orchestrator import generate_summary
import asyncio

def run_async(coro):
    """Helper to run async functions"""
    try:
        loop = asyncio.get_event_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
    return loop.run_until_complete(coro)

def mybooks_page():
    if not is_logged_in():
        st.error("Login required")
        st.session_state.page = "login"
        st.rerun()
        return
    
    user = get_current_user()
    if not user or "user_id" not in user:
        st.error("Invalid user session. Please login again.")
        st.session_state.page = "login"
        st.rerun()
        return
    st.title("📚 My Books")
    
    # DEBUG: Show user info to check format
    st.sidebar.subheader("🔍 Debug Info")
    st.sidebar.write(f"User ID type: {type(user['user_id'])}")
    st.sidebar.write(f"User ID value: {user['user_id']}")
    
    # Try different user_id formats
    try:
        # First try: user_id as ObjectId
        if isinstance(user["user_id"], ObjectId):
            user_id_query = user["user_id"]
        else:
            # Try to convert string to ObjectId
            user_id_query = ObjectId(user["user_id"])
        
        st.sidebar.success("✓ User ID converted to ObjectId")
        
    except Exception as e:
        st.sidebar.error(f"✗ User ID conversion failed: {e}")
        # Fallback: use as string
        user_id_query = user["user_id"]
        st.sidebar.warning("Using user_id as string")
    
    # Add search and filter options
    col1, col2, col3, col4 = st.columns([2, 2, 1, 1])
    
    with col1:
        search_query = st.text_input("🔍 Search by title", placeholder="Enter book title...")
    
    with col2:
        status_filter = st.selectbox(
            "Filter by status",
            ["All", "uploaded", "extracting", "text_extracted", "processing", "completed", "failed"]
        )
    
    with col3:
        # Show/Hide temporary books toggle
        show_temp = st.checkbox("Show Temp", value=False, 
                               help="Show temporary books from pasted text")
    
    with col4:
        st.write("")  # Spacing
        if st.button("🔄 Refresh"):
            st.rerun()
    
    # Build query - FIXED VERSION
    query = {"user_id": user_id_query}
    
    # Exclude temporary books unless checkbox is checked
    if not show_temp:
        query["is_temporary"] = {"$ne": True}
    
    if search_query:
        query["title"] = {"$regex": search_query, "$options": "i"}
    
    if status_filter != "All":
        query["status"] = status_filter
    
    # DEBUG: Show query
    st.sidebar.write("📋 Query:", query)
    
    try:
        # Get books with sorting
        books = list(db.books.find(query).sort("uploaded_at", -1))
        
        # DEBUG: Show count
        st.sidebar.write(f"📊 Found {len(books)} books")
        
        if books:
            # Show first book as sample for debugging
            st.sidebar.write("📖 Sample book:", {
                "title": books[0].get("title"),
                "status": books[0].get("status"),
                "user_id": str(books[0].get("user_id"))[:10] + "...",
                "is_temporary": books[0].get("is_temporary", False)
            })
    except Exception as e:
        st.error(f"Database error: {str(e)}")
        st.sidebar.error(f"Query error: {e}")
        books = []
    
    # Check if we need to regenerate a summary
    if "_regenerate_book" in st.session_state:
        book_id = st.session_state._regenerate_book
        del st.session_state._regenerate_book
        
        st.info(f"🔄 Generating summary for selected book...")
        
        with st.spinner("Generating summary..."):
            try:
                # Default summary options
                summary_options = {
                    "length": "medium",
                    "style": "paragraph",
                    "detail": "concise"
                }
                
                result = run_async(
                    generate_summary(
                        book_id=book_id,
                        user_id=user["user_id"],
                        summary_options=summary_options
                    )
                )
                
                if result and result.get("success"):
                    st.success("✅ Summary regenerated successfully!")
                    st.rerun()
                else:
                    error_msg = result.get("error", "Unknown error") if result else "No response"
                    st.error(f"❌ Failed to regenerate summary: {error_msg}")
                    
            except Exception as e:
                st.error(f"❌ Error: {str(e)}")
    
    if not books:
        st.info("📭 No books found. Upload some books first!")
        st.write("""
        **Possible reasons:**
        1. You haven't uploaded any books yet
        2. Your books are marked as temporary (check 'Show Temp' box)
        3. Database connection issue
        
        **Try:**
        - Go to **Upload Book** page and upload a book
        - Check the 'Show Temp' box above
        - Click Refresh button
        """)
        return
    
    # Show statistics
    total_books = len(books)
    completed_books = len([b for b in books if b.get("status") == "completed"])
    failed_books = len([b for b in books if b.get("status") == "failed"])
    temp_books = len([b for b in books if b.get("is_temporary", False)])
    
    stat_col1, stat_col2, stat_col3, stat_col4 = st.columns(4)
    with stat_col1:
        st.metric("Total Books", total_books)
    with stat_col2:
        st.metric("Completed", completed_books)
    with stat_col3:
        st.metric("Failed", failed_books)
    with stat_col4:
        st.metric("Temporary", temp_books)
    
    st.markdown("---")
    
    # Display each book
    for index, b in enumerate(books):
        b_id = str(b.get("_id"))
        
        # Create expander for each book
        expander_title = f"📘 {b.get('title', 'Untitled')}"
        if b.get("is_temporary", False):
            expander_title += " 🏷️"
        expander_title += f" - {b.get('status', 'unknown').replace('_', ' ').title()}"
        
        with st.expander(expander_title, expanded=False):
            col_info, col_stats = st.columns([2, 1])
            
            with col_info:
                # Book info
                st.write(f"**Author:** {b.get('author', 'Not specified')}")
                st.write(f"**Uploaded:** {b.get('uploaded_at', 'N/A').strftime('%Y-%m-%d %H:%M') if isinstance(b.get('uploaded_at'), datetime) else 'N/A'}")
                st.write(f"**File Type:** {b.get('file_type', 'N/A').upper()}")
                
                if b.get("chapter"):
                    st.write(f"**Chapter:** {b['chapter']}")
                
                # Show if temporary
                if b.get("is_temporary", False):
                    st.info("📝 This is a temporary book from pasted text")
                
                # Show error if failed
                if b.get("status") == "failed" and b.get("error_message"):
                    st.error(f"**Error:** {b['error_message']}")
            
            with col_stats:
                # Book stats
                st.write(f"**Words:** {b.get('word_count', 0):,}")
                st.write(f"**Characters:** {b.get('char_count', 0):,}")
                
                # Progress bar for processing
                if b.get("status") == "processing":
                    progress_data = db.progress.find_one({"book_id": ObjectId(b_id)})
                    if progress_data:
                        progress = progress_data.get("percentage", 0)
                        st.progress(progress / 100)
                        st.caption(f"{progress}% - {progress_data.get('message', '')}")
            
            # Action buttons
            st.markdown("---")
            col_btn1, col_btn2, col_btn3, col_btn4 = st.columns(4)
            
            with col_btn1:
                if st.button("📄 View Text", key=f"text_{b_id}_{index}"):
                    st.session_state[f"show_text_{b_id}"] = True
            
            with col_btn2:
                if st.button("📖 View Summary", key=f"summary_{b_id}_{index}"):
                    st.session_state[f"show_summary_{b_id}"] = True
            
            with col_btn3:
                if b.get("status") == "text_extracted":
                    if st.button("🔁 Regenerate", key=f"regen_{b_id}_{index}"):
                        st.session_state._regenerate_book = b_id
                        st.rerun()
                elif b.get("status") == "failed":
                    if st.button("🔄 Retry", key=f"retry_{b_id}_{index}"):
                        st.session_state._regenerate_book = b_id
                        st.rerun()
                else:
                    st.button("⏳ Processing...", disabled=True, key=f"proc_{b_id}_{index}")
            
            with col_btn4:
                if st.button("🗑️ Delete", key=f"delete_{b_id}_{index}"):
                    st.session_state[f"confirm_delete_{b_id}"] = True
            
            # Show text if requested
            if st.session_state.get(f"show_text_{b_id}", False):
                st.markdown("### 📄 Raw Text")
                raw_text = b.get("raw_text", "")
                if raw_text:
                    st.text_area("Full Text", value=raw_text, height=200, key=f"textarea_{b_id}_{index}")
                    
                    # Show text statistics
                    words = len(raw_text.split())
                    chars = len(raw_text)
                    sentences = raw_text.count('.') + raw_text.count('!') + raw_text.count('?')
                    st.caption(f"📊 Text stats: {words:,} words, {chars:,} characters, ~{sentences} sentences")
                else:
                    st.warning("No text available for this book.")
                
                if st.button("Close Text", key=f"close_text_{b_id}_{index}"):
                    st.session_state[f"show_text_{b_id}"] = False
                    st.rerun()
            
            # Show summary if requested
            if st.session_state.get(f"show_summary_{b_id}", False):
                st.markdown("### 📖 Summary")
                summary = db.summaries.find_one({"book_id": ObjectId(b_id)})
                if summary:
                    summary_text = summary.get("summary_text") or summary.get("summary", "")
                    if summary_text:
                        st.write(summary_text)
                        
                        # Summary metadata
                        meta_col1, meta_col2, meta_col3 = st.columns(3)
                        with meta_col1:
                            st.caption(f"📝 Length: {len(summary_text.split()):,} words")
                        with meta_col2:
                            if "processing_time" in summary:
                                st.caption(f"⏱️ Time: {summary['processing_time']}s")
                        with meta_col3:
                            if "created_at" in summary:
                                st.caption(f"📅 {summary['created_at'].strftime('%Y-%m-%d %H:%M')}")
                        
                        # Download button for summary
                        st.download_button(
                            label="📥 Download Summary",
                            data=summary_text,
                            file_name=f"summary_{b.get('title', 'book').replace(' ', '_')}.txt",
                            mime="text/plain",
                            key=f"dl_summary_{b_id}_{index}"
                        )
                    else:
                        st.warning("Summary exists but text is empty.")
                else:
                    st.info("No summary available yet. Generate one using the 'Regenerate' button.")
                
                if st.button("Close Summary", key=f"close_summary_{b_id}_{index}"):
                    st.session_state[f"show_summary_{b_id}"] = False
                    st.rerun()
            
            # Delete confirmation
            if st.session_state.get(f"confirm_delete_{b_id}", False):
                st.warning(f"⚠️ Are you sure you want to delete '{b.get('title', 'this book')}'?")
                col_yes, col_no = st.columns(2)
                
                with col_yes:
                    if st.button("✅ Yes, Delete", key=f"confirm_yes_{b_id}_{index}"):
                        try:
                            # Use the proper delete function
                            success = delete_book_and_summary(b_id)
                            if success:
                                st.success("✅ Book deleted successfully!")
                                
                                # Clean up session states
                                for key in [f"show_text_{b_id}", f"show_summary_{b_id}", f"confirm_delete_{b_id}"]:
                                    if key in st.session_state:
                                        del st.session_state[key]
                                
                                # Remove file if exists
                                file_path = b.get("file_path")
                                if file_path and os.path.exists(file_path):
                                    try:
                                        os.remove(file_path)
                                    except:
                                        pass
                                
                                st.rerun()
                            else:
                                st.error("❌ Failed to delete book.")
                        except Exception as e:
                            st.error(f"❌ Delete error: {str(e)}")
                
                with col_no:
                    if st.button("❌ Cancel", key=f"confirm_no_{b_id}_{index}"):
                        st.session_state[f"confirm_delete_{b_id}"] = False
                        st.rerun()
    
    # Bulk actions section
    st.markdown("---")
    st.subheader("📦 Bulk Actions")
    
    bulk_col1, bulk_col2, bulk_col3 = st.columns(3)
    
    with bulk_col1:
        if st.button("🗑️ Delete All Failed", type="secondary"):
            failed_books = list(db.books.find({"user_id": user_id_query, "status": "failed"}))
            if failed_books:
                deleted_count = 0
                for fb in failed_books:
                    if delete_book_and_summary(str(fb["_id"])):
                        deleted_count += 1
                st.success(f"✅ Deleted {deleted_count} failed books!")
                st.rerun()
            else:
                st.info("No failed books to delete.")
    
    with bulk_col2:
        if st.button("🗑️ Delete All Temp", type="secondary"):
            temp_books = list(db.books.find({"user_id": user_id_query, "is_temporary": True}))
            if temp_books:
                deleted_count = 0
                for tb in temp_books:
                    if delete_book_and_summary(str(tb["_id"])):
                        deleted_count += 1
                st.success(f"✅ Deleted {deleted_count} temporary books!")
                st.rerun()
            else:
                st.info("No temporary books to delete.")
    
    with bulk_col3:
        if st.button("📊 Export List", type="secondary"):
            # Create a simple CSV of book info
            import csv
            import io
            
            output = io.StringIO()
            writer = csv.writer(output)
            writer.writerow(["Title", "Author", "Status", "Word Count", "Upload Date", "File Type"])
            
            for b in books:
                writer.writerow([
                    b.get("title", ""),
                    b.get("author", ""),
                    b.get("status", ""),
                    b.get("word_count", 0),
                    b.get("uploaded_at", "").strftime("%Y-%m-%d") if isinstance(b.get("uploaded_at"), datetime) else "",
                    b.get("file_type", "")
                ])
            
            st.download_button(
                label="📥 Download CSV",
                data=output.getvalue(),
                file_name="my_books_export.csv",
                mime="text/csv",
                key="bulk_export"
            )
    
    # Diagnostic help section
    with st.expander("🛠️ Troubleshooting Help"):
        st.write("""
        **If books are not showing:**
        
        1. **Check database connection**: Make sure MongoDB is running
        2. **Verify user ID format**: Check if user ID matches database format
        3. **Check book ownership**: Books must have your user_id
        4. **Refresh the page**: Click the refresh button
        
        **Debug steps:**
        - Look at the debug info in the sidebar
        - Check if books exist in the Upload History page
        - Verify the user_id in your session matches database
        """)
        
        # Direct database check
        if st.button("Check All Books in Database", key="debug_check"):
            all_books = list(db.books.find({}))
            st.write(f"Total books in database: {len(all_books)}")
            for book in all_books[:5]:  # Show first 5
                st.write(f"- {book.get('title')} | User: {book.get('user_id')}")