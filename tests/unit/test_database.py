import pytest
import sys
import os
from bson import ObjectId
from datetime import datetime
sys.path.append(os.path.join(os.path.dirname(__file__), '../..'))

from utils.database import (
    create_user, get_user_by_email, 
    create_book, get_book_by_id,
    save_summary_with_metadata, get_book_summary_versions
)

class TestDatabaseOperations:
    
    @pytest.fixture
    def test_user_data(self):
        return {
            "name": "Test User",
            "email": f"test_{datetime.now().timestamp()}@test.com",
            "password": "testpassword123"
        }
    
    @pytest.fixture
    def test_book_data(self):
        return {
            "title": "Test Book",
            "author": "Test Author",
            "chapter": "Chapter 1",
            "raw_text": "This is test book content for database testing."
        }
    
    def test_create_and_retrieve_user(self, test_user_data):
        """Test user creation and retrieval"""
        # Create user
        user_id = create_user(
            name=test_user_data["name"],
            email=test_user_data["email"],
            password=test_user_data["password"]
        )
        
        assert user_id is not None
        
        # Retrieve user
        user = get_user_by_email(test_user_data["email"])
        assert user is not None
        assert user["email"] == test_user_data["email"]
        assert user["name"] == test_user_data["name"]
    
    def test_create_book(self, test_user_data, test_book_data):
        """Test book creation"""
        # First create a user
        user_id = create_user(
            name=test_user_data["name"],
            email=test_user_data["email"],
            password=test_user_data["password"]
        )
        
        # Create book
        book_id = create_book(
            user_id=user_id,
            title=test_book_data["title"],
            author=test_book_data["author"],
            chapter=test_book_data["chapter"],
            raw_text=test_book_data["raw_text"]
        )
        
        assert book_id is not None
        
        # Retrieve book
        book = get_book_by_id(book_id)
        assert book is not None
        assert book["title"] == test_book_data["title"]
        assert book["author"] == test_book_data["author"]
    
    def test_save_summary_with_metadata(self, test_user_data):
        """Test saving summary with version control"""
        # Create user
        user_id = create_user(
            name=test_user_data["name"],
            email=test_user_data["email"],
            password=test_user_data["password"]
        )
        
        # Create book
        book_id = create_book(
            user_id=user_id,
            title="Test Book for Summary",
            author="Test Author",
            raw_text="Sample book text"
        )
        
        # Save first version
        summary1_id = save_summary_with_metadata(
            book_id=book_id,
            user_id=user_id,
            summary_text="First version of summary",
            summary_options={"length": "medium", "style": "paragraph"},
            version=1
        )
        
        # Save second version
        summary2_id = save_summary_with_metadata(
            book_id=book_id,
            user_id=user_id,
            summary_text="Second version of summary",
            summary_options={"length": "short", "style": "bullets"},
            version=2
        )
        
        # Get versions
        versions = get_book_summary_versions(book_id, user_id)
        assert len(versions) == 2
        assert versions[0]["version"] == 1
        assert versions[1]["version"] == 2