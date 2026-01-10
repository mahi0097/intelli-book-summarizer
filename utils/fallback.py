# utils/fallback.py
import random
import re
from typing import Optional, List, Dict, Any
from utils.error_handler import ModelError, error_handler, log_operation

class SummaryFallback:
    """Fallback mechanisms for when AI model fails"""
    
    @staticmethod
    @error_handler
    @log_operation("extractive_fallback_summary")
    def extractive_fallback(text: str, target_length: str = "medium") -> str:
        """
        Simple extractive summarization fallback
        Returns first few sentences when AI model fails
        """
        if not text or len(text.strip()) < 100:
            return text or "Text is too short for summarization."
        
        # Split into sentences (improved approach)
        sentences = re.split(r'[.!?]+', text)
        sentences = [s.strip() for s in sentences if s.strip()]
        
        if not sentences:
            return "Unable to generate summary from the provided text."
        
        # Determine number of sentences based on target length
        length_map = {
            "short": 3,
            "medium": 5,
            "long": 8
        }
        
        num_sentences = length_map.get(target_length, 3)
        num_sentences = min(num_sentences, len(sentences))
        
        # Take first N sentences (simple extractive method)
        summary = '. '.join(sentences[:num_sentences]) + '.'
        
        # Add fallback notice
        summary += "\n\n*[Generated using fallback method - AI model unavailable]*"
        
        return summary
    
    @staticmethod
    @error_handler
    @log_operation("key_points_fallback")
    def key_points_fallback(text: str, num_points: int = 5) -> List[str]:
        """Extract key points as bullet list"""
        sentences = re.split(r'[.!?]+', text)
        sentences = [s.strip() for s in sentences if s.strip()]
        
        if len(sentences) < 3:
            return ["• " + (text[:200] + "..." if len(text) > 200 else text)]
        
        # Simple heuristic: take longer sentences (likely more important)
        scored_sentences = []
        for sentence in sentences:
            word_count = len(sentence.split())
            if word_count >= 5:  # At least 5 words
                scored_sentences.append((sentence, word_count))
        
        # Sort by length (descending)
        scored_sentences.sort(key=lambda x: x[1], reverse=True)
        
        # Take top N
        key_points = [f"• {s[0]}." for s in scored_sentences[:num_points]]
        
        if not key_points:
            key_points = [f"• {sentences[0]}."]
        
        # Add fallback notice
        key_points.append("\n*[Generated using fallback method]*")
        
        return key_points
    
    @staticmethod
    def get_troubleshooting_suggestions(error_type: str) -> List[str]:
        """Get user-friendly troubleshooting suggestions"""
        suggestions = {
            "text_too_long": [
                "Try splitting your text into smaller sections (under 10,000 words)",
                "Upload as a file instead of pasting text",
                "Focus on one chapter at a time"
            ],
            "processing_timeout": [
                "Try with a shorter text",
                "Use 'Short' summary length instead of 'Long'",
                "Check your internet connection and try again",
                "Wait a few minutes and retry"
            ],
            "model_error": [
                "Try again in a few moments",
                "Use different summary settings",
                "Simplify the text if possible",
                "Check if the text contains special characters or formatting issues"
            ],
            "file_error": [
                "Make sure the file is not corrupted",
                "Try converting to PDF or TXT format",
                "Check if the file is password protected",
                "Reduce the file size (max 10MB)"
            ],
            "rate_limit": [
                "Wait a few minutes before trying again",
                "You've reached the rate limit for now",
                "Try again in 5-10 minutes"
            ],
            "authentication": [
                "Check your email and password",
                "Reset your password if needed",
                "Make sure your account is active"
            ],
            "database": [
                "Try refreshing the page",
                "Wait a moment and try again",
                "Contact support if problem persists"
            ]
        }
        
        return suggestions.get(error_type, [
            "Try again in a few moments",
            "Check your input and try again",
            "Refresh the page",
            "Contact support if problem persists"
        ])

class GracefulDegradation:
    """Implement graceful degradation for non-critical features"""
    
    @staticmethod
    def with_fallback(main_func, fallback_func, fallback_message: str = None):
        """Execute main function with fallback if it fails"""
        from utils.error_handler import error_handler, ErrorLogger
        
        @error_handler
        def wrapper(*args, **kwargs):
            try:
                return main_func(*args, **kwargs)
            except Exception as e:
                ErrorLogger.log_error(
                    "fallback_triggered",
                    f"Main function failed, using fallback: {str(e)}",
                    extra_data={
                        "main_func": main_func.__name__,
                        "fallback_func": fallback_func.__name__
                    }
                )
                
                if fallback_message:
                    ErrorLogger.log_user_action(
                        "fallback_used",
                        details={
                            "reason": str(e), 
                            "fallback": fallback_func.__name__,
                            "message": fallback_message
                        }
                    )
                
                return fallback_func(*args, **kwargs)
        return wrapper
    
    @staticmethod
    def get_simplified_options():
        """Get simplified options when complex features fail"""
        return {
            "length": "medium",  # Most reliable
            "style": "paragraph",  # Most reliable
            "simplify": True,
            "max_tokens": 500
        }