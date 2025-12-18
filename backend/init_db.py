# backend/init_db.py

from utils.database import create_indexes
import re
import time
import logging
from datetime import datetime,timedate
import bcrypt
from pymongo.errors import DuplicateKeyError, PyMongoError
from bson import ObjectId



    
if __name__ == "__main__":
    print("Creating indexes...")
    create_indexes()
    print("Indexes created successfully!")
