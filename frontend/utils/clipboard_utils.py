import streamlit as st
import json
import base64
import html

def create_copy_button_simple(text, button_text="📋 Copy Summary", button_id=None):
    """
    Create a simple, reliable copy button using modern clipboard API
    
    This version uses a direct JavaScript approach that works reliably in Streamlit
    """
    # Generate unique ID if not provided
    if not button_id:
        import uuid
        button_id = f"copy-btn-{uuid.uuid4().hex[:8]}"
    
    # JSON stringify the text (this properly escapes everything)
    js_text = json.dumps(text)
    
    html_code = f'''
    <button id="{button_id}" 
            style="padding: 12px 24px; background: linear-gradient(45deg, #2196F3, #1976D2); color: white; border: none; border-radius: 6px; cursor: pointer; font-size: 14px; font-weight: 600; margin: 10px 0; width: 100%; transition: all 0.3s ease;"
            onclick="copyText({js_text}, this)">
        {button_text}
    </button>
    <script>
    function copyText(text, button) {{
        // Use modern Clipboard API if available
        if (navigator.clipboard && window.isSecureContext) {{
            navigator.clipboard.writeText(text).then(() => {{
                showSuccess(button);
            }}).catch(err => {{
                console.error('Clipboard API failed:', err);
                // Fallback to textarea method
                fallbackCopy(text, button);
            }});
        }} else {{
            // Use fallback method
            fallbackCopy(text, button);
        }}
    }}
    
    function fallbackCopy(text, button) {{
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
                showSuccess(button);
            }} else {{
                showError(button);
            }}
        }} catch (err) {{
            console.error('Fallback copy failed:', err);
            showError(button);
        }} finally {{
            document.body.removeChild(textarea);
        }}
    }}
    
    function showSuccess(button) {{
        const originalText = button.innerHTML;
        button.innerHTML = '✅ Copied!';
        button.style.background = 'linear-gradient(45deg, #28a745, #218838)';
        
        // Show toast
        showToast('Summary copied to clipboard!', 'success');
        
        setTimeout(() => {{
            button.innerHTML = originalText;
            button.style.background = 'linear-gradient(45deg, #2196F3, #1976D2)';
        }}, 2000);
    }}
    
    function showError(button) {{
        const originalText = button.innerHTML;
        button.innerHTML = '❌ Failed';
        button.style.background = '#dc3545';
        
        showToast('Failed to copy. Please try again.', 'error');
        
        setTimeout(() => {{
            button.innerHTML = originalText;
            button.style.background = 'linear-gradient(45deg, #2196F3, #1976D2)';
        }}, 2000);
    }}
    
    function showToast(message, type = 'success') {{
        // Remove existing toast
        const existingToast = document.querySelector('.clipboard-toast');
        if (existingToast) {{
            existingToast.remove();
        }}
        
        // Create toast
        const toast = document.createElement('div');
        toast.className = 'clipboard-toast';
        toast.innerHTML = message;
        toast.style.cssText = `
            position: fixed;
            top: 20px;
            right: 20px;
            background: ${{type === 'success' ? '#28a745' : '#dc3545'}};
            color: white;
            padding: 12px 24px;
            border-radius: 5px;
            z-index: 10000;
            animation: toastFade 2s forwards;
            box-shadow: 0 4px 12px rgba(0,0,0,0.15);
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            font-size: 14px;
            font-weight: 500;
            pointer-events: none;
        `;
        
        // Add animation if not exists
        if (!document.querySelector('#toast-styles')) {{
            const style = document.createElement('style');
            style.id = 'toast-styles';
            style.textContent = `
                @keyframes toastFade {{
                    0% {{ opacity: 0; transform: translateY(-20px); }}
                    10% {{ opacity: 1; transform: translateY(0); }}
                    90% {{ opacity: 1; transform: translateY(0); }}
                    100% {{ opacity: 0; transform: translateY(-20px); }}
                }}
            `;
            document.head.appendChild(style);
        }}
        
        document.body.appendChild(toast);
        
        // Remove after animation
        setTimeout(() => {{
            if (toast.parentNode) {{
                toast.parentNode.removeChild(toast);
            }}
        }}, 2000);
    }}
    </script>
    '''
    return html_code

def create_copy_button_with_icon_simple(text, icon="📋", label="Copy", variant="primary"):
    """
    Create a styled copy button with icon (simple version)
    """
    variants = {
        "primary": "linear-gradient(45deg, #2196F3, #1976D2)",
        "secondary": "linear-gradient(45deg, #6c757d, #5a6268)",
        "success": "linear-gradient(45deg, #28a745, #218838)",
        "danger": "linear-gradient(45deg, #dc3545, #c82333)",
        "warning": "linear-gradient(45deg, #ffc107, #e0a800)",
        "info": "linear-gradient(45deg, #17a2b8, #138496)"
    }
    
    bg_color = variants.get(variant, variants["primary"])
    
    button_text = f"{icon} {label}"
    
    return create_copy_button_simple(text, button_text)

def create_floating_copy_button_simple(text, position="bottom-right"):
    """
    Create a floating copy button (simple version)
    """
    positions = {
        "bottom-right": "bottom: 20px; right: 20px;",
        "bottom-left": "bottom: 20px; left: 20px;",
        "top-right": "top: 20px; right: 20px;",
        "top-left": "top: 20px; left: 20px;"
    }
    
    pos_style = positions.get(position, positions["bottom-right"])
    
    # JSON stringify the text
    js_text = json.dumps(text)
    
    html_code = f'''
    <div style="position: fixed; {pos_style} z-index: 9999;">
        <button onclick="copyText({js_text}, this)"
                style="padding: 14px 28px; background: linear-gradient(45deg, #2196F3, #1976D2); color: white; border: none; border-radius: 50px; cursor: pointer; font-size: 14px; font-weight: 600; box-shadow: 0 4px 16px rgba(0,0,0,0.2); transition: all 0.3s ease; display: flex; align-items: center; gap: 10px;">
            📋 Copy Summary
        </button>
    </div>
    <script>
    function copyText(text, button) {{
        if (navigator.clipboard && window.isSecureContext) {{
            navigator.clipboard.writeText(text).then(() => {{
                const originalText = button.innerHTML;
                button.innerHTML = '✅ Copied!';
                button.style.background = 'linear-gradient(45deg, #28a745, #218838)';
                
                // Show toast
                const toast = document.createElement('div');
                toast.innerHTML = '✓ Summary copied!';
                toast.style.cssText = 'position: fixed; top: 20px; right: 20px; background: #28a745; color: white; padding: 12px 24px; border-radius: 5px; z-index: 10000; animation: toastFade 2s forwards;';
                document.body.appendChild(toast);
                setTimeout(() => toast.remove(), 2000);
                
                setTimeout(() => {{
                    button.innerHTML = originalText;
                    button.style.background = 'linear-gradient(45deg, #2196F3, #1976D2)';
                }}, 2000);
            }}).catch(err => {{
                console.error('Copy failed:', err);
                fallbackCopy(text, button);
            }});
        }} else {{
            fallbackCopy(text, button);
        }}
    }}
    
    function fallbackCopy(text, button) {{
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
                const originalText = button.innerHTML;
                button.innerHTML = '✅ Copied!';
                button.style.background = 'linear-gradient(45deg, #28a745, #218838)';
                
                setTimeout(() => {{
                    button.innerHTML = originalText;
                    button.style.background = 'linear-gradient(45deg, #2196F3, #1976D2)';
                }}, 2000);
            }}
        }} catch (err) {{
            console.error('Fallback copy failed:', err);
            button.innerHTML = '❌ Failed';
            button.style.background = '#dc3545';
            setTimeout(() => {{
                button.innerHTML = '📋 Copy Summary';
                button.style.background = 'linear-gradient(45deg, #2196F3, #1976D2)';
            }}, 2000);
        }} finally {{
            document.body.removeChild(textarea);
        }}
    }}
    
    // Add animation if not exists
    if (!document.querySelector('#floating-toast-styles')) {{
        const style = document.createElement('style');
        style.id = 'floating-toast-styles';
        style.textContent = `
            @keyframes toastFade {{
                0% {{ opacity: 0; transform: translateY(-20px); }}
                10% {{ opacity: 1; transform: translateY(0); }}
                90% {{ opacity: 1; transform: translateY(0); }}
                100% {{ opacity: 0; transform: translateY(-20px); }}
            }}
        `;
        document.head.appendChild(style);
    }}
    </script>
    '''
    return html_code

def create_working_copy_button(text, button_label="📋 Copy Summary"):
    """
    Create a copy button that definitely works with base64 encoding
    """
    # Use base64 encoding for safety
    encoded_text = base64.b64encode(text.encode()).decode()
    
    html_code = f'''
    <button onclick="copyBase64Text('{encoded_text}', this)"
            style="padding: 12px 24px; background: #2196F3; color: white; border: none; border-radius: 6px; cursor: pointer; font-size: 14px; font-weight: 600; margin: 10px 0; width: 100%;">
        {button_label}
    </button>
    <script>
    function copyBase64Text(encodedText, button) {{
        // Decode from base64
        const text = atob(encodedText);
        
        // Try modern clipboard API first
        if (navigator.clipboard && window.isSecureContext) {{
            navigator.clipboard.writeText(text).then(() => {{
                showCopySuccess(button);
            }}).catch(err => {{
                console.error('Modern clipboard failed:', err);
                useTextareaCopy(text, button);
            }});
        }} else {{
            useTextareaCopy(text, button);
        }}
    }}
    
    function useTextareaCopy(text, button) {{
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
                showCopySuccess(button);
            }} else {{
                showCopyError(button);
            }}
        }} catch (err) {{
            console.error('Textarea copy failed:', err);
            showCopyError(button);
        }} finally {{
            document.body.removeChild(textarea);
        }}
    }}
    
    function showCopySuccess(button) {{
        const originalText = button.innerHTML;
        button.innerHTML = '✅ Copied!';
        button.style.background = '#28a745';
        
        // Simple toast
        const toast = document.createElement('div');
        toast.innerHTML = '✓ Copied to clipboard!';
        toast.style.cssText = 'position: fixed; top: 20px; right: 20px; background: #28a745; color: white; padding: 12px 24px; border-radius: 5px; z-index: 10000; font-size: 14px;';
        document.body.appendChild(toast);
        setTimeout(() => toast.remove(), 2000);
        
        setTimeout(() => {{
            button.innerHTML = originalText;
            button.style.background = '#2196F3';
        }}, 2000);
    }}
    
    function showCopyError(button) {{
        const originalText = button.innerHTML;
        button.innerHTML = '❌ Failed';
        button.style.background = '#dc3545';
        
        setTimeout(() => {{
            button.innerHTML = originalText;
            button.style.background = '#2196F3';
        }}, 2000);
    }}
    </script>
    '''
    return html_code