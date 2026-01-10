# create_admin.py - Save in project root (same folder as utils)
import sys
import os

# Add current directory to Python path
sys.path.insert(0, os.getcwd())

from utils.database import create_user, get_db, get_user_by_email

print("=" * 50)
print("👑 ADMIN USER CREATION TOOL")
print("=" * 50)

def create_admin_account():
    """Create or update admin user"""
    
    # Admin credentials
    ADMIN_EMAIL = "admin@booksummarizer.com"
    ADMIN_PASSWORD = "Admin@123"  # Strong password
    ADMIN_NAME = "System Administrator"
    
    print(f"\n📧 Email: {ADMIN_EMAIL}")
    print(f"🔑 Password: {ADMIN_PASSWORD}")
    print(f"👤 Name: {ADMIN_NAME}")
    print(f"👑 Role: admin")
    
    # Check if user already exists
    existing_user = get_user_by_email(ADMIN_EMAIL)
    
    if existing_user:
        print(f"\n⚠️ User '{ADMIN_EMAIL}' already exists!")
        print(f"   Current role: {existing_user.get('role', 'user')}")
        
        # Update to admin if not already
        if existing_user.get('role') != 'admin':
            db = get_db()
            db.users.update_one(
                {"email": ADMIN_EMAIL},
                {"$set": {"role": "admin"}}
            )
            print("✅ Updated user role to 'admin'")
        else:
            print("✅ User is already an admin")
    else:
        # Create new admin user
        try:
            user_id = create_user(
                name=ADMIN_NAME,
                email=ADMIN_EMAIL,
                password=ADMIN_PASSWORD,
                role="admin"  # This is crucial!
            )
            print(f"\n✅ Admin user created successfully!")
            print(f"   User ID: {user_id}")
        except Exception as e:
            print(f"\n❌ Error creating admin: {e}")
    
    # Verify the admin user
    print("\n" + "=" * 50)
    print("🔍 VERIFICATION")
    print("=" * 50)
    
    db = get_db()
    admin_users = list(db.users.find({"role": "admin"}))
    
    if admin_users:
        print(f"\n✅ Found {len(admin_users)} admin user(s):")
        for admin in admin_users:
            print(f"\n   👑 Admin:")
            print(f"   • Email: {admin.get('email')}")
            print(f"   • Name: {admin.get('name', 'Unknown')}")
            print(f"   • Role: {admin.get('role', 'user')}")
            print(f"   • Created: {admin.get('created_at', 'Unknown')}")
    else:
        print("\n❌ No admin users found in database!")
    
    print("\n" + "=" * 50)
    print("🚀 READY TO LOGIN")
    print("=" * 50)
    print("\nTo access admin panel:")
    print(f"1. Start app: streamlit run app.py")
    print(f"2. Login with:")
    print(f"   📧 Email: {ADMIN_EMAIL}")
    print(f"   🔑 Password: {ADMIN_PASSWORD}")
    print(f"3. Look for '👑 Admin Dashboard' in sidebar")
    print(f"\n📌 Note: Make sure frontend/admin_dashboard.py exists!")

if __name__ == "__main__":
    create_admin_account()