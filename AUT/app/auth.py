"""
Authentication for the AUT: OAuth2 password flow with JWT bearer tokens.

Two fixed users for testing purposes:
  - admin / admin  -> role "admin", full access (GET/POST/PUT/DELETE)
  - user  / user   -> role "user",  read-only access (GET only)

Passwords are hashed with the standard library's hashlib (PBKDF2-HMAC-SHA256)
rather than a compiled package like bcrypt, so no C/Rust build toolchain is
ever needed to install this project's dependencies.

NOTE: SECRET_KEY and the hardcoded credentials are intentionally simple
because this is a throwaway application-under-test, not a production
service. Do not reuse this pattern for anything real.
"""
import hashlib
import hmac
import os
from datetime import datetime, timedelta, timezone

import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jwt.exceptions import InvalidTokenError

from app.schemas import TokenData

SECRET_KEY = "aut-demo-secret-key-change-me"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

PBKDF2_ITERATIONS = 200_000


def _hash_password(password: str, salt: bytes | None = None) -> tuple[bytes, bytes]:
    salt = salt or os.urandom(16)
    digest = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, PBKDF2_ITERATIONS)
    return salt, digest


def _make_user(username: str, password: str, role: str) -> dict:
    salt, digest = _hash_password(password)
    return {"username": username, "salt": salt, "hashed_password": digest, "role": role}


USERS_DB = {
    "admin": _make_user("admin", "admin", "admin"),
    "user": _make_user("user", "user", "user"),
}

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")


def verify_password(plain_password: str, salt: bytes, expected_hash: bytes) -> bool:
    _, digest = _hash_password(plain_password, salt)
    return hmac.compare_digest(digest, expected_hash)


def authenticate_user(username: str, password: str):
    user = USERS_DB.get(username)
    if not user or not verify_password(password, user["salt"], user["hashed_password"]):
        return None
    return user


def create_access_token(data: dict, expires_delta: timedelta | None = None) -> str:
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + (
        expires_delta or timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    )
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)


def get_current_user(token: str = Depends(oauth2_scheme)) -> TokenData:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username = payload.get("sub")
        role = payload.get("role")
        if username is None:
            raise credentials_exception
        return TokenData(username=username, role=role)
    except InvalidTokenError:
        raise credentials_exception


def require_admin(current_user: TokenData = Depends(get_current_user)) -> TokenData:
    if current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin privileges required",
        )
    return current_user
