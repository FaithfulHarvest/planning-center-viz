"""Security utilities: password hashing, JWT tokens, credential encryption."""
from datetime import datetime, timedelta, timezone
from typing import Optional
from jose import JWTError, jwt
from passlib.context import CryptContext
from cryptography.fernet import Fernet
import base64
import hashlib

from app.config import get_settings

settings = get_settings()

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a password against its hash."""
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    """Generate password hash."""
    return pwd_context.hash(password)


# JWT token handling
def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """Create a JWT access token."""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(hours=settings.access_token_expire_hours)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, settings.secret_key, algorithm=settings.algorithm)
    return encoded_jwt


def decode_access_token(token: str) -> Optional[dict]:
    """Decode and verify a JWT token."""
    try:
        payload = jwt.decode(token, settings.secret_key, algorithms=[settings.algorithm])
        return payload
    except JWTError:
        return None


# Credential encryption for PCO API keys
def _get_fernet() -> Fernet:
    """Get Fernet instance for encryption/decryption."""
    # Ensure key is 32 bytes, base64-encoded
    key = settings.encryption_key
    if len(key) != 44:  # Base64-encoded 32 bytes
        # Derive a proper key from the provided string
        key_bytes = hashlib.sha256(key.encode()).digest()
        key = base64.urlsafe_b64encode(key_bytes).decode()
    return Fernet(key.encode())


def encrypt_credential(plaintext: str) -> str:
    """Encrypt a PCO credential for database storage."""
    f = _get_fernet()
    return f.encrypt(plaintext.encode()).decode()


def decrypt_credential(ciphertext: str) -> str:
    """Decrypt a PCO credential from database."""
    f = _get_fernet()
    return f.decrypt(ciphertext.encode()).decode()


def generate_schema_name(church_name: str, city: str, state: str) -> str:
    """
    Generate a SQL schema name from church name, city, and state.

    Example: "Grace Fellowship" + "Paradise" + "TX" -> "gf_paradise_tx"

    Args:
        church_name: Full church name (e.g., "Grace Fellowship")
        city: City name (e.g., "Paradise")
        state: 2-letter state abbreviation (e.g., "TX")

    Returns:
        Schema name in format: initials_city_state (all lowercase)
    """
    import re

    # Extract first letter of each word in church name
    words = church_name.strip().split()
    initials = ''.join(word[0].lower() for word in words if word)

    # Clean city name (remove special chars, lowercase)
    city_clean = re.sub(r'[^a-zA-Z0-9]', '', city.strip().lower())

    # State abbreviation (lowercase)
    state_clean = state.strip().lower()[:2]

    # Combine: initials_city_state
    schema_name = f"{initials}_{city_clean}_{state_clean}"

    # Ensure valid SQL identifier (max 128 chars, start with letter)
    schema_name = re.sub(r'[^a-z0-9_]', '', schema_name)
    if not schema_name[0].isalpha():
        schema_name = 'c_' + schema_name

    return schema_name[:100]  # Limit length
