# utils/error_handler.py
import sys
import os
import logging
import traceback
from datetime import datetime
from functools import wraps
import time
from typing import Optional, Dict, Any
import hashlib

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/app_errors.log'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)

class AppError(Exception):
    """Base application error class"""
    def __init__(self, message: str, code: str = "APP_ERROR", user_message: Optional[str] = None):
        self.message = message
        self.code = code
        self.user_message = user_message or "An unexpected error occurred. Please try again."
        self.timestamp = datetime.now()
        self.error_id = hashlib.md5(f"{code}_{message}_{self.timestamp}".encode()).hexdigest()[:8]
        super().__init__(self.message)

class ValidationError(AppError):
    """Input validation errors"""
    def __init__(self, message: str, field: Optional[str] = None):
        user_msg = f"Please check your input: {message}"
        super().__init__(message, "VALIDATION_ERROR", user_msg)
        self.field = field

class DatabaseError(AppError):
    """Database operation errors"""
    def __init__(self, message: str):
        user_msg = "Database error. Our team has been notified."
        super().__init__(message, "DATABASE_ERROR", user_msg)

class FileProcessingError(AppError):
    """File processing errors"""
    def __init__(self, message: str):
        user_msg = f"File processing error: {message}"
        super().__init__(message, "FILE_ERROR", user_msg)

class ModelError(AppError):
    """AI model errors"""
    def __init__(self, message: str):
        user_msg = "Summary generation failed. Please try with different text or settings."
        super().__init__(message, "MODEL_ERROR", user_msg)

class RateLimitError(AppError):
    """Rate limiting errors"""
    def __init__(self, message: str, retry_after: int):
        user_msg = f"Too many requests. Please try again in {retry_after} seconds."
        super().__init__(message, "RATE_LIMIT_ERROR", user_msg)
        self.retry_after = retry_after

class AuthenticationError(AppError):
    """Authentication errors"""
    def __init__(self, message: str):
        user_msg = "Authentication failed. Please check your credentials."
        super().__init__(message, "AUTH_ERROR", user_msg)

def error_handler(func):
    """Decorator to handle errors in functions"""
    @wraps(func)
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except AppError as e:
            # Known application errors - log and re-raise
            logger.warning(f"AppError in {func.__name__}: {e.code} - {e.message}")
            raise
        except Exception as e:
            # Unknown errors - log with full traceback
            error_id = f"ERR_{int(time.time())}"
            logger.error(f"Unexpected error in {func.__name__} [{error_id}]: {str(e)}")
            logger.error(traceback.format_exc())
            
            # Return a user-friendly error
            raise AppError(
                f"Unexpected error occurred (Ref: {error_id})",
                "UNKNOWN_ERROR",
                f"Something went wrong. Reference: {error_id}"
            )
    return wrapper

def log_operation(operation: str):
    """Decorator to log operation start/end and timing"""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            start_time = time.time()
            logger.info(f"Starting {operation}")
            
            try:
                result = func(*args, **kwargs)
                elapsed = time.time() - start_time
                logger.info(f"Completed {operation} in {elapsed:.2f}s")
                return result
            except Exception as e:
                elapsed = time.time() - start_time
                logger.error(f"Failed {operation} after {elapsed:.2f}s: {str(e)}")
                raise
        return wrapper
    return decorator

class ErrorLogger:
    """Centralized error logging utility"""
    
    @staticmethod
    def log_error(
        error_type: str,
        message: str,
        user_id: Optional[str] = None,
        extra_data: Optional[Dict[str, Any]] = None
    ):
        """Log error with context"""
        log_entry = {
            "timestamp": datetime.utcnow().isoformat(),
            "error_type": error_type,
            "message": message,
            "user_id": user_id,
            "extra_data": extra_data or {},
            "traceback": traceback.format_exc() if sys.exc_info()[0] else None
        }
        
        logger.error(f"Error logged: {log_entry}")
        
        # Also log to database if available
        try:
            from utils.database import get_db
            db = get_db()
            if 'error_logs' in db.list_collection_names():
                db.error_logs.insert_one(log_entry)
        except:
            pass  # Don't fail if database logging fails
    
    @staticmethod
    def log_user_action(
        action: str,
        user_id: Optional[str] = None,
        success: bool = True,
        details: Optional[Dict[str, Any]] = None
    ):
        """Log user actions for audit trail"""
        log_entry = {
            "timestamp": datetime.utcnow().isoformat(),
            "action": action,
            "user_id": user_id,
            "success": success,
            "details": details or {}
        }
        
        logger.info(f"User action: {log_entry}")
        
        # Log to database if available
        try:
            from utils.database import get_db
            db = get_db()
            if 'audit_logs' in db.list_collection_names():
                db.audit_logs.insert_one(log_entry)
        except:
            pass

class RateLimiter:
    """Simple rate limiter"""
    
    def __init__(self, max_requests: int, time_window: int):
        self.max_requests = max_requests
        self.time_window = time_window  # in seconds
        self.requests = {}  # user_id -> list of timestamps
    
    def is_allowed(self, user_id: str) -> bool:
        """Check if request is allowed"""
        now = time.time()
        
        if user_id not in self.requests:
            self.requests[user_id] = []
        
        # Clean old requests
        self.requests[user_id] = [
            ts for ts in self.requests[user_id]
            if now - ts < self.time_window
        ]
        
        if len(self.requests[user_id]) >= self.max_requests:
            return False
        
        self.requests[user_id].append(now)
        return True
    
    def get_retry_after(self, user_id: str) -> int:
        """Get seconds until next allowed request"""
        if user_id not in self.requests or not self.requests[user_id]:
            return 0
        
        oldest_request = min(self.requests[user_id])
        return max(0, self.time_window - (time.time() - oldest_request))

# Global rate limiter instances
upload_limiter = RateLimiter(max_requests=10, time_window=300)  # 10 uploads per 5 minutes
summary_limiter = RateLimiter(max_requests=20, time_window=300)  # 20 summaries per 5 minutes
api_limiter = RateLimiter(max_requests=100, time_window=3600)  # 100 API calls per hour
login_limiter = RateLimiter(max_requests=5, time_window=300)  # 5 login attempts per 5 minutes