# backend/auth.py - COMPLETE UPDATED VERSION
import os
import re
import bcrypt
import jwt
from datetime import datetime, timedelta
from bson import ObjectId

# Configuration
SECRET_KEY = os.getenv("JWT_SECRET", "your-super-secret-jwt-key-change-in-production")
JWT_ALGORITHM = "HS256"
JWT_EXPIRATION_HOURS = 24


# =========================
# PASSWORD HANDLING
# =========================
def hash_password(password: str) -> str:
    """Hash a password for storing"""
    salt = bcrypt.gensalt()
    return bcrypt.hashpw(password.encode('utf-8'), salt).decode('utf-8')


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a stored password against a plain password"""
    try:
        return bcrypt.checkpw(
            plain_password.encode('utf-8'),
            hashed_password.encode('utf-8')
        )
    except Exception:
        return False


# =========================
# JWT TOKEN HANDLING
# =========================
def create_token(user_id, email, role="user"):
    """Create JWT token for user"""
    payload = {
        "user_id": str(user_id),
        "email": email,
        "role": role,
        "exp": datetime.utcnow() + timedelta(hours=JWT_EXPIRATION_HOURS),
        "iat": datetime.utcnow()
    }
    return jwt.encode(payload, SECRET_KEY, algorithm=JWT_ALGORITHM)


def verify_token(token):
    """Verify JWT token"""
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[JWT_ALGORITHM])
        return payload
    except jwt.ExpiredSignatureError:
        return None
    except jwt.InvalidTokenError:
        return None
    except Exception:
        return None


# =========================
# VALIDATION FUNCTIONS
# =========================
def is_valid_email(email):
    """Validate email format"""
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(pattern, email) is not None


def is_valid_name(name):
    """Validate name format"""
    if not name or len(name.strip()) < 2:
        return False
    pattern = r'^[A-Za-z\s\-\']+$'
    return re.match(pattern, name.strip()) is not None


def is_valid_password(password):
    """Validate password strength"""
    if len(password) < 8:
        return False, "Password must be at least 8 characters"
    if not any(c.isupper() for c in password):
        return False, "Password must contain at least one uppercase letter"
    if not any(c.isdigit() for c in password):
        return False, "Password must contain at least one number"
    return True, "Password is valid"


# =========================
# USER REGISTRATION
# =========================
def register_user(name, email, password, role="user"):
    """Register a new user"""
    try:
        # Import inside function to avoid circular imports
        from utils.database import db
        
        # Validate inputs
        if not is_valid_email(email):
            return {
                "success": False,
                "message": "Invalid email format"
            }
        
        if not is_valid_name(name):
            return {
                "success": False,
                "message": "Invalid name format. Name must be at least 2 characters and contain only letters, spaces, hyphens, and apostrophes"
            }
        
        is_pass_valid, pass_msg = is_valid_password(password)
        if not is_pass_valid:
            return {
                "success": False,
                "message": pass_msg
            }
        
        # Check if user already exists
        existing_user = db.users.find_one({"email": email.lower()})
        if existing_user:
            return {
                "success": False,
                "message": "Email already registered"
            }
        
        # Create user document
        user_data = {
            "name": name.strip(),
            "email": email.lower(),
            "password_hash": hash_password(password),
            "role": role,
            "is_active": True,
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow(),
            "last_login": None,
            "settings": {}
        }
        
        # Insert into database
        result = db.users.insert_one(user_data)
        
        # Create token
        token = create_token(result.inserted_id, email, role)
        
        return {
            "success": True,
            "user_id": str(result.inserted_id),
            "token": token,
            "message": "Registration successful"
        }
        
    except Exception as e:
        return {
            "success": False,
            "message": f"Registration failed: {str(e)}"
        }


# =========================
# USER LOGIN
# =========================
def login_user(email, password):
    """Authenticate user login"""
    try:
        # Import inside function to avoid circular imports
        from utils.database import get_user_by_email
        
        # Validate email
        if not email or not password:
            return {
                "success": False,
                "message": "Email and password are required"
            }
        
        # Get user from database
        user = get_user_by_email(email.lower())
        if not user:
            return {
                "success": False,
                "message": "Invalid email or password"
            }
        
        # Check if account is active
        if not user.get("is_active", True):
            return {
                "success": False,
                "message": "Account is deactivated. Please contact support."
            }
        
        # Verify password
        if not verify_password(password, user.get("password_hash", "")):
            return {
                "success": False,
                "message": "Invalid email or password"
            }
        
        # Update last login
        from utils.database import db
        db.users.update_one(
            {"_id": user["_id"]},
            {"$set": {"last_login": datetime.utcnow()}}
        )
        
        # Create token
        token = create_token(user["_id"], user["email"], user.get("role", "user"))
        
        # Prepare user response
        user_response = {
            "user_id": str(user["_id"]),
            "id": str(user["_id"]),  # Compatibility field
            "name": user.get("name", user["email"].split("@")[0]),
            "email": user["email"],
            "role": user.get("role", "user"),
            "is_active": user.get("is_active", True),
            "created_at": user.get("created_at"),
            "last_login": user.get("last_login"),
            "token": token
        }
        
        return {
            "success": True,
            "user": user_response,
            "message": "Login successful"
        }
        
    except Exception as e:
        return {
            "success": False,
            "message": f"Login failed: {str(e)}"
        }


# =========================
# SESSION MANAGEMENT
# =========================
def set_user_session(session, user):
    """Set user session data"""
    session["logged_in"] = True
    session["user_id"] = user["user_id"]
    session["username"] = user.get("name", user["email"].split("@")[0])
    session["email"] = user["email"]
    session["role"] = user.get("role", "user")
    session["token"] = user.get("token")
    session["last_activity"] = datetime.utcnow()


def clear_user_session(session):
    """Clear user session data"""
    session.clear()
    session["logged_in"] = False


# =========================
# USER MANAGEMENT
# =========================
def get_current_user(session_state):
    """Get current user from session state"""
    if not session_state.get("logged_in", False):
        return None
    
    try:
        from utils.database import get_user_by_id
        
        user_id = session_state.get("user_id")
        if not user_id:
            return None
        
        user = get_user_by_id(user_id)
        if not user:
            return None
        
        # Format user data
        user['_id'] = str(user.get('_id', ''))
        user['id'] = user['_id']  # Compatibility field
        user['name'] = user.get('name', 'User')
        user['email'] = user.get('email', '')
        user['role'] = user.get('role', 'user')
        user['is_active'] = user.get('is_active', True)
        
        return user
        
    except Exception as e:
        print(f"Error getting current user: {str(e)}")
        return None


def is_logged_in(session_state):
    """Check if user is logged in"""
    # Basic check
    if not session_state.get("logged_in", False):
        return False
    
    # Check if user_id exists
    if not session_state.get("user_id"):
        return False
    
    # Check session timeout (8 hours)
    last_activity = session_state.get("last_activity")
    if last_activity:
        try:
            if isinstance(last_activity, str):
                last_activity = datetime.fromisoformat(last_activity.replace('Z', '+00:00'))
            
            time_diff = (datetime.utcnow() - last_activity).total_seconds()
            if time_diff > 8 * 3600:  # 8 hours timeout
                # Clear session
                clear_user_session(session_state)
                return False
        except Exception:
            pass
    
    return True


def is_admin(session_state):
    """Check if current user is admin"""
    user = get_current_user(session_state)
    return user and user.get("role") == "admin"


def verify_user_token(token):
    """Verify JWT token and extract user info"""
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
        print(f"Token verification error: {str(e)}")
        return None


def update_user_profile(user_id, updates):
    """Update user profile information"""
    try:
        from utils.database import db
        
        # Filter allowed updates
        allowed_updates = {"name", "settings"}
        filtered_updates = {k: v for k, v in updates.items() if k in allowed_updates}
        
        if not filtered_updates:
            return {"success": False, "message": "No valid updates provided"}
        
        # Add update timestamp
        filtered_updates["updated_at"] = datetime.utcnow()
        
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


# =========================
# PASSWORD MANAGEMENT
# =========================
def change_password(user_id, current_password, new_password):
    """Change user password"""
    try:
        from utils.database import db
        
        user_obj_id = ObjectId(user_id) if isinstance(user_id, str) else user_id
        
        # Get user
        user = db.users.find_one({"_id": user_obj_id})
        if not user:
            return {"success": False, "message": "User not found"}
        
        # Verify current password
        if not verify_password(current_password, user.get("password_hash", "")):
            return {"success": False, "message": "Current password is incorrect"}
        
        # Validate new password
        is_valid, msg = is_valid_password(new_password)
        if not is_valid:
            return {"success": False, "message": msg}
        
        # Update password
        result = db.users.update_one(
            {"_id": user_obj_id},
            {
                "$set": {
                    "password_hash": hash_password(new_password),
                    "updated_at": datetime.utcnow()
                }
            }
        )
        
        if result.modified_count > 0:
            return {"success": True, "message": "Password changed successfully"}
        else:
            return {"success": False, "message": "Failed to change password"}
            
    except Exception as e:
        return {"success": False, "message": str(e)}


# =========================
# ACCOUNT MANAGEMENT
# =========================
def deactivate_account(user_id):
    """Deactivate user account"""
    try:
        from utils.database import db
        
        user_obj_id = ObjectId(user_id) if isinstance(user_id, str) else user_id
        
        result = db.users.update_one(
            {"_id": user_obj_id},
            {
                "$set": {
                    "is_active": False,
                    "updated_at": datetime.utcnow(),
                    "deactivated_at": datetime.utcnow()
                }
            }
        )
        
        if result.modified_count > 0:
            return {"success": True, "message": "Account deactivated successfully"}
        else:
            return {"success": False, "message": "Failed to deactivate account"}
            
    except Exception as e:
        return {"success": False, "message": str(e)}


def activate_account(user_id):
    """Activate user account"""
    try:
        from utils.database import db
        
        user_obj_id = ObjectId(user_id) if isinstance(user_id, str) else user_id
        
        result = db.users.update_one(
            {"_id": user_obj_id},
            {
                "$set": {
                    "is_active": True,
                    "updated_at": datetime.utcnow(),
                    "reactivated_at": datetime.utcnow()
                }
            }
        )
        
        if result.modified_count > 0:
            return {"success": True, "message": "Account activated successfully"}
        else:
            return {"success": False, "message": "Failed to activate account"}
            
    except Exception as e:
        return {"success": False, "message": str(e)}