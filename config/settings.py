# config/settings.py - UPDATED VERSION
import os
from pathlib import Path
from typing import Dict, Any

# Base paths
BASE_DIR = Path(__file__).parent.parent
LOG_DIR = BASE_DIR / "logs"
UPLOAD_DIR = BASE_DIR / "uploads"
TEMP_DIR = BASE_DIR / "temp"
EXPORT_DIR = BASE_DIR / "exports"
CACHE_DIR = BASE_DIR / ".cache"

# Create directories
for directory in [LOG_DIR, UPLOAD_DIR, TEMP_DIR, EXPORT_DIR, CACHE_DIR]:
    directory.mkdir(exist_ok=True)

# Application settings
APP_CONFIG: Dict[str, Any] = {
    # Basic app info
    "APP_NAME": "Intelligent Book Summarizer Pro",
    "APP_VERSION": "2.0.0",
    "DEBUG": os.getenv("DEBUG", "False").lower() == "true",
    
    # File upload settings - CONSISTENT WITH UPLOAD.PY
    "MAX_FILE_SIZE": 10 * 1024 * 1024,  # 10MB (MATCHES UPLOAD.PY)
    "ALLOWED_EXTENSIONS": ['.pdf', '.txt', '.docx', '.doc', '.rtf', '.epub'],
    "UPLOAD_DIR": str(UPLOAD_DIR),
    
    # Text processing settings
    "MAX_TEXT_LENGTH": 1000000,  # 1 million characters
    "MIN_TEXT_LENGTH": 100,
    "DEFAULT_SUMMARY_LENGTH": "medium",
    "SUMMARY_LENGTH_OPTIONS": ["short", "medium", "long"],
    "SUMMARY_STYLE_OPTIONS": ["paragraph", "bullets", "detailed", "concise"],
    
    # Rate limiting settings
    "RATE_LIMITS": {
        "upload": {"max_requests": 10, "time_window": 300, "strategy": "sliding_window"},
        "summary": {"max_requests": 20, "time_window": 300, "strategy": "token_bucket"},
        "api": {"max_requests": 100, "time_window": 3600, "strategy": "sliding_window"},
        "login": {"max_requests": 5, "time_window": 300, "strategy": "fixed_window"},
        "export": {"max_requests": 5, "time_window": 60, "strategy": "sliding_window"},
    },
    
    # Security settings
    "SESSION_TIMEOUT": 28800,  # 8 hours in seconds
    "PASSWORD_MIN_LENGTH": 8,
    "PASSWORD_REQUIREMENTS": {
        "min_length": 8,
        "require_uppercase": True,
        "require_lowercase": True,
        "require_numbers": True,
        "require_special": False,
    },
    
    # Model and processing settings
    "ENABLE_FALLBACK": True,
    "MODEL_TIMEOUT": 30,  # seconds
    "MAX_PROCESSING_TIME": 120,  # seconds
    "CHUNK_SIZE": 4000,  # characters per chunk
    "OVERLAP_SIZE": 200,  # characters overlap between chunks
    
    # UI/UX settings
    "DEFAULT_THEME": "light",
    "ENABLE_DARK_MODE": True,
    "ANIMATION_DURATION": 300,  # milliseconds
    "TOOLTIP_DELAY": 500,  # milliseconds
    "AUTO_SAVE_INTERVAL": 30,  # seconds
    
    # Database settings
    "DB_RETRY_ATTEMPTS": 3,
    "DB_RETRY_DELAY": 1,  # seconds
    "DB_TIMEOUT": 10,  # seconds
    
    # Logging settings
    "LOG_LEVEL": "INFO",
    "LOG_ROTATION_SIZE": 10 * 1024 * 1024,  # 10MB
    "LOG_BACKUP_COUNT": 5,
    "LOG_RETENTION_DAYS": 30,
    
    # Export settings
    "EXPORT_FORMATS": ["txt", "pdf", "html", "json"],
    "MAX_EXPORT_SIZE": 5 * 1024 * 1024,  # 5MB
    
    # Cache settings
    "CACHE_TTL": 3600,  # 1 hour
    "CACHE_MAX_SIZE": 100 * 1024 * 1024,  # 100MB
}

# Environment-specific overrides
if os.getenv("ENVIRONMENT") == "production":
    APP_CONFIG.update({
        "DEBUG": False,
        "LOG_LEVEL": "WARNING",
        "MAX_FILE_SIZE": 5 * 1024 * 1024,  # 5MB for production
        "RATE_LIMITS": {
            "upload": {"max_requests": 5, "time_window": 300},
            "summary": {"max_requests": 10, "time_window": 300},
            "api": {"max_requests": 50, "time_window": 3600},
        }
    })
elif os.getenv("ENVIRONMENT") == "development":
    APP_CONFIG.update({
        "DEBUG": True,
        "LOG_LEVEL": "DEBUG",
        "MAX_FILE_SIZE": 20 * 1024 * 1024,  # 20MB for development
    })

# Helper functions
def get_setting(key: str, default: Any = None) -> Any:
    """Get a setting value with optional default"""
    return APP_CONFIG.get(key, default)

def update_settings(**kwargs):
    """Update settings dynamically"""
    APP_CONFIG.update(kwargs)

def validate_settings():
    """Validate all settings are valid"""
    # Check file size consistency
    if APP_CONFIG["MAX_FILE_SIZE"] != 10 * 1024 * 1024:
        print(f"⚠️ Warning: MAX_FILE_SIZE is {APP_CONFIG['MAX_FILE_SIZE']} bytes, but upload.py expects 10MB")
    
    # Check required directories exist
    required_dirs = [LOG_DIR, UPLOAD_DIR, TEMP_DIR]
    for directory in required_dirs:
        if not directory.exists():
            print(f"⚠️ Warning: Directory {directory} does not exist")
    
    return True

# Validate on import
if __name__ != "__main__":
    validate_settings()