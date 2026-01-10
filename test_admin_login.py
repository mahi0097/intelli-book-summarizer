# test_admin_login.py
import sys
import os
sys.path.insert(0, os.getcwd())

from utils.database import get_user_by_email, verify_password

def test_admin_login():
    """Test admin login credentials"""
    
    # Test credentials
    TEST_CREDENTIALS = [
        ("admin@booksummarizer.com", "Admin@123"),
        ("admin@test.com", "admin123"),
        ("admin@example.com", "password"),
    ]
    
    print("=" * 50)
    print("🔐 ADMIN LOGIN TEST")
    print("=" * 50)
    
    for email, password in TEST_CREDENTIALS:
        print(f"\nTrying: {email}")
        
        user = get_user_by_email(email)
        
        if user:
            print(f"✅ User found: {user.get('name')}")
            print(f"   Role: {user.get('role', 'user')}")
            print(f"   Active: {user.get('is_active', True)}")
            
            # Test password
            if verify_password(user['password_hash'], password):
                print(f"✅ Password CORRECT!")
                print(f"   👑 ADMIN LOGIN SUCCESSFUL!")
                print(f"\n📌 Login with:")
                print(f"   Email: {email}")
                print(f"   Password: {password}")
                return True
            else:
                print(f"❌ Password incorrect")
        else:
            print(f"❌ User not found")
    
    print("\n" + "=" * 50)
    print("❌ No valid admin credentials found!")
    print("=" * 50)
    print("\nRun: python create_admin.py")
    return False

if __name__ == "__main__":
    test_admin_login()