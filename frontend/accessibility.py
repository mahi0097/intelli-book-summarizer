# frontend/accessibility.py
import streamlit as st
from typing import Dict, List, Optional, Callable

class AccessibilityManager:
    """Manager for accessibility features"""
    
    def __init__(self):
        self.features = {
            "high_contrast": False,
            "large_text": False,
            "reduced_motion": False,
            "screen_reader": False,
            "keyboard_navigation": True
        }
        
        # ARIA landmark roles for page sections
        self.landmarks = {
            "header": "banner",
            "nav": "navigation",
            "main": "main",
            "sidebar": "complementary",
            "footer": "contentinfo",
            "search": "search",
            "form": "form"
        }
    
    def inject_accessibility_css(self):
        """Inject accessibility CSS styles"""
        css = """
        <style>
            /* High contrast mode */
            .high-contrast {
                --text-color: #000000 !important;
                --bg-color: #FFFFFF !important;
                --primary-color: #0000EE !important;
                --secondary-color: #551A8B !important;
                --border-color: #000000 !important;
            }
            
            .high-contrast .stApp,
            .high-contrast .card,
            .high-contrast .summary-box {
                background-color: var(--bg-color) !important;
                color: var(--text-color) !important;
                border-color: var(--border-color) !important;
            }
            
            .high-contrast a {
                color: var(--primary-color) !important;
                text-decoration: underline !important;
            }
            
            .high-contrast button {
                border: 2px solid var(--border-color) !important;
            }
            
            /* Large text mode */
            .large-text {
                font-size: 1.2rem !important;
            }
            
            .large-text h1 { font-size: 2.5rem !important; }
            .large-text h2 { font-size: 2rem !important; }
            .large-text h3 { font-size: 1.75rem !important; }
            .large-text p, 
            .large-text li, 
            .large-text .stText { 
                font-size: 1.2rem !important;
                line-height: 1.8 !important;
            }
            
            .large-text button {
                padding: 12px 24px !important;
                min-height: 48px !important;
            }
            
            /* Reduced motion */
            .reduced-motion * {
                animation-duration: 0.01ms !important;
                animation-iteration-count: 1 !important;
                transition-duration: 0.01ms !important;
            }
            
            /* Focus indicators for keyboard navigation */
            .keyboard-nav button:focus,
            .keyboard-nav input:focus,
            .keyboard-nav select:focus,
            .keyboard-nav textarea:focus,
            .keyboard-nav a:focus {
                outline: 3px solid #005A9C !important;
                outline-offset: 2px !important;
                position: relative !important;
                z-index: 1000 !important;
            }
            
            /* Screen reader only text */
            .sr-only {
                position: absolute;
                width: 1px;
                height: 1px;
                padding: 0;
                margin: -1px;
                overflow: hidden;
                clip: rect(0, 0, 0, 0);
                white-space: nowrap;
                border: 0;
            }
            
            /* Skip to content link */
            .skip-to-content {
                position: absolute;
                top: -40px;
                left: 0;
                background: #005A9C;
                color: white;
                padding: 8px;
                z-index: 1001;
                text-decoration: none;
            }
            
            .skip-to-content:focus {
                top: 0;
            }
            
            /* Accessible form labels */
            .accessible-label {
                display: block;
                margin-bottom: 0.5rem;
                font-weight: 600;
            }
            
            .accessible-label .required {
                color: #DC2626;
            }
            
            /* Error states for forms */
            .error-field {
                border-color: #DC2626 !important;
                border-width: 2px !important;
            }
            
            .error-message {
                color: #DC2626;
                font-size: 0.875rem;
                margin-top: 0.25rem;
            }
            
            /* Loading indicators for screen readers */
            .sr-loading {
                position: absolute;
                left: -10000px;
                top: auto;
                width: 1px;
                height: 1px;
                overflow: hidden;
            }
            
            /* Alternative text indicators */
            .alt-text-indicator::after {
                content: " 📷";
                font-size: 0.8em;
            }
        </style>
        """
        
        st.markdown(css, unsafe_allow_html=True)
    
    def setup_accessibility_features(self):
        """Setup accessibility features in session state"""
        if "accessibility" not in st.session_state:
            st.session_state.accessibility = self.features.copy()
        
        # Apply CSS based on settings
        css_classes = []
        if st.session_state.accessibility["high_contrast"]:
            css_classes.append("high-contrast")
        if st.session_state.accessibility["large_text"]:
            css_classes.append("large-text")
        if st.session_state.accessibility["reduced_motion"]:
            css_classes.append("reduced-motion")
        if st.session_state.accessibility["keyboard_navigation"]:
            css_classes.append("keyboard-nav")
        
        if css_classes:
            body_class = " ".join(css_classes)
            st.markdown(f"<body class='{body_class}'>", unsafe_allow_html=True)
    
    def create_skip_link(self, target_id: str = "main-content"):
        """Create skip to content link"""
        skip_link = f"""
        <a href="#{target_id}" class="skip-to-content">
            Skip to main content
        </a>
        """
        st.markdown(skip_link, unsafe_allow_html=True)
    
    def create_landmark(self, role: str, label: Optional[str] = None, element: str = "div"):
        """Create ARIA landmark with proper attributes"""
        if role not in self.landmarks.values():
            role = "region"
        
        aria_label = f' aria-label="{label}"' if label else ""
        return f'<{element} role="{role}"{aria_label}>'
    
    def close_landmark(self, element: str = "div"):
        """Close landmark element"""
        return f"</{element}>"
    
    def sr_only(self, text: str):
        """Create screen-reader only text"""
        return f'<span class="sr-only">{text}</span>'
    
    def create_accessible_button(self, label: str, key: str, icon: str = "", 
                               tooltip: str = "", disabled: bool = False):
        """Create accessible button with proper ARIA attributes"""
        aria_label = f' aria-label="{tooltip}"' if tooltip else ""
        disabled_attr = " disabled" if disabled else ""
        
        button_html = f"""
        <button {aria_label}{disabled_attr} data-testid="{key}">
            {icon} {label}
        </button>
        """
        
        return button_html
    
    def create_accessible_input(self, label: str, input_id: str, required: bool = False,
                              error: Optional[str] = None, help_text: Optional[str] = None):
        """Create accessible form input"""
        required_indicator = '<span class="required" aria-hidden="true">*</span>' if required else ''
        required_attr = ' required aria-required="true"' if required else ''
        error_class = ' class="error-field"' if error else ''
        aria_invalid = ' aria-invalid="true"' if error else ' aria-invalid="false"'
        aria_describedby = []
        
        if error:
            aria_describedby.append(f"{input_id}-error")
        if help_text:
            aria_describedby.append(f"{input_id}-help")
        
        aria_describedby_attr = f' aria-describedby="{" ".join(aria_describedby)}"' if aria_describedby else ''
        
        html = f"""
        <div style="margin-bottom: 1rem;">
            <label for="{input_id}" class="accessible-label">
                {label}{required_indicator}
            </label>
            
            <input type="text" id="{input_id}" name="{input_id}" 
                   {required_attr}{error_class}{aria_invalid}{aria_describedby_attr}>
            
            {f'<div id="{input_id}-help" class="help-text">{help_text}</div>' if help_text else ''}
            {f'<div id="{input_id}-error" class="error-message" role="alert">{error}</div>' if error else ''}
        </div>
        """
        
        return html
    
    def create_accessible_select(self, label: str, select_id: str, options: List[Dict],
                               required: bool = False, error: Optional[str] = None):
        """Create accessible select dropdown"""
        required_indicator = '<span class="required" aria-hidden="true">*</span>' if required else ''
        required_attr = ' required aria-required="true"' if required else ''
        error_class = ' class="error-field"' if error else ''
        aria_invalid = ' aria-invalid="true"' if error else ' aria-invalid="false"'
        aria_describedby = f' aria-describedby="{select_id}-error"' if error else ''
        
        options_html = ""
        for option in options:
            value = option.get("value", "")
            text = option.get("text", "")
            selected = ' selected' if option.get("selected", False) else ''
            options_html += f'<option value="{value}"{selected}>{text}</option>'
        
        html = f"""
        <div style="margin-bottom: 1rem;">
            <label for="{select_id}" class="accessible-label">
                {label}{required_indicator}
            </label>
            
            <select id="{select_id}" name="{select_id}" 
                    {required_attr}{error_class}{aria_invalid}{aria_describedby}>
                {options_html}
            </select>
            
            {f'<div id="{select_id}-error" class="error-message" role="alert">{error}</div>' if error else ''}
        </div>
        """
        
        return html
    
    def create_loading_indicator(self, message: str = "Loading, please wait"):
        """Create accessible loading indicator"""
        html = f"""
        <div role="status" aria-live="polite" aria-busy="true">
            <div class="sr-loading">{message}</div>
            <div aria-hidden="true">⏳ {message}</div>
        </div>
        """
        
        return html
    
    def create_success_message(self, message: str, message_id: Optional[str] = None):
        """Create accessible success message"""
        role_attr = ' role="status" aria-live="polite"' if not message_id else f' id="{message_id}"'
        
        html = f"""
        <div{role_attr} class="success-banner">
            ✅ {message}
        </div>
        """
        
        return html
    
    def create_error_message(self, message: str, message_id: Optional[str] = None):
        """Create accessible error message"""
        role_attr = ' role="alert" aria-live="assertive"' if not message_id else f' id="{message_id}"'
        
        html = f"""
        <div{role_attr} class="error-banner">
            ❌ {message}
        </div>
        """
        
        return html
    
    def create_data_table(self, data: List[Dict], caption: str = "", 
                         column_headers: List[str] = None):
        """Create accessible data table"""
        if not data:
            return '<p>No data available</p>'
        
        # Generate headers
        if column_headers:
            headers = column_headers
        else:
            headers = list(data[0].keys()) if data else []
        
        headers_html = "".join([f"<th scope='col'>{header}</th>" for header in headers])
        
        # Generate rows
        rows_html = ""
        for i, row in enumerate(data):
            row_html = "<tr>"
            for j, (key, value) in enumerate(row.items()):
                if j == 0:
                    row_html += f"<th scope='row'>{value}</th>"
                else:
                    row_html += f"<td>{value}</td>"
            row_html += "</tr>"
            rows_html += row_html
        
        caption_html = f"<caption>{caption}</caption>" if caption else ""
        
        html = f"""
        <div role="region" aria-label="{caption}" tabindex="0">
            <table>
                {caption_html}
                <thead>
                    <tr>{headers_html}</tr>
                </thead>
                <tbody>
                    {rows_html}
                </tbody>
            </table>
        </div>
        """
        
        return html
    
    def create_accessibility_panel(self):
        """Create accessibility settings panel"""
        with st.sidebar.expander("♿ Accessibility", expanded=False):
            st.markdown("### Accessibility Settings")
            
            # High contrast toggle
            high_contrast = st.toggle(
                "High Contrast Mode",
                value=st.session_state.accessibility.get("high_contrast", False),
                help="Increase contrast for better visibility"
            )
            
            # Large text toggle
            large_text = st.toggle(
                "Large Text Mode",
                value=st.session_state.accessibility.get("large_text", False),
                help="Increase text size for better readability"
            )
            
            # Reduced motion toggle
            reduced_motion = st.toggle(
                "Reduce Motion",
                value=st.session_state.accessibility.get("reduced_motion", False),
                help="Reduce animations and transitions"
            )
            
            # Keyboard navigation toggle
            keyboard_nav = st.toggle(
                "Enhanced Keyboard Navigation",
                value=st.session_state.accessibility.get("keyboard_navigation", True),
                help="Improve keyboard navigation support"
            )
            
            # Update session state
            st.session_state.accessibility.update({
                "high_contrast": high_contrast,
                "large_text": large_text,
                "reduced_motion": reduced_motion,
                "keyboard_navigation": keyboard_nav
            })
            
            # Apply button
            if st.button("Apply Settings", use_container_width=True):
                st.rerun()
            
            st.markdown("---")
            st.markdown("**Keyboard Shortcuts:**")
            st.markdown("""
            - `Tab`: Navigate between elements
            - `Shift + Tab`: Navigate backwards
            - `Enter`: Activate buttons/links
            - `Space`: Toggle checkboxes/buttons
            - `Esc`: Close modals/dialogs
            """)
    
    def setup_keyboard_shortcuts(self):
        """Setup keyboard shortcuts for common actions"""
        shortcuts_js = """
        <script>
        document.addEventListener('keydown', function(event) {
            // Ctrl/Cmd + S: Save
            if ((event.ctrlKey || event.metaKey) && event.key === 's') {
                event.preventDefault();
                window.parent.postMessage({type: 'streamlit:setComponentValue', value: 'save_action'}, '*');
            }
            
            // Ctrl/Cmd + F: Search
            if ((event.ctrlKey || event.metaKey) && event.key === 'f') {
                event.preventDefault();
                window.parent.postMessage({type: 'streamlit:setComponentValue', value: 'search_action'}, '*');
            }
            
            // Escape: Close modals
            if (event.key === 'Escape') {
                window.parent.postMessage({type: 'streamlit:setComponentValue', value: 'escape_action'}, '*');
            }
            
            // Question mark: Help
            if (event.key === '?') {
                window.parent.postMessage({type: 'streamlit:setComponentValue', value: 'help_action'}, '*');
            }
        });
        </script>
        """
        
        st.markdown(shortcuts_js, unsafe_allow_html=True)

# Global accessibility manager instance
accessibility_manager = AccessibilityManager()

# Convenience functions
def setup_accessibility():
    """Setup accessibility features (convenience function)"""
    accessibility_manager.setup_accessibility_features()
    accessibility_manager.inject_accessibility_css()

def show_accessibility_panel():
    """Show accessibility panel (convenience function)"""
    accessibility_manager.create_accessibility_panel()

def create_accessible_input(label: str, input_id: str, **kwargs):
    """Create accessible input (convenience function)"""
    return accessibility_manager.create_accessible_input(label, input_id, **kwargs)