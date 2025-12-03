import re
import time
import logging
from datetime import datetime, timedelta

import bcrypt
from pymongo.errors import DuplicateKeyError, PyMongoError

try:
    from utils.database import connect_db
except Exception:
    raise

# bcrypt rounds
BCRYPT_ROUNDS = 12

# Rate limiting
MAX_LOGIN_ATTEMPTS = 5
LOGIN_WINDOW_SECONDS = 15 * 60

_login_attempts = {}

# -------------------------
# Logger
# -------------------------
logger = logging.getLogger("auth")
if not logger.handlers:
    handler = logging.StreamHandler()
    handler.setFormatter(logging.Formatter("%(asctime)s %(levelname)s %(message)s"))
    logger.addHandler(handler)
logger.setLevel(logging.INFO)


# -------------------------
# Helpers
# -------------------------
def db():
    return connect_db()


EMAIL_REGEX = re.compile(r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$")


def _validate_registration_input(name, email, password):
    errors = []
    if not name or len(name.strip()) < 2:
        errors.append("Name must be at least 2 characters.")
    if not re.match(r"^[A-Za-z ]+$", name.strip()):
        errors.append("Name must contain only letters and spaces.")
    if not email or not EMAIL_REGEX.match(email):
        errors.append("Invalid email format.")
    if not password or len(password) < 8:
        errors.append("Password must be at least 8 characters long.")
    if not re.search(r"[A-Z]", password):
        errors.append("Password must contain at least 1 uppercase letter.")
    if not re.search(r"[a-z]", password):
        errors.append("Password must contain at least 1 lowercase letter.")
    if not re.search(r"[0-9]", password):
        errors.append("Password must contain at least 1 number.")
    if not re.search(r"[!@#$%^&*(),.?\":{}|<>]", password):
        errors.append("Password must contain at least 1 special character.")
    return errors


def _validate_login_input(email, password):
    if not email or not EMAIL_REGEX.match(email):
        return False, "Invalid credentials."
    if not password:
        return False, "Invalid credentials."
    return True, None


# -------------------------
# Rate Limiting
# -------------------------
def _cleanup_attempts(identifier):
    now = time.time()
    window_start = now - LOGIN_WINDOW_SECONDS
    attempts = _login_attempts.get(identifier, [])
    attempts = [ts for ts in attempts if ts >= window_start]

    if attempts:
        _login_attempts[identifier] = attempts
    else:
        _login_attempts.pop(identifier, None)


def _record_failed_attempt(identifier):
    now = time.time()
    attempts = _login_attempts.get(identifier, [])
    attempts.append(now)
    _login_attempts[identifier] = attempts
    _cleanup_attempts(identifier)


def _is_rate_limited(identifier):
    _cleanup_attempts(identifier)
    return len(_login_attempts.get(identifier, [])) >= MAX_LOGIN_ATTEMPTS


# -------------------------
# Registration
# -------------------------
def register_user(fullName, email, password):
    try:
        errors = _validate_registration_input(fullName or "", email or "", password or "")
        if errors:
            return {"success": False, "message": "Validation failed: " + "; ".join(errors), "user_id": None}

        mongo = db()
        users = mongo.users

        password_hash = bcrypt.hashpw(
            password.encode("utf-8"),
            bcrypt.gensalt(rounds=BCRYPT_ROUNDS)
        ).decode("utf-8")

        user_doc = {
            "name": fullName.strip(),
            "email": email.strip().lower(),
            "password_hash": password_hash,
            "role": "user",
            "created_at": datetime.utcnow()
        }

        try:
            result = users.insert_one(user_doc)
            logger.info("User registered: %s", user_doc["email"])
            return {"success": True, "message": "User registered successfully", "user_id": str(result.inserted_id)}
        except DuplicateKeyError:
            logger.warning("Duplicate registration email: %s", email)
            return {"success": False, "message": "Email already registered", "user_id": None}
        except PyMongoError:
            logger.exception("Database error during registration")
            return {"success": False, "message": "Database error", "user_id": None}

    except Exception as e:
        logger.exception("Unexpected error in register_user: %s", e)
        return {"success": False, "message": "Internal error", "user_id": None}


# -------------------------
# Login
# -------------------------
def login_user(email, password, identifier=None):
    try:
        ok, err = _validate_login_input(email, password)
        if not ok:
            return {"success": False, "message": "Invalid credentials", "user": None}

        ident = identifier or email.lower()
        if _is_rate_limited(ident):
            logger.warning("Rate limit reached for %s", ident)
            return {"success": False, "message": "Too many failed attempts. Try again later.", "user": None}

        mongo = db()
        users = mongo.users

        user = users.find_one({"email": email.lower()})
        if not user:
            _record_failed_attempt(ident)
            logger.info("Failed login (unknown email): %s", email)
            return {"success": False, "message": "Invalid credentials", "user": None}

        stored_hash = user.get("password_hash", "")
        try:
            matches = bcrypt.checkpw(password.encode("utf-8"), stored_hash.encode("utf-8"))
        except Exception:
            _record_failed_attempt(ident)
            return {"success": False, "message": "Invalid credentials", "user": None}

        if not matches:
            _record_failed_attempt(ident)
            logger.info("Failed login (bad password) for email: %s", email)
            return {"success": False, "message": "Invalid credentials", "user": None}

        # successful login
        if ident in _login_attempts:
            _login_attempts.pop(ident, None)

        user_safe = {
            "user_id": str(user["_id"]),
            "name": user.get("name"),
            "email": user.get("email"),
            "role": user.get("role", "user"),
            "created_at": user.get("created_at")
        }

        return {"success": True, "message": "Login successful", "user": user_safe}

    except PyMongoError:
        logger.exception("Database error on login")
        return {"success": False, "message": "Database error", "user": None}
    except Exception as e:
        logger.exception("Unexpected login error: %s", e)
        return {"success": False, "message": "Internal error", "user": None}


# -------------------------
# Session Helpers
# -------------------------
def is_logged_in(st_session):
    return bool(st_session.get("logged_in"))


def get_current_user(st_session):
    if not is_logged_in(st_session):
        return None
    return {
        "user_id": st_session.get("user_id"),
        "name": st_session.get("user_name"),
        "email": st_session.get("user_email"),
        "role": st_session.get("user_role")
    }


def logout(st_session, redirect_fn=None):
    for k in ["logged_in", "user_id", "user_name", "user_email", "user_role"]:
        st_session.pop(k, None)

    if redirect_fn:
        redirect_fn()

    return {"success": True, "message": "Logged out successfully"}
