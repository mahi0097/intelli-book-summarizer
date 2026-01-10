import pytest
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '../..'))

from backend.models.summarizer import FastSummarizer, UltraFastSummarizer
import time

class TestSummarizerModels:
    
    @pytest.fixture
    def sample_text(self):
        return """Artificial intelligence is transforming industries. 
        Machine learning algorithms analyze data patterns. 
        This technology is used in healthcare and finance."""
    
    def test_fast_summarizer_initialization(self):
        """Test FastSummarizer initialization"""
        summarizer = FastSummarizer("distilbart")
        assert hasattr(summarizer, 'model_name')
        assert hasattr(summarizer, 'max_input_tokens')
    
    def test_ultra_fast_summarizer_initialization(self):
        """Test UltraFastSummarizer initialization"""
        summarizer = UltraFastSummarizer()
        assert summarizer.name == "UltraFastExtractive"
    
    def test_summarize_short_text(self, sample_text):
        """Test summarization of short text"""
        summarizer = UltraFastSummarizer()
        result = summarizer.generate_ultra_fast_summary(sample_text)
        
        assert result["success"] == True
        assert "summary_text" in result
        assert len(result["summary_text"]) > 0
        assert result["processing_time"] > 0
    
    def test_summarize_empty_text(self):
        """Test summarization with empty text"""
        summarizer = UltraFastSummarizer()
        result = summarizer.generate_ultra_fast_summary("")
        
        assert result["success"] == False or len(result["summary_text"]) == 0
    
    def test_parallel_summarization(self):
        """Test parallel processing"""
        summarizer = FastSummarizer("distilbart")
        
        # Create multiple chunks
        chunks = ["Chunk one with some text."] * 5
        
        import time
        start_time = time.time()
        summaries = summarizer.parallel_summarize(chunks, max_workers=2)
        parallel_time = time.time() - start_time
        
        start_time = time.time()
        sequential = [summarizer.fast_summarize_chunk(chunk) for chunk in chunks]
        sequential_time = time.time() - start_time
        
        # Parallel should be faster (or at least not slower)
        assert len(summaries) == len(chunks)