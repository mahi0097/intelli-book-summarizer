import streamlit as st 
from backend.summary_orchestrator import generate_summary
from bson import ObjectId
from utils.database import db, create_book, update_book_status
import asyncio
import tempfile
import os
import uuid
from datetime import datetime

def run_async(coro):
    try:
        loop = asyncio.get_event_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

    if loop.is_running():
        return loop.run_until_complete(coro)
    else:
        return loop.run_until_complete(coro)


def create_temporary_book_from_text(user_id, text, title="Pasted Text"):
    """Create a temporary book entry from pasted text"""
    try:
        # Generate a unique filename
        temp_filename = f"temp_{uuid.uuid4().hex[:8]}.txt"
        temp_filepath = os.path.join("data/uploads", temp_filename)
        
        # Ensure directory exists
        os.makedirs("data/uploads", exist_ok=True)
        
        # Save text to temporary file
        with open(temp_filepath, "w", encoding="utf-8") as f:
            f.write(text)
        
        # Create book entry in database - with only the parameters create_book accepts
        book_id = create_book(
            user_id=user_id,
            title=title,
            author="User",
            chapter="Direct Input",
            file_path=temp_filepath,
            raw_text=text
        )
        
        # Update the book with additional fields
        db.books.update_one(
            {"_id": ObjectId(book_id) if isinstance(book_id, str) else book_id},
            {"$set": {
                "word_count": len(text.split()),
                "file_type": "txt",
                "status": "text_extracted",
                "uploaded_at": datetime.now(),
                "is_temporary": True
            }}
        )
        
        return str(book_id)
    except Exception as e:
        st.error(f"Failed to create temporary book: {str(e)}")
        return None


def summary_generation_page():
    st.title("📝 Summary Generation Interface")
    st.write("Select a previously uploaded book OR paste text directly to generate a summary")

    # User check session
    if "user_id" not in st.session_state:
        st.error("You must be logged in to generate a summary")
        return
    
    user_id = st.session_state["user_id"]
    
    # DEBUG: Show user_id type and value
    st.sidebar.subheader("🔍 Debug Info")
    st.sidebar.write(f"User ID: {user_id}")
    st.sidebar.write(f"User ID type: {type(user_id)}")

    # Try different user_id formats in query
    books = []
    try:
        # Try as ObjectId first
        try:
            user_id_obj = ObjectId(user_id)
            st.sidebar.success("✓ Converted to ObjectId")
        except:
            st.sidebar.warning("✗ Cannot convert to ObjectId, using as string")
            user_id_obj = user_id
        
        # Try multiple query formats
        query_formats = [
            {"user_id": user_id_obj, "status": "text_extracted", "is_temporary": {"$ne": True}},
            {"user_id": user_id_obj, "status": "completed", "is_temporary": {"$ne": True}},
            {"user_id": user_id_obj, "status": {"$in": ["text_extracted", "completed"]}},
            {"user_id": user_id_obj}  # Try without status filter
        ]
        
        for i, query in enumerate(query_formats):
            try:
                found_books = list(db.books.find(query).sort("uploaded_at", -1).limit(10))
                st.sidebar.write(f"Query {i+1}: Found {len(found_books)} books")
                if found_books:
                    books = found_books
                    st.sidebar.success(f"✓ Using query {i+1}")
                    # Show sample book info
                    sample = books[0]
                    st.sidebar.write(f"Sample: {sample.get('title')} - Status: {sample.get('status')}")
                    break
            except Exception as e:
                st.sidebar.error(f"Query {i+1} error: {str(e)[:50]}")
        
        # If still no books, check all books in database for debugging
        if not books:
            all_books = list(db.books.find({}).limit(5))
            st.sidebar.write(f"All books in DB: {len(all_books)}")
            for b in all_books:
                st.sidebar.write(f"- {b.get('title')}: user_id={b.get('user_id')}, type={type(b.get('user_id'))}")
                
    except Exception as e:
        st.error(f"Database error: {str(e)}")
        st.sidebar.error(f"Error: {str(e)}")
    
    # Create tabs for different input methods
    tab1, tab2 = st.tabs(["📚 Select Book", "📝 Paste Text"])
    
    selected_book = None
    pasted_text = ""
    
    with tab1:
        st.subheader("Select Previously Uploaded Book")
        if books:
            selected_book = st.selectbox(
                "Choose a book:",
                options=books,
                format_func=lambda b: f"{b.get('title', 'Untitled')} - {b.get('status', 'unknown')} ({b.get('word_count', 0)} words)",
                key="book_select"
            )
            st.info(f"Found {len(books)} books. Status: {selected_book.get('status') if selected_book else 'N/A'}")
        else:
            st.info("No books found. Upload books first or use the 'Paste Text' tab.")
            # Show help text
            st.markdown("""
            **To upload books:**
            1. Go to **Upload Book** page from the sidebar
            2. Upload a .txt, .pdf, or .docx file
            3. Wait for text extraction to complete
            4. Return to this page to select the book
            """)
    
    # ... rest of the code remains the same ...
    with tab2:
        st.subheader("Paste Text Directly")
        pasted_text = st.text_area(
            "Paste your text here:",
            height=300,
            placeholder="Paste any text you want to summarize...",
            key="pasted_text"
        )
        
        if pasted_text:
            word_count = len(pasted_text.split())
            st.info(f"📝 Text length: {word_count} words, {len(pasted_text)} characters")
            
            if word_count < 50:
                st.warning("⚠️ Text is very short. For better results, provide at least 100-200 words.")
            elif word_count > 10000:
                st.warning("⚠️ Text is very long. Processing may take some time.")

    st.markdown("---")
    st.subheader("⚙️ Summary Settings")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        summary_length = st.radio(
            "Summary Length:",
            ["short", "medium", "long"],
            index=1,
            help="Short: ~50 words, Medium: ~150 words, Long: ~300 words"
        )
    
    with col2:
        summary_style = st.radio(
            "Summary Style:",
            ["paragraph", "bullets"],
            index=0,
            help="Paragraph: Continuous text, Bullets: Point-form summary"
        )
    
    with col3:
        detail_level = st.radio(
            "Detail Level:",
            ["concise", "detailed"],
            index=0,
            help="Concise: Key points only, Detailed: More comprehensive"
        )
    
    summary_options = {
        "length": summary_length,
        "style": summary_style,
        "detail": detail_level
    }
    
    st.markdown("---")
    
    # Generate summary button
    if st.button("🚀 Generate Summary", type="primary", use_container_width=True):
        book_id = None
        raw_text = ""
        
        # Check which input method was used
        if pasted_text.strip():
            # Use pasted text
            if len(pasted_text.strip()) < 20:
                st.error("Please provide more text (at least 20 characters).")
                return
                
            with st.spinner("📥 Creating temporary book from pasted text..."):
                book_id = create_temporary_book_from_text(
                    user_id=user_id,
                    text=pasted_text.strip(),
                    title=f"Pasted Text - {datetime.now().strftime('%Y-%m-%d %H:%M')}"
                )
                
            if not book_id:
                st.error("Failed to process pasted text. Please try again.")
                return
                
            raw_text = pasted_text.strip()
            
        elif selected_book:
            # Use selected book
            book_id = str(selected_book["_id"])
            raw_text = selected_book.get("raw_text", "")
            
            if not raw_text or len(raw_text.strip()) < 20:
                st.error("Selected book has no readable text content.")
                return
        else:
            st.error("Please either select a book OR paste some text.")
            return
        
        # Generate summary
        if book_id:
            with st.spinner(f"🧠 Generating {summary_length} {summary_style} summary..."):
                try:
                    # Show progress
                    progress_bar = st.progress(0)
                    status_text = st.empty()
                    
                    status_text.info("Initializing summarization...")
                    progress_bar.progress(10)
                    
                    # Run summarization
                    result = run_async(
                        generate_summary(
                            book_id=book_id,
                            user_id=user_id,
                            summary_options=summary_options
                        )
                    )
                    
                    progress_bar.progress(100)
                    status_text.empty()
                    
                    # Display results
                    st.markdown("---")
                    st.subheader("📄 Generated Summary")
                    
                    if result and result.get("success"):
                        summary_text = result.get("summary", "")
                        
                        if summary_style == "paragraph":
                            st.markdown(summary_text)
                        else:
                            # For bullet style, format properly
                            st.markdown(summary_text)
                        
                        # Show statistics
                        col_stats1, col_stats2, col_stats3 = st.columns(3)
                        with col_stats1:
                            st.metric("Original Words", result.get("stats", {}).get("original_length", len(raw_text.split())))
                        with col_stats2:
                            st.metric("Summary Words", result.get("stats", {}).get("summary_length", len(summary_text.split())))
                        with col_stats3:
                            comp_ratio = result.get("stats", {}).get("compression_ratio", "N/A")
                            if isinstance(comp_ratio, (int, float)):
                                st.metric("Compression", f"{comp_ratio:.1f}%")
                            else:
                                st.metric("Compression", comp_ratio)
                        
                        # Add download button
                        col_dl1, col_dl2 = st.columns(2)
                        with col_dl1:
                            st.download_button(
                                label="📥 Download Summary",
                                data=summary_text,
                                file_name=f"summary_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt",
                                mime="text/plain"
                            )
                        with col_dl2:
                            if st.button("🗑️ Clear & Start New", type="secondary"):
                                # Clean up temporary book if created
                                if pasted_text.strip():
                                    try:
                                        db.books.delete_one({"_id": ObjectId(book_id)})
                                    except:
                                        pass
                                st.rerun()
                        
                        st.markdown("---")
                        st.caption(f"⏱️ Processing time: {result.get('processing_time_sec', 'N/A')} seconds")
                        
                    else:
                        error_msg = result.get("error", "Unknown error") if result else "No response from summarizer"
                        st.error(f"❌ Summary generation failed: {error_msg}")
                        
                        # Clean up temporary book if created
                        if pasted_text.strip():
                            try:
                                db.books.delete_one({"_id": ObjectId(book_id)})
                            except:
                                pass
                        
                        # Show troubleshooting tips
                        with st.expander("🛠️ Troubleshooting Tips"):
                            st.write("""
                            1. Make sure your text is in English
                            2. Try with shorter text (under 2000 words)
                            3. Check if the text contains special characters
                            4. Try changing the summary length/style
                            """)
                            
                except Exception as e:
                    st.error(f"❌ Error during summarization: {str(e)}")
                    
                    # Clean up temporary book if it was created from pasted text
                    if pasted_text.strip():
                        try:
                            db.books.delete_one({"_id": ObjectId(book_id)})
                        except:
                            pass
        else:
            st.error("Failed to identify book for summarization.")

    # Display recent summaries
    st.markdown("---")
    st.subheader("📚 Recent Summaries")
    
    recent_summaries = list(db.summaries.find(
        {"user_id": ObjectId(user_id)}
    ).sort("created_at", -1).limit(5))
    
    if recent_summaries:
        for summary in recent_summaries:
            book = db.books.find_one({"_id": summary["book_id"]})
            book_title = book.get("title", "Unknown Book") if book else "Unknown Book"
            
            with st.expander(f"📖 {book_title}"):
                summary_text = summary.get("summary_text") or summary.get("summary", "")
                if summary_text:
                    # Display first 200 chars
                    preview = summary_text[:200] + "..." if len(summary_text) > 200 else summary_text
                    st.write(preview)
                    
                    col_view, col_delete = st.columns([3, 1])
                    with col_view:
                        if st.button("View Full", key=f"view_{summary['_id']}"):
                            st.session_state[f"show_full_{summary['_id']}"] = True
                    
                    # Show full summary if requested
                    if st.session_state.get(f"show_full_{summary['_id']}", False):
                        st.markdown("### Full Summary")
                        st.write(summary_text)
                        if st.button("Close", key=f"close_{summary['_id']}"):
                            st.session_state[f"show_full_{summary['_id']}"] = False
                            st.rerun()
    else:
        st.info("No summaries generated yet. Generate your first summary above!")