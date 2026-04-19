"""User authentication and management."""

import hashlib
import os
from datetime import datetime, timedelta
from typing import Optional
from pydantic import BaseModel, EmailStr
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPBearer

from api.auth import get_db, verify_api_key
from api.models import SuccessResponse

security = HTTPBearer(auto_error=False)
router = APIRouter(prefix="/auth", tags=["auth"])


# User models
class UserCreate(BaseModel):
    email: EmailStr
    password: str

    def validate_password(self) -> bool:
        return len(self.password) >= 8


class UserResponse(BaseModel):
    id: str
    email: str
    created_at: str


class UserLogin(BaseModel):
    email: EmailStr
    password: str


# Auth config
ALLOW_SIGNUP = os.getenv("OPEN_NOTEBOOK_ALLOW_SIGNUP", "false").lower() == "true"
ENCRYPTION_KEY = os.getenv("OPEN_NOTEBOOK_ENCRYPTION_KEY", "")


def hash_password(password: str, key: str = ENCRYPTION_KEY) -> str:
    """Hash password with encryption key."""
    combined = f"{password}:{key}"
    return hashlib.sha256(combined.encode()).hexdigest()


def verify_password(password: str, hash: str, key: str = ENCRYPTION_KEY) -> bool:
    """Verify password against hash."""
    return hash_password(password, key) == hash


@router.get("/users")
async def list_users(db=Depends(get_db)):
    """List all users (admin only)."""
    verify_api_key(db)
    users = await db.query("SELECT * FROM users ORDER BY created_at DESC")
    return {"users": [UserResponse(id=u["id"], email=u["email"], created_at=u.get("created_at", "")).model_dump() for u in users]}


@router.post("/register", status_code=status.HTTP_201_CREATED)
async def register(user: UserCreate, db=Depends(get_db)):
    """Register a new user."""
    
    if not ALLOW_SIGNUP:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Sign up is disabled. Set OPEN_NOTEBOOK_ALLOW_SIGNUP=true to enable."
        )
    
    if not user.validate_password():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Password must be at least 8 characters"
        )
    
    # Check if user exists
    existing = await db.query("SELECT id FROM users WHERE email = $email", {"email": user.email})
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="User with this email already exists"
        )
    
    # Create user
    password_hash = hash_password(user.password)
    now = datetime.utcnow().isoformat()
    
    result = await db.create(
        "users",
        {
            "email": user.email,
            "password_hash": password_hash,
            "created_at": now,
        }
    )
    
    return {"message": "User created successfully", "user_id": result["id"]}


@router.post("/login")
async def login(credentials: UserLogin, db=Depends(get_db)):
    """Login and get token."""
    
    # First try multi-user lookup
    users = await db.query("SELECT * FROM users WHERE email = $email", {"email": credentials.email})
    
    if users:
        # Multi-user mode
        user = users[0]
        if not verify_password(credentials.password, user["password_hash"]):
            raise HTTPException(status_code=401, detail="Invalid password")
        
        token = f"user_{user['id']}:{hash_password(credentials.email + str(datetime.utcnow()), '')}"
        return {"token": token, "user_id": user["id"], "email": user["email"]}
    
    # Fall back to single-user mode (legacy)
    if not ENCRYPTION_KEY:
        raise HTTPException(status_code=500, detail="Server not configured")
    
    # Check against encryption key as password
    if credentials.password == ENCRYPTION_KEY:
        # Generate session token
        token = hashlib.sha256(f"{credentials.email}:{ENCRYPTION_KEY}:{datetime.utcnow()}".encode()).hexdigest()
        return {"token": token, "mode": "single-user"}
    
    raise HTTPException(status_code=401, detail="Invalid credentials")


@router.delete("/users/{user_id}")
async def delete_user(user_id: str, db=Depends(get_db)):
    """Delete a user (admin only)."""
    verify_api_key(db)
    await db.delete(user_id)
    return {"message": "User deleted"}


@router.get("/config")
async def auth_config():
    """Get auth configuration."""
    return {
        "allow_signup": ALLOW_SIGNUP,
        "mode": "multi-user" if ALLOW_SIGNUP else "single-user",
    }