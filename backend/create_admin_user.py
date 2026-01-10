# create_admin_user.py
import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), ".")))

from utils.database import db
import bcrypt
from datetime import datetime

def create_admin_user():
    """Create an admin user in the database"""
    print("👑 Creating Admin User")
    print("=" * 50)
    
    # Admin credentials
    admin_email = "admin@booksummarizer.com"
    admin_password = "Admin123!"  # Change this in production!
    admin_name = "System Administrator"
    
    # Check if admin already exists
    existing = db.users.find_one({"email": admin_email.lower()})
    if existing:
        print(f"⚠️ Admin user already exists:")
        print(f"   Email: {existing.get('email')}")
        print(f"   Name: {existing.get('name')}")
        print(f"   Role: {existing.get('role', 'user')}")
        
        # Check if they're admin
        if existing.get('role') == 'admin':
            print("✅ User is already an admin")
        else:
            print("⚠️ User exists but is not admin")
            # Ask to promote
            response = input("Promote to admin? (y/n): ")
            if response.lower() == 'y':
                db.users.update_one(
                    {"_id": existing["_id"]},
                    {"$set": {"role": "admin", "updated_at": datetime.utcnow()}}
                )
                print("✅ User promoted to admin!")
        return
    
    # Hash the password
    password_hash = bcrypt.hashpw(admin_password.encode(), bcrypt.gensalt()).decode()
    
    # Create admin user document
    admin_user = {
        "name": admin_name,
        "email": admin_email.lower(),
        "password_hash": password_hash,
        "role": "admin",
        "created_at": datetime.utcnow(),
        "updated_at": datetime.utcnow()
    }
    
    # Insert into database
    result = db.users.insert_one(admin_user)
    
    if result.inserted_id:
        print(f"✅ Admin user created successfully!")
        print(f"   Email: {admin_email}")
        print(f"   Password: {admin_password}")
        print(f"   User ID: {result.inserted_id}")
        print("\n⚠️ IMPORTANT: Change the password immediately!")
        print("   You can login with these credentials.")
    else:
        print("❌ Failed to create admin user")

def list_admin_users():
    """List all admin users in the system"""
    print("\n👥 Existing Admin Users:")
    print("=" * 50)
    
    admins = list(db.users.find({"role": "admin"}))
    
    if not admins:
        print("❌ No admin users found")
        return
    
    for i, admin in enumerate(admins, 1):
        print(f"{i}. {admin.get('name')} ({admin.get('email')})")
        print(f"   ID: {admin.get('_id')}")
        print(f"   Created: {admin.get('created_at')}")
        print()

if __name__ == "__main__":
    create_admin_user()
    list_admin_users()