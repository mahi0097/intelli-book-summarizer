import pytest
import sys
import os
import asyncio
sys.path.append(os.path.join(os.path.dirname(__file__), '../..'))

from backend.summary_orchestrator import generate_summary
from utils.database import create_book, create_user

class TestSummarizationIntegration:
    
    @pytest.fixture
    async def setup_test_book(self):
        """Setup test book for summarization"""
        # Create test user
        user_id = create_user(
            name="Integration Test User",
            email=f"integration_{datetime.now().timestamp()}@test.com",
            password="testpass"
        )
        
        # Create test book with substantial text
        book_text = """
        Artificial Intelligence: A Comprehensive Overview
        
        Artificial intelligence (AI) is intelligence demonstrated by machines, 
        as opposed to natural intelligence displayed by animals including humans. 
        Leading AI textbooks define the field as the study of "intelligent agents": 
        any system that perceives its environment and takes actions that maximize 
        its chance of achieving its goals.
        
        Machine learning is a subset of AI that enables computers to learn 
        and improve from experience without being explicitly programmed. 
        Deep learning is a subset of machine learning that uses neural networks 
        with multiple layers to analyze various factors of data.
        
        Applications of AI include advanced web search engines, 
        recommendation systems, understanding human speech, self-driving cars, 
        automated decision-making, and competing at the highest level 
        in strategic game systems.
        """
        
        book_id = create_book(
            user_id=user_id,
            title="AI Overview Book",
            author="Tech Writer",
            raw_text=book_text
        )
        
        return user_id, book_id, book_text
    
    @pytest.mark.asyncio
    async def test_complete_summarization_flow(self, setup_test_book):
        """Test complete summarization workflow"""
        user_id, book_id, original_text = await setup_test_book
        
        # Define summary options
        summary_options = {
            "length": "medium",
            "style": "paragraph",
            "tone": "academic"
        }
        
        # Generate summary
        result = await generate_summary(book_id, user_id, summary_options)
        
        # Verify results
        assert result["success"] == True
        assert "summary" in result
        assert len(result["summary"]) > 0
        
        # Check summary is shorter than original
        original_words = len(original_text.split())
        summary_words = len(result["summary"].split())
        
        assert summary_words < original_words
        assert summary_words > 10  # Should be meaningful
        
        # Check processing time
        assert "processing_time_sec" in result
        assert result["processing_time_sec"] > 0
        
        # Check stats
        assert "stats" in result
        assert "original_length" in result["stats"]
        assert "summary_length" in result["stats"]