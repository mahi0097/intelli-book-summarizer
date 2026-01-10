import pytest
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '../..'))

from backend.preprocessing import preprocess_for_summarization

class TestPreprocessing:
    
    def test_preprocess_empty_text(self):
        """Test preprocessing with empty text"""
        result = preprocess_for_summarization("", chunk_size=500)
        assert result["success"] == False
        assert "error" in result
    
    def test_preprocess_short_text(self):
        """Test preprocessing with short text"""
        text = "This is a short text."
        result = preprocess_for_summarization(text, chunk_size=500)
        assert result["success"] == True
        assert len(result["chunks"]) == 1
        assert result["chunks"][0] == text
    
    def test_preprocess_long_text_chunking(self):
        """Test chunking of long text"""
        # Create a long text
        text = " ".join(["Sentence " + str(i) for i in range(1000)])
        result = preprocess_for_summarization(text, chunk_size=300)
        assert result["success"] == True
        assert len(result["chunks"]) > 1
        
        # Check chunk sizes
        for chunk in result["chunks"]:
            words = len(chunk.split())
            assert words <= 350  # Some buffer allowed
    
    def test_preprocess_with_special_characters(self):
        """Test text with special characters"""
        text = "Text with special chars: ©®™€£¥•…—±×÷≠≈∞"
        result = preprocess_for_summarization(text, chunk_size=500)
        assert result["success"] == True
        assert "©®™€£¥•…—±×÷≠≈∞" in result["chunks"][0]
    
    def test_preprocess_preserves_paragraphs(self):
        """Test that paragraphs are preserved"""
        text = """First paragraph.
        
Second paragraph with more content.
        
Third paragraph."""
        
        result = preprocess_for_summarization(text, chunk_size=100)
        assert result["success"] == True
        # Should preserve paragraph breaks
        assert "\n\n" in result["chunks"][0]