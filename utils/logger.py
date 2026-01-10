# utils/logger.py
import logging
import logging.handlers
import sys
import os
import json
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional
import traceback

class JSONFormatter(logging.Formatter):
    """JSON formatter for structured logging"""
    
    def format(self, record):
        log_record = {
            "timestamp": datetime.utcnow().isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
            "process_id": record.process,
            "thread_id": record.thread,
        }
        
        # Add exception info if available
        if record.exc_info:
            log_record["exception"] = {
                "type": record.exc_info[0].__name__ if record.exc_info[0] else None,
                "message": str(record.exc_info[1]) if record.exc_info[1] else None,
                "traceback": traceback.format_exception(*record.exc_info) if record.exc_info else None
            }
        
        # Add extra fields
        if hasattr(record, 'extra'):
            log_record.update(record.extra)
        
        return json.dumps(log_record, default=str)

class ColoredFormatter(logging.Formatter):
    """Colored console formatter for better readability"""
    
    COLORS = {
        'DEBUG': '\033[36m',      # Cyan
        'INFO': '\033[32m',       # Green
        'WARNING': '\033[33m',    # Yellow
        'ERROR': '\033[31m',      # Red
        'CRITICAL': '\033[41m',   # Red background
        'RESET': '\033[0m'        # Reset
    }
    
    def format(self, record):
        log_message = super().format(record)
        color = self.COLORS.get(record.levelname, self.COLORS['RESET'])
        return f"{color}{log_message}{self.COLORS['RESET']}"

class ApplicationLogger:
    """Centralized application logging system"""
    
    def __init__(self, app_name: str = "BookSummarizer"):
        self.app_name = app_name
        self.loggers: Dict[str, logging.Logger] = {}
        self.setup_logging()
    
    def setup_logging(self):
        """Setup comprehensive logging configuration"""
        
        # Create logs directory
        log_dir = Path("logs")
        log_dir.mkdir(exist_ok=True)
        
        # Define log file paths
        log_files = {
            "app": log_dir / "application.log",
            "errors": log_dir / "errors.log",
            "audit": log_dir / "audit.log",
            "performance": log_dir / "performance.log",
            "database": log_dir / "database.log"
        }
        
        # Root logger configuration
        root_logger = logging.getLogger()
        root_logger.setLevel(logging.DEBUG)
        
        # Remove existing handlers
        root_logger.handlers.clear()
        
        # Console handler (colored output)
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(logging.INFO)
        console_format = ColoredFormatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        console_handler.setFormatter(console_format)
        root_logger.addHandler(console_handler)
        
        # File handler for all logs (JSON format)
        file_handler = logging.handlers.RotatingFileHandler(
            log_files["app"],
            maxBytes=10*1024*1024,  # 10MB
            backupCount=5,
            encoding='utf-8'
        )
        file_handler.setLevel(logging.DEBUG)
        file_handler.setFormatter(JSONFormatter())
        root_logger.addHandler(file_handler)
        
        # Error file handler
        error_handler = logging.handlers.RotatingFileHandler(
            log_files["errors"],
            maxBytes=5*1024*1024,  # 5MB
            backupCount=3,
            encoding='utf-8'
        )
        error_handler.setLevel(logging.ERROR)
        error_format = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s\n%(pathname)s:%(lineno)d\n'
        )
        error_handler.setFormatter(error_format)
        root_logger.addHandler(error_handler)
        
        # Create specific loggers
        self.create_module_loggers()
        
        # Log startup
        self.get_logger("system").info(f"Logging system initialized for {self.app_name}")
    
    def create_module_loggers(self):
        """Create loggers for different application modules"""
        modules = [
            ("database", logging.INFO),
            ("auth", logging.INFO),
            ("upload", logging.INFO),
            ("summary", logging.INFO),
            ("api", logging.INFO),
            ("system", logging.INFO),
            ("performance", logging.DEBUG),
            ("audit", logging.INFO),
        ]
        
        for module_name, level in modules:
            logger = logging.getLogger(module_name)
            logger.setLevel(level)
            self.loggers[module_name] = logger
    
    def get_logger(self, module: str) -> logging.Logger:
        """Get logger for a specific module"""
        if module not in self.loggers:
            self.loggers[module] = logging.getLogger(module)
        return self.loggers[module]
    
    def log_operation(self, operation: str, duration: float, success: bool = True, 
                     user_id: Optional[str] = None, details: Optional[Dict] = None):
        """Log operation with timing and outcome"""
        logger = self.get_logger("performance")
        log_data = {
            "operation": operation,
            "duration_ms": duration * 1000,
            "success": success,
            "user_id": user_id,
            "timestamp": datetime.utcnow().isoformat(),
            "details": details or {}
        }
        
        if success:
            logger.info(f"Operation completed: {operation}", extra={"operation": log_data})
        else:
            logger.warning(f"Operation failed: {operation}", extra={"operation": log_data})
    
    def log_user_action(self, action: str, user_id: Optional[str] = None, 
                       success: bool = True, details: Optional[Dict] = None):
        """Log user actions for audit trail"""
        logger = self.get_logger("audit")
        log_data = {
            "action": action,
            "user_id": user_id,
            "success": success,
            "timestamp": datetime.utcnow().isoformat(),
            "ip_address": self._get_client_ip(),
            "user_agent": self._get_user_agent(),
            "details": details or {}
        }
        
        if success:
            logger.info(f"User action: {action}", extra={"audit": log_data})
        else:
            logger.warning(f"Failed user action: {action}", extra={"audit": log_data})
    
    def log_error_with_context(self, error_type: str, message: str, 
                              user_id: Optional[str] = None, 
                              extra_context: Optional[Dict] = None):
        """Log error with comprehensive context"""
        logger = self.get_logger("system")
        
        # Get current stack trace
        stack = traceback.extract_stack()
        relevant_stack = []
        for frame in stack[-5:]:  # Last 5 frames
            relevant_stack.append({
                "file": frame.filename,
                "line": frame.lineno,
                "function": frame.name
            })
        
        error_data = {
            "error_type": error_type,
            "message": message,
            "user_id": user_id,
            "timestamp": datetime.utcnow().isoformat(),
            "stack_trace": relevant_stack,
            "context": extra_context or {}
        }
        
        logger.error(f"{error_type}: {message}", extra={"error": error_data})
    
    def log_database_query(self, query_type: str, collection: str, 
                          duration: float, success: bool = True,
                          details: Optional[Dict] = None):
        """Log database queries for performance monitoring"""
        logger = self.get_logger("database")
        log_data = {
            "query_type": query_type,
            "collection": collection,
            "duration_ms": duration * 1000,
            "success": success,
            "timestamp": datetime.utcnow().isoformat(),
            "details": details or {}
        }
        
        if duration > 1.0:  # Slow query warning
            logger.warning(f"Slow database query: {query_type} on {collection}", 
                         extra={"query": log_data})
        else:
            logger.debug(f"Database query: {query_type} on {collection}", 
                        extra={"query": log_data})
    
    def _get_client_ip(self) -> Optional[str]:
        """Get client IP address (placeholder for web framework integration)"""
        # This would be implemented based on your web framework
        # For Streamlit, you might need a different approach
        return None
    
    def _get_user_agent(self) -> Optional[str]:
        """Get user agent (placeholder for web framework integration)"""
        # This would be implemented based on your web framework
        return None
    
    def cleanup_old_logs(self, days_to_keep: int = 30):
        """Clean up log files older than specified days"""
        log_dir = Path("logs")
        if not log_dir.exists():
            return
        
        cutoff_time = datetime.now().timestamp() - (days_to_keep * 24 * 3600)
        
        for log_file in log_dir.iterdir():
            if log_file.is_file() and log_file.stat().st_mtime < cutoff_time:
                try:
                    log_file.unlink()
                    self.get_logger("system").info(f"Cleaned up old log file: {log_file.name}")
                except Exception as e:
                    self.get_logger("system").error(f"Failed to cleanup log file {log_file.name}: {e}")

# Global logger instance
app_logger = ApplicationLogger("IntelligentBookSummarizer")

# Convenience functions
def get_logger(module: str) -> logging.Logger:
    """Get logger for a module (convenience function)"""
    return app_logger.get_logger(module)

def log_operation(operation: str, duration: float, **kwargs):
    """Log operation (convenience function)"""
    app_logger.log_operation(operation, duration, **kwargs)

def log_user_action(action: str, **kwargs):
    """Log user action (convenience function)"""
    app_logger.log_user_action(action, **kwargs)