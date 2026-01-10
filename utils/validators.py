# utils/validators.py
import re
import os
from typing import Tuple, Optional, List
from pathlib import Path
from utils.error_handler import ValidationError

class InputValidator:
    """Centralized input validation"""
    
    # Allowed file extensions and their MIME types
    ALLOWED_EXTENSIONS = {
        '.pdf': 'application/pdf',
        '.txt': 'text/plain',
        '.docx': 'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
        '.doc': 'application/msword',
        '.rtf': 'application/rtf'
    }
    
    MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB
    
    @staticmethod
    def validate_email(email: str) -> Tuple[bool, str]:
        """Validate email format"""
        if not email or len(email.strip()) == 0:
            return False, "Email is required"
        
        if len(email) > 254:
            return False, "Email is too long (max 254 characters)"
        
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        if not re.match(pattern, email):
            return False, "Invalid email format"
        
        return True, ""
    
    @staticmethod
    def validate_password(password: str) -> Tuple[bool, str]:
        """Validate password strength"""
        if not password or len(password.strip()) == 0:
            return False, "Password is required"
        
        if len(password) < 8:
            return False, "Password must be at least 8 characters"
        
        if len(password) > 128:
            return False, "Password is too long (max 128 characters)"
        
        if not any(char.isdigit() for char in password):
            return False, "Password must contain at least one number"
        
        if not any(char.isupper() for char in password):
            return False, "Password must contain at least one uppercase letter"
        
        if not any(char.islower() for char in password):
            return False, "Password must contain at least one lowercase letter"
        
        # Check for common weak passwords
        weak_passwords = ['password', '12345678', 'qwerty123', 'admin123', 'letmein']
        if password.lower() in weak_passwords:
            return False, "Password is too common"
        
        return True, ""
    
    @staticmethod
    def validate_name(name: str) -> Tuple[bool, str]:
        """Validate user name"""
        if not name or len(name.strip()) < 2:
            return False, "Name must be at least 2 characters"
        
        if len(name) > 100:
            return False, "Name is too long (max 100 characters)"
        
        # Allow letters, spaces, hyphens, apostrophes
        if not re.match(r'^[A-Za-z\s\-\'\.]+$', name):
            return False, "Name can only contain letters, spaces, hyphens, and apostrophes"
        
        return True, ""
    
    @staticmethod
    def validate_file(file_obj, check_size: bool = True) -> Tuple[bool, str, Optional[str]]:
        """
        Validate uploaded file
        Returns: (is_valid, error_message, file_type)
        """
        try:
            if file_obj is None:
                return False, "No file selected", None
            
            # Check file name
            if not file_obj.name or len(file_obj.name.strip()) == 0:
                return False, "Invalid file name", None
            
            # Check file size
            if check_size:
                file_size = len(file_obj.getvalue())
                if file_size > InputValidator.MAX_FILE_SIZE:
                    max_mb = InputValidator.MAX_FILE_SIZE // (1024 * 1024)
                    return False, f"File is too large (max {max_mb}MB)", None
                
                if file_size == 0:
                    return False, "File is empty", None
            
            # Check file extension
            ext = Path(file_obj.name).suffix.lower()
            if ext not in InputValidator.ALLOWED_EXTENSIONS:
                allowed = ', '.join(InputValidator.ALLOWED_EXTENSIONS.keys())
                return False, f"File type not allowed. Allowed: {allowed}", None
            
            return True, "", ext
            
        except Exception as e:
            return False, f"File validation error: {str(e)}", None
    
    @staticmethod
    def validate_text(text: str, min_length: int = 100, max_length: int = 1000000) -> Tuple[bool, str]:
        """Validate text input"""
        if not text or len(text.strip()) < min_length:
            return False, f"Text must be at least {min_length} characters"
        
        if len(text) > max_length:
            return False, f"Text is too long (max {max_length} characters)"
        
        # Check for potentially malicious content
        suspicious_patterns = [
            (r'<script.*?>.*?</script>', "Script tags not allowed"),
            (r'on\w+\s*=', "Event handlers not allowed"),
            (r'javascript:', "JavaScript URLs not allowed"),
            (r'data:', "Data URLs not allowed"),
            (r'eval\(', "Eval function not allowed"),
            (r'document\.', "Document access not allowed"),
            (r'window\.', "Window access not allowed"),
        ]
        
        for pattern, message in suspicious_patterns:
            if re.search(pattern, text, re.IGNORECASE):
                return False, message
        
        return True, ""
    
    @staticmethod
    def validate_summary_options(
        length: str,
        style: str,
        custom_instructions: Optional[str] = None
    ) -> Tuple[bool, str]:
        """Validate summary generation options"""
        valid_lengths = ["short", "medium", "long"]
        valid_styles = ["paragraph", "bullets", "detailed", "concise"]
        
        if length not in valid_lengths:
            return False, f"Invalid summary length. Choose from: {', '.join(valid_lengths)}"
        
        if style not in valid_styles:
            return False, f"Invalid summary style. Choose from: {', '.join(valid_styles)}"
        
        if custom_instructions and len(custom_instructions) > 1000:
            return False, "Custom instructions too long (max 1000 characters)"
        
        return True, ""
    
    @staticmethod
    def sanitize_input(text: str, allow_html: bool = False) -> str:
        """Sanitize user input to prevent XSS"""
        if not text:
            return ""
        
        # Remove HTML tags if not allowed
        if not allow_html:
            text = re.sub(r'<[^>]*>', '', text)
        
        # Escape special characters
        replacements = {
            '&': '&amp;',
            '<': '&lt;',
            '>': '&gt;',
            '"': '&quot;',
            "'": '&#x27;',
            '/': '&#x2F;',
            '\\': '&#x5C;'
        }
        
        for char, replacement in replacements.items():
            text = text.replace(char, replacement)
        
        return text.strip()

    @staticmethod
    def validate_book_title(title: str) -> Tuple[bool, str]:
        """Validate book title"""
        if not title or len(title.strip()) == 0:
            return False, "Book title is required"
        
        if len(title) > 200:
            return False, "Book title is too long (max 200 characters)"
        
        # Check for malicious content
        if re.search(r'[<>\"\']', title):
            return False, "Title contains invalid characters"
        
        return True, ""

# Validation decorator
def validate_input(**validators):
    """Decorator for input validation"""
    def decorator(func):
        import inspect
        from functools import wraps
        
        @wraps(func)
        def wrapper(*args, **kwargs):
            # Get function parameter names
            sig = inspect.signature(func)
            params = list(sig.parameters.keys())
            
            # Map args to param names
            args_dict = {}
            for i, arg in enumerate(args):
                if i < len(params):
                    args_dict[params[i]] = arg
            
            # Add kwargs
            args_dict.update(kwargs)
            
            # Validate each parameter
            for param_name, validator_func in validators.items():
                if param_name in args_dict:
                    value = args_dict[param_name]
                    is_valid, error_msg = validator_func(value)
                    if not is_valid:
                        raise ValidationError(f"{param_name}: {error_msg}")
            
            return func(*args, **kwargs)
        return wrapper
    return decorator