# create_admin.py
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from utils.database import create_user, get_db

print("👑 Creating admin user...")

# Create admin user
admin_id = create_user(
    name="System Administrator",
    email="admin@test.com",  # You can change this
    password="admin123",     # You can change this
    role="admin"
)

print(f"✅ Admin user created!")
print(f"📧 Email: admin@test.com")
print(f"🔑 Password: admin123")
print(f"🆔 User ID: {admin_id}")

# Verify it was created
db = get_db()
user = db.users.find_one({"email": "admin@test.com"})
if user:
    print(f"✅ Verified in database. Role: {user.get('role')}")
else:
    print("❌ User not found in database")