# backend/admin_auth.py - CORRECTED
from functools import wraps
from flask import request, jsonify
from bson import ObjectId
from utils.database import db

def admin_required(f):
    """Decorator to require admin privileges"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # Get user from session or token
        user_id = request.headers.get('X-User-ID')
        auth_token = request.headers.get('Authorization')
        
        if not user_id:
            return jsonify({"error": "User ID required"}), 401
        
        # Check if user exists and is admin
        try:
            user = db.users.find_one({"_id": ObjectId(user_id)})
        except:
            return jsonify({"error": "Invalid user ID format"}), 400
        
        if not user:
            return jsonify({"error": "User not found"}), 404
        
        if user.get("role") != "admin":
            return jsonify({"error": "Admin privileges required"}), 403
        
        return f(*args, **kwargs)
    return decorated_function

def get_admin_user():
    """Get current admin user from request"""
    user_id = request.headers.get('X-User-ID')
    if user_id:
        try:
            return db.users.find_one({"_id": ObjectId(user_id), "role": "admin"})
        except:
            return None
    return None