# test_admin_access.py
import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), ".")))

from utils.database import db
from backend.auth import login_user
import streamlit as st

def test_admin_access():
    print("🔍 Testing Admin Access Setup")
    print("=" * 60)
    
    # 1. Check if admin users exist
    admins = list(db.users.find({"role": "admin"}))
    print(f"1. Admin users found: {len(admins)}")
    for admin in admins:
        print(f"   - {admin.get('email')} ({admin.get('name')})")
    
    if not admins:
        print("❌ No admin users. Create one with: python create_admin_user.py")
        return
    
    # 2. Test login with first admin
    admin_email = admins[0].get('email')
    test_password = "Admin123!"  # Change if you used different password
    
    print(f"\n2. Testing login for: {admin_email}")
    
    # Test login using the current auth API
    result = login_user(admin_email, test_password)
    
    if result["success"]:
        print(f"   ✅ Login successful!")
        print(f"   User role: {result['user'].get('role')}")
        print(f"   Is admin? {result['user'].get('role') == 'admin'}")
        
        # 3. Test if admin_dashboard_page would allow access
        user = result['user']
        if user.get('role') == 'admin':
            print("\n3. ✅ Admin access verified!")
            print("   You can access admin dashboard")
        else:
            print("\n3. ❌ User is not admin despite admin role in DB")
            print("   Check login_user() function in backend/auth.py")
    else:
        print(f"   ❌ Login failed: {result.get('message')}")
        print("\n   Try creating admin with: python create_admin_user.py")
    
    print("\n" + "=" * 60)
    print("🚀 To access admin dashboard:")
    print("1. Start your app: streamlit run app.py")
    print("2. Login with admin credentials")
    print("3. Look for '🛡 Admin Dashboard' in sidebar")
    print("4. Click it to access admin dashboard")

if __name__ == "__main__":
    test_admin_access()
