# backend/auth.py - COMPLETE UPDATED VERSION
import os
import re
import bcrypt
import jwt
from datetime import datetime, timedelta
from bson import ObjectId

# =========================
# JWT CONFIG
# =========================
SECRET_KEY = os.getenv("JWT_SECRET", "change-this-secret-in-production")
JWT_ALGORITHM = "HS256"
JWT_EXPIRATION_HOURS = 24


# =========================
# PASSWORD HELPERS
# =========================
def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()


def verify_password(password: str, hashed_password: str) -> bool:
    return bcrypt.checkpw(password.encode(), hashed_password.encode())


# =========================
# JWT HELPERS
# =========================
def create_token(user_id, email, role="user"):
    payload = {
        "user_id": str(user_id),
        "email": email,
        "role": role,
        "exp": datetime.utcnow() + timedelta(hours=JWT_EXPIRATION_HOURS)
    }
    return jwt.encode(payload, SECRET_KEY, algorithm=JWT_ALGORITHM)


def verify_token(token):
    try:
        return jwt.decode(token, SECRET_KEY, algorithms=[JWT_ALGORITHM])
    except jwt.ExpiredSignatureError:
        return None
    except jwt.InvalidTokenError:
        return None


# =========================
# VALIDATION
# =========================
def is_valid_email(email):
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(pattern, email) is not None


# =========================
# REGISTER USER
# =========================
def register_user(name, email, password, role="user"):
    from utils.database import db, create_user

    if not is_valid_email(email):
        return {
            "success": False,
            "message": "Invalid email format"
        }

    if db.users.find_one({"email": email.lower()}):
        return {
            "success": False,
            "message": "Email already registered"
        }

    try:
        user_id = create_user(name, email, password, role)
        return {
            "success": True,
            "user_id": str(user_id)
        }
    except Exception as e:
        return {
            "success": False,
            "message": str(e)
        }


# =========================
# LOGIN USER
# =========================
def login_user(email, password):
    from utils.database import get_user_by_email

    user = get_user_by_email(email)

    if not user:
        return {
            "success": False,
            "message": "Invalid email or password"
        }

    if not verify_password(password, user["password_hash"]):
        return {
            "success": False,
            "message": "Invalid email or password"
        }

    token = create_token(user["_id"], user["email"], user.get("role", "user"))

    return {
        "success": True,
        "user": {
            "user_id": str(user["_id"]),
            "id": str(user["_id"]),  # Added for compatibility
            "name": user.get("name", user["email"].split("@")[0]),
            "email": user["email"],
            "role": user.get("role", "user"),
            "token": token
        }
    }


# =========================
# SESSION HELPERS (STREAMLIT)
# =========================
def set_user_session(session, user):
    session["logged_in"] = True
    session["user_id"] = user["user_id"]
    session["username"] = user["email"]
    session["role"] = user.get("role", "user")
    session["token"] = user.get("token")
    session["last_activity"] = datetime.utcnow()


def clear_user_session(session):
    session.clear()
    session["logged_in"] = False


# =========================
# NEW FUNCTIONS FOR APP.PY COMPATIBILITY
# =========================
def get_current_user(session_state):
    """
    Get current user from session state
    Used by app.py
    """
    if not session_state.get("logged_in", False):
        return None
    
    try:
        from utils.database import get_user_by_id
        
        user_id = session_state.get("user_id")
        if not user_id:
            return None
        
        user = get_user_by_id(user_id)
        if user:
            # Ensure all required fields
            user['_id'] = str(user.get('_id', ''))
            user['id'] = user['_id']  # Add 'id' field for compatibility
            user['name'] = user.get('name', 'User')
            user['email'] = user.get('email', '')
            user['role'] = user.get('role', 'user')
            return user
        
        return None
    except Exception as e:
        print(f"Error getting current user: {e}")
        return None


def is_logged_in(session_state):
    """
    Check if user is logged in
    Used by app.py
    """
    # Basic check
    if not session_state.get("logged_in", False):
        return False
    
    # Check if user_id exists
    if not session_state.get("user_id"):
        return False
    
    # Optional: Check session timeout
    last_activity = session_state.get("last_activity")
    if last_activity:
        time_diff = (datetime.utcnow() - last_activity).total_seconds()
        if time_diff > 8 * 3600:  # 8 hours timeout
            # Clear session
            for key in ["logged_in", "user_id", "username", "role", "token", "last_activity"]:
                if key in session_state:
                    session_state[key] = None
            return False
    
    return True


# =========================
# TOKEN VERIFICATION
# =========================
def verify_user_token(token):
    """
    Verify JWT token and extract user info
    """
    try:
        decoded = verify_token(token)
        if decoded:
            return {
                "user_id": decoded.get("user_id"),
                "email": decoded.get("email"),
                "role": decoded.get("role", "user")
            }
        return None
    except Exception as e:
        print(f"Token verification error: {e}")
        return None


# =========================
# ADMIN CHECK
# =========================
def is_admin(session_state):
    """
    Check if current user is admin
    """
    user = get_current_user(session_state)
    return user and user.get("role") == "admin"


# =========================
# USER MANAGEMENT
# =========================
def update_user_profile(user_id, updates):
    """
    Update user profile information
    """
    try:
        from utils.database import db
        
        # Filter allowed updates
        allowed_updates = {"name", "settings"}
        filtered_updates = {k: v for k, v in updates.items() if k in allowed_updates}
        
        if not filtered_updates:
            return {"success": False, "message": "No valid updates provided"}
        
        user_obj_id = ObjectId(user_id) if isinstance(user_id, str) else user_id
        
        result = db.users.update_one(
            {"_id": user_obj_id},
            {"$set": filtered_updates}
        )
        
        if result.modified_count > 0:
            return {"success": True, "message": "Profile updated successfully"}
        else:
            return {"success": False, "message": "No changes made"}
            
    except Exception as e:
        return {"success": False, "message": str(e)}