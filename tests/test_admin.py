# test_admin.py
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from utils.database import create_user, get_db

print("=" * 50)
print("🛠️ CREATING ADMIN USER FOR TESTING")
print("=" * 50)

# Create admin user
admin_email = "admin@test.com"
admin_password = "admin123"

# Check if admin already exists
db = get_db()
existing_admin = db.users.find_one({"email": admin_email})
if existing_admin:
    print(f"⚠️ Admin user '{admin_email}' already exists")
    print(f"   Role: {existing_admin.get('role', 'unknown')}")
    print(f"   ID: {existing_admin.get('_id')}")
else:
    # Create new admin user
    admin_id = create_user(
        name="Test Administrator",
        email=admin_email,
        password=admin_password,
        role="admin"  # This is crucial!
    )
    print(f"✅ Created admin user:")
    print(f"   Email: {admin_email}")
    print(f"   Password: {admin_password}")
    print(f"   Role: admin")
    print(f"   ID: {admin_id}")

print("\n" + "=" * 50)
print("📊 DATABASE STATUS CHECK")
print("=" * 50)

# Check all users
all_users = list(db.users.find({}))
print(f"Total users in database: {len(all_users)}")
print("\nUser list:")
for user in all_users:
    role = user.get('role', 'user')
    status = "👑 ADMIN" if role == "admin" else "👤 USER"
    print(f"  {status} - {user.get('email')} (Role: {role})")

print("\n" + "=" * 50)
print("🚀 READY TO TEST ADMIN PANEL")
print("=" * 50)
print("\nTo test admin panel:")
print("1. Start your app: streamlit run app.py")
print("2. Login with:")
print(f"   📧 Email: {admin_email}")
print(f"   🔑 Password: {admin_password}")
print("3. Look for '👑 Admin' or 'Admin Dashboard' in the navigation")
print("\nIf you don't see admin options, check:")
print("   • Your app.py has admin navigation")
print("   • User role is 'admin' (not 'user')")
print("   • Look for page='admin_dashboard' in URL")