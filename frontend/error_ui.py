# frontend/error_ui.py
import streamlit as st
from typing import Optional, Callable, List
import traceback
import time

def display_error_ui(
    error_message: str,
    user_friendly_message: Optional[str] = None,
    suggestions: Optional[List[str]] = None,
    error_code: Optional[str] = None,
    show_retry: bool = True
):
    """
    Display user-friendly error messages
    """
    with st.container():
        # Error header
        st.error("❌ " + (user_friendly_message or "An error occurred"))
        
        # Error reference code
        if error_code:
            st.caption(f"**Error reference:** `{error_code}`")
            st.caption("Please provide this code if contacting support.")
        
        # Suggestions to fix
        if suggestions:
            with st.expander("💡 **Suggestions to fix this issue**", expanded=True):
                for i, suggestion in enumerate(suggestions, 1):
                    st.write(f"{i}. {suggestion}")
        
        # Technical details (collapsed by default)
        with st.expander("🔧 **Technical details (for support)**", expanded=False):
            st.code(error_message[:1000] + ("..." if len(error_message) > 1000 else ""))
            
            # Show traceback if available
            if hasattr(st.session_state, 'last_traceback'):
                st.write("**Traceback:**")
                st.code(st.session_state.last_traceback)
        
        # Action buttons
        col1, col2, col3 = st.columns(3)
        
        with col1:
            if show_retry and st.button("🔄 Try Again", key="error_retry"):
                st.rerun()
        
        with col2:
            if st.button("🏠 Go Home", key="error_home"):
                st.session_state.page = "home"
                st.rerun()
        
        with col3:
            if st.button("📋 Copy Error Details", key="error_copy"):
                error_details = f"Error: {error_message}\nCode: {error_code}\nTime: {time.ctime()}"
                st.code(error_details)
                st.info("Error details copied to clipboard (simulated)")

def safe_execute(
    func: Callable,
    success_message: Optional[str] = None,
    on_error: Optional[Callable] = None,
    loading_message: Optional[str] = None,
    show_errors: bool = True
):
    """
    Execute a function safely with error handling
    """
    from utils.error_handler import ErrorLogger
    
    # Show loading spinner if message provided
    if loading_message:
        with st.spinner(loading_message):
            return _execute_safely(func, success_message, on_error, show_errors, ErrorLogger)
    else:
        return _execute_safely(func, success_message, on_error, show_errors, ErrorLogger)

def _execute_safely(func, success_message, on_error, show_errors, ErrorLogger):
    """Internal execution with error handling"""
    try:
        result = func()
        if success_message:
            st.success(success_message)
        return result
        
    except Exception as e:
        # Store traceback for debugging
        st.session_state.last_traceback = traceback.format_exc()
        
        # Log the error
        ErrorLogger.log_error(
            "frontend_error",
            f"Error in {func.__name__}: {str(e)}",
            user_id=st.session_state.get("user_id"),
            extra_data={"traceback": traceback.format_exc()}
        )
        
        # Get error details
        error_msg = str(e)
        user_msg = getattr(e, 'user_message', "Something went wrong. Please try again.")
        error_code = getattr(e, 'code', 'UNKNOWN')
        
        # Get troubleshooting suggestions
        from utils.fallback import SummaryFallback
        error_type = getattr(e, 'code', 'unknown').lower().replace('_error', '')
        suggestions = SummaryFallback.get_troubleshooting_suggestions(error_type)
        
        # Display error UI
        if show_errors:
            display_error_ui(
                error_message=error_msg,
                user_friendly_message=user_msg,
                suggestions=suggestions,
                error_code=error_code
            )
        
        # Execute custom error handler
        if on_error:
            on_error(e)
        
        return None

def validate_form_inputs(form_data: dict) -> tuple:
    """
    Validate form inputs and return errors
    """
    from utils.validators import InputValidator
    
    errors = {}
    
    for field, value in form_data.items():
        if field == 'email' and value:
            is_valid, error_msg = InputValidator.validate_email(value)
            if not is_valid:
                errors[field] = error_msg
        
        elif field == 'password' and value:
            is_valid, error_msg = InputValidator.validate_password(value)
            if not is_valid:
                errors[field] = error_msg
        
        elif field == 'name' and value:
            is_valid, error_msg = InputValidator.validate_name(value)
            if not is_valid:
                errors[field] = error_msg
        
        elif field == 'text' and value:
            is_valid, error_msg = InputValidator.validate_text(value)
            if not is_valid:
                errors[field] = error_msg
        
        elif field == 'title' and value:
            is_valid, error_msg = InputValidator.validate_book_title(value)
            if not is_valid:
                errors[field] = error_msg
    
    return len(errors) == 0, errors

def show_loading_with_timeout(message: str, timeout: int = 30, progress_callback=None):
    """
    Show loading spinner with timeout
    """
    from utils.error_handler import ModelError
    
    start_time = time.time()
    placeholder = st.empty()
    
    with placeholder.container():
        progress_bar = st.progress(0)
        status_text = st.empty()
        
        while time.time() - start_time < timeout:
            elapsed = time.time() - start_time
            progress = min(elapsed / timeout, 1.0)
            
            if progress_callback:
                progress = progress_callback(progress)
            
            progress_bar.progress(progress)
            status_text.text(f"{message}... ({int(elapsed)}s)")
            
            time.sleep(0.5)
            
            # Check if we should break early
            if hasattr(st.session_state, 'operation_completed'):
                if st.session_state.operation_completed:
                    placeholder.empty()
                    return True
        
        # Timeout reached
        placeholder.empty()
        raise ModelError(f"Operation timed out after {timeout} seconds")

def show_form_errors(errors: dict):
    """Display form validation errors"""
    if errors:
        with st.container():
            st.error("⚠️ Please fix the following errors:")
            for field, error in errors.items():
                st.write(f"• **{field.title()}:** {error}")

def create_success_message(message: str, auto_close: bool = True):
    """Create a success message that auto-closes"""
    success_placeholder = st.empty()
    with success_placeholder.container():
        st.success(message)
    
    if auto_close:
        time.sleep(3)
        success_placeholder.empty()