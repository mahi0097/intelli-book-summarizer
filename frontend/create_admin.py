# frontend/create_admin.py

import sys
import os
from datetime import datetime

# ✅ Add project root to PYTHONPATH
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(PROJECT_ROOT)

from utils.database import get_db

def create_default_admin():
    db = get_db()

    admin_email = "admin@example.com"

    # Check if admin already exists
    existing_admin = db.users.find_one({"email": admin_email})
    if existing_admin:
        print("⚠️ Admin already exists")
        return

    db.users.insert_one({
        "name": "Admin",
        "email": admin_email,
        "password": "admin123",  # ⚠️ hash in real app
        "role": "admin",
        "is_active": True,
        "created_at": datetime.now()
    })

    print("✅ Default admin created successfully")

if __name__ == "__main__":
    create_default_admin()
