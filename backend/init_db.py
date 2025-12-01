# backend/init_db.py

from utils.database import create_indexes

if __name__ == "__main__":
    print("Creating indexes...")
    create_indexes()
    print("Indexes created successfully!")
