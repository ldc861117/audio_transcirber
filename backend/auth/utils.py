import re
from werkzeug.security import generate_password_hash, check_password_hash

def validate_email(email):
    """Simple email validation."""
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(pattern, email) is not None

def validate_username(username):
    """Username 2-32 characters."""
    return 2 <= len(username) <= 32

def validate_password(password):
    """Password at least 6 characters."""
    return len(password) >= 6

def hash_password(password):
    return generate_password_hash(password)

def verify_password(password_hash, password):
    return check_password_hash(password_hash, password)
