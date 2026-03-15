import pytest
import sys
import os
import tempfile
sys.path.append(os.path.join(os.path.dirname(__file__), '../..'))

from backend.text_extractor import process_book
from utils.database import create_book, update_book_status, get_book_by_id

class TestUploadIntegration:
    
    def test_complete_upload_flow_txt(self):
        """Test complete upload flow for TXT file"""
        # Create test TXT file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
            f.write("""Chapter 1: The Beginning
            
This is a test book for integration testing.
It contains multiple paragraphs and sentences.
            
The purpose is to test the complete upload flow.""")
            temp_file = f.name
        
        try:
            # Create book entry
            user_id = "test_user_123"
            book_id = create_book(
                user_id=user_id,
                title="Test Integration Book",
                author="Test Author",
                file_path=temp_file,
                raw_text=""
            )
            
            # Update status
            update_book_status(book_id, "extracting")
            
            # Process book
            result = process_book(book_id, temp_file)
            
            # Verify results
            assert result["success"] == True
            assert "extraction" in result
            assert result["extraction"]["word_count"] > 0
            
            # Check database update
            book = get_book_by_id(book_id)
            assert book["status"] == "text_extracted"
            assert book["word_count"] > 0
            
        finally:
            # Cleanup
            os.unlink(temp_file)
    
    def test_upload_failed_flow(self):
        """Test upload flow with invalid file"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.invalid', delete=False) as f:
            f.write("Invalid content")
            temp_file = f.name
        
        try:
            user_id = "test_user_123"
            book_id = create_book(
                user_id=user_id,
                title="Invalid Book",
                author="Test",
                file_path=temp_file,
                raw_text=""
            )
            
            result = process_book(book_id, temp_file)
            
            # Should fail
            assert result["success"] == False
            assert "error" in result
            
            book = get_book_by_id(book_id)
            assert book["status"] in ["extraction_failed", "failed"]
            
        finally:
            os.unlink(temp_file)