import streamlit as st
import json
from datetime import datetime
import base64

def create_copy_to_clipboard_js(summary_text):
    """Generate JavaScript for copying to clipboard"""
    # Escape the text for JavaScript
    escaped_text = summary_text.replace('`', '\\`').replace('$', '\\$')
    
    js_code = f"""
    <script>
    function copyToClipboard() {{
        const text = `{escaped_text}`;
        navigator.clipboard.writeText(text).then(() => {{
            // Show success message
            const btn = document.getElementById('copy-btn');
            const originalText = btn.innerHTML;
            btn.innerHTML = '✅ Copied!';
            btn.style.backgroundColor = '#28a745';
            
            setTimeout(() => {{
                btn.innerHTML = originalText;
                btn.style.backgroundColor = '';
            }}, 2000);
        }}).catch(err => {{
            console.error('Copy failed:', err);
            alert('Copy failed: ' + err);
        }});
    }}
    
    // Create button if it doesn't exist
    if (!document.getElementById('copy-btn')) {{
        const btn = document.createElement('button');
        btn.id = 'copy-btn';
        btn.innerHTML = '📋 Copy Summary';
        btn.style.cssText = `
            padding: 8px 16px;
            background: #6c757d;
            color: white;
            border: none;
            border-radius: 4px;
            cursor: pointer;
            font-size: 14px;
            margin: 10px 0;
        `;
        btn.onclick = copyToClipboard;
        document.body.appendChild(btn);
    }}
    </script>
    """
    return js_code

def create_download_button(data, filename, mime_type, button_text="Download"):
    """Create a download button with base64 encoded data"""
    b64 = base64.b64encode(data.encode()).decode()
    href = f'data:{mime_type};base64,{b64}'
    
    html = f"""
    <a href="{href}" download="{filename}" style="text-decoration: none;">
        <button style="
            padding: 8px 16px;
            background: #007bff;
            color: white;
            border: none;
            border-radius: 4px;
            cursor: pointer;
            font-size: 14px;
            margin: 5px;
        ">
            {button_text}
        </button>
    </a>
    """
    return html

def create_export_panel(summary_text, book_info, include_original_callback=None):
    """Create a comprehensive export panel"""
    
    st.subheader("📤 Export Options")
    
    col1, col2, col3 = st.columns([1, 1, 2])
    
    with col1:
        export_format = st.selectbox(
            "Format",
            ["TXT", "PDF", "JSON"],
            key="export_format"
        )
    
    with col2:
        include_original = st.checkbox(
            "Include original text",
            value=False,
            key="include_original"
        )
    
    # Create export data based on format
    if export_format == "TXT":
        content = format_as_txt(summary_text, book_info, include_original)
        file_ext = ".txt"
        mime_type = "text/plain"
    
    elif export_format == "PDF":
        # Note: PDF generation should be done via API
        content = summary_text  # Will be handled differently
        file_ext = ".pdf"
        mime_type = "application/pdf"
    
    else:  # JSON
        content = json.dumps({
            "summary": summary_text,
            "book_info": book_info,
            "exported_at": datetime.now().isoformat(),
            "include_original": include_original
        }, indent=2)
        file_ext = ".json"
        mime_type = "application/json"
    
    # Generate filename
    safe_title = book_info.get("title", "summary").replace(" ", "_")
    filename = f"{safe_title}_summary{file_ext}"
    
    # Export buttons
    st.markdown("---")
    export_col1, export_col2, export_col3 = st.columns(3)
    
    with export_col1:
        # Copy to clipboard button
        st.components.v1.html(
            create_copy_to_clipboard_js(summary_text),
            height=0
        )
    
    with export_col2:
        if export_format == "PDF":
            # For PDF, we'll trigger API call
            if st.button("⬇️ Download PDF", use_container_width=True):
                st.session_state["generate_pdf"] = True
        else:
            # For text formats, use direct download
            st.markdown(
                create_download_button(content, filename, mime_type, "⬇️ Download"),
                unsafe_allow_html=True
            )
    
    with export_col3:
        if st.button("📧 Share via Email", use_container_width=True):
            # This would trigger email sharing functionality
            st.info("Email sharing feature would be implemented here")
    
    # Show preview for text formats
    if export_format != "PDF":
        with st.expander("Preview Export"):
            st.text_area("Preview", content, height=200)
    
    return content

def format_as_txt(summary_text, book_info, include_original=False):
    """Format as text document"""
    content = f"""BOOK SUMMARY
{'=' * 50}

Title: {book_info.get('title', 'Unknown')}
Author: {book_info.get('author', 'Unknown')}
Generated: {datetime.now().strftime('%d %B %Y %H:%M')}

{'=' * 50}
SUMMARY
{'=' * 50}

{summary_text}

"""
    
    if include_original and book_info.get('original_text'):
        content += f"""
{'=' * 50}
ORIGINAL TEXT EXCERPT
{'=' * 50}

{book_info.get('original_text', '')[:1000]}...
[Original text truncated - full text available in app]
"""
    
    return content