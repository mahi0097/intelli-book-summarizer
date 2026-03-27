import streamlit as st
from backend.summary_orchestrator import generate_summary
from bson import ObjectId
from utils.database import db, create_book
import asyncio
import tempfile
import os
import uuid
from datetime import datetime
import json
import base64

# Import export utilities from backend
from backend.exporters.export_utils import format_txt_export, format_json_export

# ✅ Import sidebar CSS from navbar.py
from frontend.navbar import get_sidebar_css


def load_summary_generation_css():
    # ✅ Inject sidebar CSS from navbar.py
    sidebar_css = get_sidebar_css()
    st.markdown(sidebar_css, unsafe_allow_html=True)

    st.markdown("""
    <style>
    /* ===============================
       GLOBAL THEME
    =============================== */
    :root {
        --primary: #2563eb;
        --primary-dark: #1d4ed8;
        --bg-light: #f8fafc;
        --bg-dark: #0f172a;
        --card-light: #ffffff;
        --card-dark: #1e293b;
        --border-light: #e5e7eb;
        --border-dark: #334155;
        --success: #16a34a;
    }

    /* App background */
    .stApp {
        background: #eef6ff;
    }

    @media (prefers-color-scheme: dark) {
        .stApp {
            background: var(--bg-dark);
            color: #e5e7eb;
        }
    }

    /* Tabs */
    button[data-baseweb="tab"] {
        font-weight: 600;
        border-radius: 10px;
        padding: 8px 14px;
    }

    /* Cards / expanders */
    [data-testid="stExpander"],
    [data-testid="stMetric"],
    .summary-box,
    .stTextArea textarea {
        background: var(--card-light);
        border-radius: 14px;
        border: 1px solid var(--border-light);
        padding: 16px;
        box-shadow: 0 10px 25px rgba(0,0,0,0.06);
        transition: all 0.3s ease;
        animation: fadeUp 0.4s ease;
    }

    @media (prefers-color-scheme: dark) {
        [data-testid="stExpander"],
        [data-testid="stMetric"],
        .summary-box,
        .stTextArea textarea {
            background: var(--card-dark);
            border-color: var(--border-dark);
        }
    }

    /* Hover lift */
    [data-testid="stExpander"]:hover,
    .summary-box:hover {
        transform: translateY(-4px);
        box-shadow: 0 18px 40px rgba(37,99,235,0.25);
    }

    /* Summary content */
    .summary-box {
        line-height: 1.7;
        font-size: 0.96rem;
        white-space: pre-wrap;
    }

    /* Buttons */
    .main .stButton > button {
        background: linear-gradient(135deg, var(--primary), var(--primary-dark));
        color: white;
        border-radius: 12px;
        font-weight: 600;
        border: none;
        transition: all 0.25s ease;
    }

    .main .stButton > button:hover {
        transform: translateY(-3px);
        box-shadow: 0 12px 30px rgba(37,99,235,0.4);
    }

    /* Primary action emphasis */
    button[kind="primary"] {
        background: linear-gradient(135deg, #16a34a, #15803d) !important;
    }

    /* Progress bar */
    .stProgress > div > div {
        background-color: var(--primary);
    }

    /* Divider */
    hr {
        border: none;
        height: 1px;
        background: linear-gradient(to right, transparent, #93c5fd, transparent);
    }

    /* Animation */
    @keyframes fadeUp {
        from {
            opacity: 0;
            transform: translateY(14px);
        }
        to {
            opacity: 1;
            transform: translateY(0);
        }
    }
    </style>
    """, unsafe_allow_html=True)


# Import clipboard utilities
try:
    from frontend.utils.clipboard_utils import (
        create_copy_button_simple,
        create_copy_button_with_icon_simple,
        create_floating_copy_button_simple,
        create_working_copy_button
    )
    CLIPBOARD_UTILS_AVAILABLE = True
except ImportError as e:
    print(f"Warning: Clipboard utilities not available: {e}")
    CLIPBOARD_UTILS_AVAILABLE = False

    # Create fallback functions
    def create_copy_button_simple(text, button_text="📋 Copy Summary", button_id=None):
        return f'<button style="padding: 10px 20px; background: #ccc; color: white; border: none; border-radius: 5px;">{button_text} (Not Available)</button>'

    def create_copy_button_with_icon_simple(text, icon="📋", label="Copy", variant="primary"):
        return create_copy_button_simple(text, f"{icon} {label}")

    def create_floating_copy_button_simple(text, position="bottom-right"):
        return '<div></div>'

    def create_working_copy_button(text, button_label="📋 Copy Summary"):
        return create_copy_button_simple(text, button_label)


# ReportLab for PDF generation
try:
    from reportlab.lib.pagesizes import A4, letter
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, PageBreak
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.enums import TA_JUSTIFY
    from reportlab.lib import colors
    REPORTLAB_AVAILABLE = True
except ImportError:
    REPORTLAB_AVAILABLE = False


def run_async(coro):
    """Helper to run async functions in Streamlit"""
    try:
        loop = asyncio.get_event_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
    return loop.run_until_complete(coro)


def create_temporary_book_from_text(user_id, text, title="Pasted Text"):
    """Create a temporary book from pasted text"""
    try:
        os.makedirs("data/uploads", exist_ok=True)
        temp_filename = f"temp_{uuid.uuid4().hex[:8]}.txt"
        temp_path = os.path.join("data/uploads", temp_filename)

        with open(temp_path, "w", encoding="utf-8") as f:
            f.write(text)

        book_id = create_book(
            user_id=user_id,
            title=title,
            author="User",
            chapter="Direct Input",
            file_path=temp_path,
            raw_text=text
        )

        db.books.update_one(
            {"_id": ObjectId(book_id)},
            {"$set": {
                "word_count": len(text.split()),
                "status": "text_extracted",
                "is_temporary": True,
                "uploaded_at": datetime.now()
            }}
        )
        return str(book_id)
    except Exception as e:
        st.error(f"Error creating temporary book: {str(e)}")
        return None


def export_pdf_enhanced(summary_text, title, author, original_text=None):
    """Enhanced PDF export with professional formatting"""
    if not REPORTLAB_AVAILABLE:
        return export_pdf_basic(summary_text, title, author, original_text)

    try:
        tmp = tempfile.NamedTemporaryFile(delete=False, suffix=".pdf")
        tmp.close()

        doc = SimpleDocTemplate(
            tmp.name,
            pagesize=letter,
            rightMargin=72,
            leftMargin=72,
            topMargin=72,
            bottomMargin=72
        )

        styles = getSampleStyleSheet()

        title_style = ParagraphStyle(
            'CustomTitle',
            parent=styles['Heading1'],
            fontSize=16,
            spaceAfter=30,
            textColor=colors.HexColor('#2E86AB')
        )

        section_style = ParagraphStyle(
            'SectionTitle',
            parent=styles['Heading2'],
            fontSize=14,
            spaceBefore=20,
            spaceAfter=12,
            textColor=colors.HexColor('#A23B72')
        )

        meta_style = ParagraphStyle(
            'MetaInfo',
            parent=styles['Normal'],
            fontSize=11,
            spaceAfter=6
        )

        text_style = ParagraphStyle(
            'BodyText',
            parent=styles['Normal'],
            fontSize=11,
            spaceAfter=12,
            alignment=TA_JUSTIFY,
            leading=14
        )

        story = []

        story.append(Paragraph(f"Book Summary Report", title_style))
        story.append(Spacer(1, 10))

        story.append(Paragraph(f"<b>Book Title:</b> {title}", meta_style))
        story.append(Paragraph(f"<b>Author:</b> {author}", meta_style))
        story.append(Paragraph(f"<b>Generated:</b> {datetime.now().strftime('%d %B %Y %H:%M')}", meta_style))
        story.append(Spacer(1, 20))

        story.append(Paragraph("Summary", section_style))
        story.append(Spacer(1, 10))

        summary_paragraphs = summary_text.split('\n\n')
        for para in summary_paragraphs:
            if para.strip():
                story.append(Paragraph(para.replace('\n', '<br/>'), text_style))
                story.append(Spacer(1, 8))

        if original_text:
            story.append(PageBreak())
            story.append(Paragraph("Original Text Excerpt", section_style))
            story.append(Spacer(1, 10))

            if len(original_text) > 3000:
                original_text = original_text[:3000] + "...\n\n[Text truncated for PDF export]"

            original_paragraphs = original_text.split('\n\n')
            for i, para in enumerate(original_paragraphs[:5]):
                if para.strip():
                    story.append(Paragraph(f"Paragraph {i+1}:", ParagraphStyle(
                        'OriginalLabel',
                        parent=styles['Normal'],
                        fontSize=10,
                        textColor=colors.gray
                    )))
                    story.append(Paragraph(para.replace('\n', '<br/>'), text_style))
                    story.append(Spacer(1, 12))

        story.append(Spacer(1, 30))
        footer_text = f"Generated by Book Summarizer Pro • {datetime.now().strftime('%Y-%m-%d')} • Page <page>"
        story.append(Paragraph(footer_text, ParagraphStyle(
            'Footer',
            parent=styles['Normal'],
            fontSize=9,
            textColor=colors.gray,
            alignment=1
        )))

        doc.build(story)
        return tmp.name

    except Exception as e:
        st.error(f"PDF generation error: {str(e)}")
        return export_pdf_basic(summary_text, title, author, original_text)


def export_pdf_basic(summary_text, title, author, original_text=None):
    """Basic PDF export fallback"""
    if not REPORTLAB_AVAILABLE:
        st.warning("PDF export is unavailable because ReportLab is not installed in this deployment.")
        return None

    try:
        from reportlab.platypus import SimpleDocTemplate, Paragraph
        from reportlab.lib.pagesizes import A4
        from reportlab.lib.styles import getSampleStyleSheet

        tmp = tempfile.NamedTemporaryFile(delete=False, suffix=".pdf")
        styles = getSampleStyleSheet()
        doc = SimpleDocTemplate(tmp.name, pagesize=A4)
        story = []

        story.append(Paragraph(f"<b>Title:</b> {title}", styles["Normal"]))
        story.append(Paragraph(f"<b>Author:</b> {author}", styles["Normal"]))
        story.append(Paragraph(f"<b>Date:</b> {datetime.now().strftime('%d %B %Y %H:%M')}", styles["Normal"]))
        story.append(Paragraph("<br/><b>Summary</b><br/>", styles["Heading2"]))
        story.append(Paragraph(summary_text, styles["Normal"]))

        if original_text:
            story.append(Paragraph("<br/><b>Original Text Excerpt</b><br/>", styles["Heading2"]))
            if len(original_text) > 2000:
                original_text = original_text[:2000] + "... [truncated]"
            story.append(Paragraph(original_text, styles["Normal"]))

        doc.build(story)
        return tmp.name
    except Exception as e:
        st.error(f"Basic PDF export failed: {str(e)}")
        return None


def create_top_right_copy_icon(summary_text):
    """Create a floating copy icon in the top right corner"""
    encoded_text = base64.b64encode(summary_text.encode()).decode()

    html = f'''
    <div id="floating-copy-icon" style="position: fixed; top: 20px; right: 20px; z-index: 9999;">
        <button onclick="copySummary('{encoded_text}', this)"
                style="width: 50px; height: 50px; border-radius: 50%; background: linear-gradient(45deg, #2196F3, #1976D2);
                       color: white; border: none; cursor: pointer; font-size: 24px; display: flex;
                       align-items: center; justify-content: center; box-shadow: 0 4px 12px rgba(0,0,0,0.2);
                       transition: all 0.3s ease;">
            📋
        </button>
        <div id="copy-tooltip" style="position: absolute; top: 60px; right: 0; background: #333; color: white;
              padding: 8px 12px; border-radius: 4px; font-size: 12px; white-space: nowrap; opacity: 0;
              transition: opacity 0.3s; pointer-events: none;">
            Copy Summary
        </div>
    </div>

    <script>
    function copySummary(encodedText, button) {{
        try {{
            const text = atob(encodedText);
            const originalHTML = button.innerHTML;

            if (navigator.clipboard && window.isSecureContext) {{
                navigator.clipboard.writeText(text).then(() => {{
                    showCopySuccess(button, originalHTML);
                }}).catch(err => {{
                    useFallbackCopy(text, button, originalHTML);
                }});
            }} else {{
                useFallbackCopy(text, button, originalHTML);
            }}
        }} catch (error) {{
            showCopyError(button);
        }}
    }}

    function useFallbackCopy(text, button, originalHTML) {{
        const textarea = document.createElement('textarea');
        textarea.value = text;
        textarea.style.position = 'fixed';
        textarea.style.left = '-999999px';
        textarea.style.top = '-999999px';
        document.body.appendChild(textarea);
        textarea.select();

        try {{
            const successful = document.execCommand('copy');
            if (successful) {{
                showCopySuccess(button, originalHTML);
            }} else {{
                showCopyError(button);
            }}
        }} catch (err) {{
            showCopyError(button);
        }} finally {{
            document.body.removeChild(textarea);
        }}
    }}

    function showCopySuccess(button, originalHTML) {{
        button.innerHTML = '✅';
        button.style.background = 'linear-gradient(45deg, #28a745, #218838)';
        showToast('Summary copied to clipboard!', 'success');
        setTimeout(() => {{
            button.innerHTML = originalHTML;
            button.style.background = 'linear-gradient(45deg, #2196F3, #1976D2)';
        }}, 2000);
    }}

    function showCopyError(button) {{
        button.innerHTML = '❌';
        button.style.background = '#dc3545';
        showToast('Failed to copy', 'error');
        setTimeout(() => {{
            button.innerHTML = '📋';
            button.style.background = 'linear-gradient(45deg, #2196F3, #1976D2)';
        }}, 2000);
    }}

    function showToast(message, type = 'success') {{
        const existingToast = document.querySelector('.copy-icon-toast');
        if (existingToast) existingToast.remove();

        const toast = document.createElement('div');
        toast.className = 'copy-icon-toast';
        toast.innerHTML = message;
        toast.style.cssText = `
            position: fixed; top: 80px; right: 20px;
            background: ${{type === 'success' ? '#28a745' : '#dc3545'}};
            color: white; padding: 10px 20px; border-radius: 5px;
            z-index: 10000; animation: fadeInOut 2s forwards;
            box-shadow: 0 4px 12px rgba(0,0,0,0.15); font-size: 14px;
        `;

        if (!document.querySelector('#copy-icon-animation')) {{
            const style = document.createElement('style');
            style.id = 'copy-icon-animation';
            style.textContent = `
                @keyframes fadeInOut {{
                    0% {{ opacity: 0; transform: translateY(-10px); }}
                    10% {{ opacity: 1; transform: translateY(0); }}
                    90% {{ opacity: 1; transform: translateY(0); }}
                    100% {{ opacity: 0; transform: translateY(-10px); }}
                }}
            `;
            document.head.appendChild(style);
        }}

        document.body.appendChild(toast);
        setTimeout(() => {{ if (toast.parentNode) toast.parentNode.removeChild(toast); }}, 2000);
    }}

    document.addEventListener('DOMContentLoaded', function() {{
        const icon = document.getElementById('floating-copy-icon');
        const tooltip = document.getElementById('copy-tooltip');
        if (icon && tooltip) {{
            icon.addEventListener('mouseenter', () => {{ tooltip.style.opacity = '1'; }});
            icon.addEventListener('mouseleave', () => {{ tooltip.style.opacity = '0'; }});
        }}
    }});
    </script>
    '''
    return html


def summary_generation_page():
    load_summary_generation_css()

    """Main summary generation interface"""
    st.title("📝 AI Summary Generation")

    # Check login
    if "user_id" not in st.session_state or not st.session_state.logged_in:
        st.error("Please login to generate summaries")
        st.session_state.page = "login"
        st.rerun()
        return

    user_id = st.session_state["user_id"]

    # Create tabs for input methods
    tab1, tab2 = st.tabs(["📚 Select from My Books", "📝 Paste Text Directly"])

    selected_book = None
    pasted_text = ""
    raw_text = ""
    title = ""
    author = ""

    with tab1:
        try:
            books = list(db.books.find({
                "user_id": ObjectId(user_id),
                "is_temporary": {"$ne": True}
            }).sort("uploaded_at", -1))

            if books:
                selected_book = st.selectbox(
                    "Choose a book to summarize",
                    books,
                    format_func=lambda b: f"{b.get('title', 'Unknown')} - {b.get('author', 'Unknown')} ({b.get('word_count', 0):,} words)"
                )

                if selected_book:
                    raw_text = selected_book.get("raw_text", "")
                    title = selected_book.get("title", "Unknown")
                    author = selected_book.get("author", "Unknown")

                    with st.expander("📖 Preview Book Text", expanded=False):
                        if raw_text:
                            preview = raw_text[:500] + ("..." if len(raw_text) > 500 else "")
                            st.text_area("Text Preview", preview, height=150, disabled=True)
                            st.caption(f"Total: {len(raw_text.split()):,} words, {len(raw_text):,} characters")
                        else:
                            st.info("No text available for preview")
            else:
                st.info("No books found. Upload books first or use the paste text option.")

        except Exception as e:
            st.error(f"Error loading books: {str(e)}")

    with tab2:
        st.markdown("**Paste text directly for summarization:**")
        pasted_text = st.text_area(
            "Enter your text here",
            height=250,
            placeholder="Paste or type the text you want to summarize here..."
        )

        if pasted_text:
            raw_text = pasted_text
            title = st.text_input("Title for this text", value="Pasted Text")
            author = st.text_input("Author", value="User")

            words = len(pasted_text.split())
            chars = len(pasted_text)
            st.caption(f"📊 Text stats: {words:,} words, {chars:,} characters")

    st.markdown("---")

    # Summary options
    st.subheader("⚙️ Summary Options")

    col1, col2, col3 = st.columns(3)

    with col1:
        summary_length = st.select_slider(
            "Summary Length",
            options=["very short", "short", "medium", "long", "detailed"],
            value="medium"
        )

    with col2:
        summary_style = st.radio(
            "Format Style",
            ["Paragraph", "Bullet Points", "Executive Summary"],
            horizontal=True
        )

    with col3:
        summary_tone = st.selectbox(
            "Tone",
            ["Neutral", "Academic", "Casual", "Technical"]
        )

    # Advanced options
    with st.expander("🔧 Advanced Options"):
        col_a, col_b = st.columns(2)
        with col_a:
            focus_keywords = st.text_input(
                "Focus Keywords (optional)",
                placeholder="comma-separated keywords"
            )
        with col_b:
            include_key_points = st.checkbox("Include key points", value=True)
            include_quotes = st.checkbox("Include important quotes", value=False)

    # Generate button
    generate_col1, generate_col2, generate_col3 = st.columns([2, 1, 1])

    with generate_col2:
        generate_clicked = st.button(
            "🚀 Generate Summary",
            use_container_width=True,
            type="primary"
        )

    with generate_col3:
        if st.button("🔄 Reset", use_container_width=True):
            for key in ["generated_summary", "generated_book_id", "generated_title",
                        "generated_author", "generated_raw_text"]:
                if key in st.session_state:
                    del st.session_state[key]
            st.rerun()

    # Store generated summary in session state
    if "generated_summary" not in st.session_state:
        st.session_state.generated_summary = None
    if "generated_book_id" not in st.session_state:
        st.session_state.generated_book_id = None

    # Generate summary when button is clicked
    if generate_clicked:
        if not raw_text.strip():
            st.error("Please select a book or paste text to summarize")
            return

        if len(raw_text.split()) < 50:
            st.warning("Text is very short. For best results, use text with at least 100 words.")

        book_id = None
        if pasted_text.strip():
            with st.spinner("Creating temporary book..."):
                book_id = create_temporary_book_from_text(user_id, pasted_text, title)
                if not book_id:
                    st.error("Failed to create temporary book")
                    return
        elif selected_book:
            book_id = str(selected_book["_id"])

        if not book_id:
            st.error("Could not identify book")
            return

        summary_options = {
            "length": summary_length,
            "style": summary_style.lower().replace(" ", "_"),
            "tone": summary_tone.lower(),
            "source": "pasted_text" if pasted_text.strip() else "book",
            "include_key_points": include_key_points,
            "include_quotes": include_quotes
        }

        if focus_keywords:
            summary_options["focus_keywords"] = [k.strip() for k in focus_keywords.split(",")]

        with st.spinner(f"Generating {summary_length} summary..."):
            try:
                result = run_async(
                    generate_summary(
                        book_id=book_id,
                        user_id=user_id,
                        summary_options=summary_options
                    )
                )

                if result and result.get("success"):
                    summary_text = result["summary"]
                    st.session_state.generated_summary = summary_text
                    st.session_state.generated_book_id = book_id
                    st.session_state.generated_title = title
                    st.session_state.generated_author = author
                    st.session_state.generated_raw_text = raw_text
                    st.rerun()
                else:
                    error_msg = result.get("error", "Unknown error") if result else "Summary generation failed"
                    st.error(f"❌ {error_msg}")

            except Exception as e:
                st.error(f"Error generating summary: {str(e)}")

    # Display generated summary if available
    if st.session_state.generated_summary:
        copy_icon_html = create_top_right_copy_icon(st.session_state.generated_summary)
        st.components.v1.html(copy_icon_html, height=0)

        st.markdown("---")
        st.subheader("✅ Summary Generated Successfully!")

        st.markdown("### 📄 Generated Summary")
        st.markdown(f'<div class="summary-box">{st.session_state.generated_summary}</div>', unsafe_allow_html=True)

        col_stat1, col_stat2, col_stat3 = st.columns(3)
        with col_stat1:
            summary_words = len(st.session_state.generated_summary.split())
            st.metric("Summary Length", f"{summary_words:,} words")
        with col_stat2:
            original_words = len(st.session_state.generated_raw_text.split())
            compression = ((original_words - summary_words) / original_words * 100) if original_words > 0 else 0
            st.metric("Compression", f"{compression:.1f}%")
        with col_stat3:
            st.metric("Original Text", f"{original_words:,} words")

        st.markdown("---")

        # Export Section
        st.subheader("📤 Export Options")

        col_format, col_options = st.columns([2, 3])

        with col_format:
            export_format = st.radio(
                "Export Format",
                ["TXT", "PDF", "JSON", "Clipboard"],
                horizontal=True,
                key="export_format"
            )

        with col_options:
            include_original = st.checkbox(
                "Include original text excerpt",
                value=st.session_state.get("include_original", False),
                key="include_original_check"
            )

            if export_format == "TXT":
                include_metadata = st.checkbox("Include metadata header", value=True)
            elif export_format == "PDF":
                high_quality = st.checkbox("High quality formatting", value=REPORTLAB_AVAILABLE)

        st.markdown("---")

        st.markdown("### 📥 Download & Share")

        if export_format == "Clipboard":
            st.markdown("### 📋 Copy to Clipboard")

            col1, col2, col3 = st.columns(3)

            with col1:
                clipboard_summary = st.session_state.generated_summary.replace("`", "\\`")
                html_code = f'''
                <button onclick="navigator.clipboard.writeText(`{clipboard_summary}`).then(() => {{
                    const btn = event.target;
                    const originalText = btn.innerHTML;
                    btn.innerHTML = '✅ Copied!';
                    btn.style.background = '#28a745';
                    setTimeout(() => {{
                        btn.innerHTML = originalText;
                        btn.style.background = '#2196F3';
                    }}, 2000);
                }})"
                style="padding: 12px 24px; background: #2196F3; color: white; border: none; border-radius: 6px; cursor: pointer; font-size: 14px; font-weight: 600; margin: 10px 0; width: 100%;">
                    📋 Copy Summary
                </button>
                '''
                st.components.v1.html(html_code, height=50)

            with col2:
                if include_original:
                    full_text = f"Summary:\n{st.session_state.generated_summary}\n\n---\n\nOriginal Text Excerpt:\n{st.session_state.generated_raw_text[:1000]}..."
                    clipboard_full_text = full_text.replace("`", "\\`")
                    html_code = f'''
                    <button onclick="navigator.clipboard.writeText(`{clipboard_full_text}`).then(() => {{
                        const btn = event.target;
                        const originalText = btn.innerHTML;
                        btn.innerHTML = '✅ Copied!';
                        btn.style.background = '#28a745';
                        setTimeout(() => {{
                            btn.innerHTML = originalText;
                            btn.style.background = '#6c757d';
                        }}, 2000);
                    }})"
                    style="padding: 12px 24px; background: #6c757d; color: white; border: none; border-radius: 6px; cursor: pointer; font-size: 14px; font-weight: 600; margin: 10px 0; width: 100%;">
                        📄 Copy with Original
                    </button>
                    '''
                    st.components.v1.html(html_code, height=50)
                else:
                    st.info("Check 'Include original text' to copy with original")

            with col3:
                formatted_text = f"""SUMMARY: {st.session_state.generated_title}
By: {st.session_state.generated_author}
Date: {datetime.now().strftime('%Y-%m-%d')}

{st.session_state.generated_summary}"""
                clipboard_formatted_text = formatted_text.replace("`", "\\`")

                html_code = f'''
                <button onclick="navigator.clipboard.writeText(`{clipboard_formatted_text}`).then(() => {{
                    const btn = event.target;
                    const originalText = btn.innerHTML;
                    btn.innerHTML = '✅ Copied!';
                    btn.style.background = '#28a745';
                    setTimeout(() => {{
                        btn.innerHTML = originalText;
                        btn.style.background = '#17a2b8';
                    }}, 2000);
                }})"
                style="padding: 12px 24px; background: #17a2b8; color: white; border: none; border-radius: 6px; cursor: pointer; font-size: 14px; font-weight: 600; margin: 10px 0; width: 100%;">
                    📝 Copy Formatted
                </button>
                '''
                st.components.v1.html(html_code, height=50)

        elif export_format == "TXT":
            txt_content = format_txt_export(
                st.session_state.generated_summary,
                st.session_state.generated_title,
                st.session_state.generated_author,
                st.session_state.generated_raw_text if include_original else None,
                include_metadata=True
            )

            col_txt1, col_txt2 = st.columns([1, 3])
            with col_txt1:
                st.download_button(
                    "📥 Download TXT",
                    txt_content,
                    file_name=f"{st.session_state.generated_title.replace(' ', '_')}_summary.txt",
                    mime="text/plain",
                    use_container_width=True
                )
            with col_txt2:
                with st.expander("Preview TXT"):
                    st.text(txt_content[:500] + ("..." if len(txt_content) > 500 else ""))

        elif export_format == "PDF":
            col_pdf1, col_pdf2 = st.columns([1, 3])
            with col_pdf1:
                if st.button("🔄 Generate PDF", use_container_width=True, key="generate_pdf_btn"):
                    with st.spinner("Generating PDF..."):
                        if high_quality and REPORTLAB_AVAILABLE:
                            pdf_path = export_pdf_enhanced(
                                st.session_state.generated_summary,
                                st.session_state.generated_title,
                                st.session_state.generated_author,
                                st.session_state.generated_raw_text if include_original else None
                            )
                        else:
                            pdf_path = export_pdf_basic(
                                st.session_state.generated_summary,
                                st.session_state.generated_title,
                                st.session_state.generated_author,
                                st.session_state.generated_raw_text if include_original else None
                            )

                        if pdf_path and os.path.exists(pdf_path):
                            with open(pdf_path, "rb") as f:
                                st.download_button(
                                    "📥 Download PDF",
                                    f,
                                    file_name=f"{st.session_state.generated_title.replace(' ', '_')}_summary.pdf",
                                    mime="application/pdf",
                                    use_container_width=True,
                                    key="download_pdf_btn"
                                )
                            try:
                                os.unlink(pdf_path)
                            except:
                                pass
                        else:
                            st.error("Failed to generate PDF")
            with col_pdf2:
                if REPORTLAB_AVAILABLE:
                    st.info("Click 'Generate PDF' to create and download the PDF file")
                else:
                    st.warning("ReportLab is missing in this deployment, so PDF export is currently unavailable.")

        elif export_format == "JSON":
            json_content = format_json_export(
                st.session_state.generated_summary,
                st.session_state.generated_title,
                st.session_state.generated_author,
                st.session_state.generated_raw_text if include_original else None
            )

            col_json1, col_json2 = st.columns([1, 3])
            with col_json1:
                st.download_button(
                    "📥 Download JSON",
                    json_content,
                    file_name=f"{st.session_state.generated_title.replace(' ', '_')}_summary.json",
                    mime="application/json",
                    use_container_width=True,
                    key="download_json_btn"
                )
            with col_json2:
                with st.expander("Preview JSON"):
                    try:
                        st.json(json.loads(json_content))
                    except:
                        st.text(json_content[:500] + ("..." if len(json_content) > 500 else ""))

        # API Access section
        with st.expander("🔧 API Access", expanded=False):
            st.code(f"""
            # Get summary via API
            GET /api/export/summary/{st.session_state.generated_book_id}

            # With parameters:
            GET /api/export/summary/{st.session_state.generated_book_id}?format=json&include_original=true

            # Available formats: txt, pdf, json
            """)

            if st.button("📋 Copy API Endpoint", key="copy_api_btn"):
                api_endpoint = f"/api/export/summary/{st.session_state.generated_book_id}"
                st.success(f"API endpoint copied: {api_endpoint}")

        # Quick actions row
        st.markdown("---")
        st.markdown("### ⚡ Quick Actions")

        col_q1, col_q2, col_q3, col_q4 = st.columns(4)

        with col_q1:
            if st.button("📧 Email Summary", use_container_width=True, key="email_btn"):
                st.info("Email functionality would be implemented here")

        with col_q2:
            if st.button("💾 Save to My Books", use_container_width=True, key="save_btn"):
                try:
                    from utils.database import save_summary
                    summary_id = save_summary(
                        st.session_state.generated_book_id,
                        st.session_state.user_id,
                        st.session_state.generated_summary,
                        {"format": export_format}
                    )
                    if summary_id:
                        st.success("✅ Summary saved to My Books!")
                    else:
                        st.error("Failed to save summary")
                except Exception as e:
                    st.error(f"Error saving summary: {str(e)}")

        with col_q3:
            if st.button("🔄 Generate Another", use_container_width=True, key="another_btn"):
                for key in ["generated_summary", "generated_book_id", "generated_title",
                            "generated_author", "generated_raw_text"]:
                    if key in st.session_state:
                        del st.session_state[key]
                st.rerun()

        with col_q4:
            if st.button("📊 View Analytics", use_container_width=True, key="analytics_btn"):
                st.info("Analytics view would be implemented here")

    # Show instruction if no summary generated yet
    else:
        st.info("👆 Configure your summary options above and click 'Generate Summary' to create a summary.")

        with st.expander("💡 Tips for better summaries"):
            st.markdown("""
            1. **For longer texts**: Choose "detailed" or "long" summary length
            2. **For quick overview**: Choose "very short" or "short" length
            3. **For reports**: Use "Executive Summary" style
            4. **For study notes**: Use "Bullet Points" style
            5. **For academic papers**: Use "Academic" tone
            6. **Minimum text**: At least 100 words for best results
            """)
