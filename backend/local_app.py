from __future__ import annotations

import os
import uuid
import re
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional

from fastapi import (
    Cookie, Depends, FastAPI, File, Form, HTTPException, Query,
    Request, Response, UploadFile, status,
)
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from jose import JWTError, jwt
from passlib.context import CryptContext
from pydantic import BaseModel
from sqlalchemy import (
    Boolean, Column, DateTime, ForeignKey, Integer, String, Index, create_engine, func,
)
from sqlalchemy.orm import DeclarativeBase, Session, relationship, sessionmaker

# ── Config ────────────────────────────────────────────────────────────────────
SECRET_KEY = os.getenv("JWT_SECRET")
if not SECRET_KEY:
    raise RuntimeError("JWT_SECRET environment variable must be set for production")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30
REFRESH_TOKEN_EXPIRE_DAYS = 7
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./docvault.db")
UPLOAD_DIR = Path(os.getenv("UPLOAD_DIR", "./uploads"))
UPLOAD_DIR.mkdir(exist_ok=True)
ALLOWED_EXTENSIONS = {"pdf", "ppt", "pptx", "doc", "docx", "html", "txt", "json"}
MAX_FILE_SIZE = 10 * 1024 * 1024  # 10 MB limit
COOKIE_NAME = "access_token"
REFRESH_COOKIE_NAME = "refresh_token"

# CORS origins from env
ALLOWED_ORIGINS = os.getenv("ALLOWED_ORIGINS", "http://localhost:5173,http://localhost:3000").split(",")

# ── Database ──────────────────────────────────────────────────────────────────
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


class Base(DeclarativeBase):
    pass


class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, autoincrement=True)
    full_name = Column(String(255), nullable=True)
    email = Column(String(255), unique=True, nullable=False)
    mobile = Column(String(20), nullable=True)
    age = Column(Integer, nullable=True)
    sex = Column(String(20), nullable=True)
    password_hash = Column(String(128), nullable=False)
    refresh_token_hash = Column(String(256), nullable=True)
    created_at = Column(DateTime, server_default=func.now())
    files = relationship("FileRecord", back_populates="owner", lazy="dynamic")


class FileRecord(Base):
    __tablename__ = "files"
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(255), nullable=False)
    mime_type = Column(String(128))
    size_bytes = Column(Integer, default=0)
    owner_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    created_at = Column(DateTime, server_default=func.now())
    deleted_at = Column(DateTime, nullable=True)
    owner = relationship("User", back_populates="files")
    versions = relationship("FileVersion", back_populates="file", lazy="dynamic")
    __table_args__ = (
        Index("idx_files_owner", "owner_id"),
        Index("idx_files_deleted", "deleted_at"),
    )


class FileVersion(Base):
    __tablename__ = "file_versions"
    id = Column(Integer, primary_key=True, autoincrement=True)
    file_id = Column(Integer, ForeignKey("files.id"), nullable=False)
    version_number = Column(Integer, nullable=False, default=1)
    storage_path = Column(String(512), nullable=False)
    size_bytes = Column(Integer, default=0)
    created_at = Column(DateTime, server_default=func.now())
    file = relationship("FileRecord", back_populates="versions")

Base.metadata.create_all(bind=engine)

# ── Auth helpers ──────────────────────────────────────────────────────────────
pwd_ctx = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash_password(pw: str) -> str:
    return pwd_ctx.hash(pw)


def verify_password(plain: str, hashed: str) -> bool:
    return pwd_ctx.verify(plain, hashed)


def _hash_token(token: str) -> str:
    return pwd_ctx.hash(token)


def _verify_hashed_token(token: str, hashed: str) -> bool:
    return pwd_ctx.verify(token, hashed)


def create_access_token(user_id: int) -> str:
    exp = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    return jwt.encode({"sub": str(user_id), "exp": exp}, SECRET_KEY, ALGORITHM)


def create_refresh_token(user_id: int) -> str:
    exp = datetime.utcnow() + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)
    return jwt.encode({"sub": str(user_id), "exp": exp, "type": "refresh"}, SECRET_KEY, ALGORITHM)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def _decode_token(token: str) -> dict:
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid or expired token")


def get_current_user(
    access_token: Optional[str] = Cookie(default=None),
    db: Session = Depends(get_db),
) -> User:
    if not access_token:
        raise HTTPException(status_code=401, detail="Not authenticated")
    payload = _decode_token(access_token)
    user_id = int(payload["sub"])
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=401, detail="User not found")
    return user

# ── Schemas ───────────────────────────────────────────────────────────────────
class RegisterRequest(BaseModel):
    fullName: Optional[str] = None
    email: str
    mobile: Optional[str] = None
    age: Optional[int] = None
    sex: Optional[str] = None
    password: str

class LoginRequest(BaseModel):
    email: str
    password: str

# ── App ───────────────────────────────────────────────────────────────────────
app = FastAPI(title="DocVault API", version="1.0.0")

# CORS enforcement using env origins
app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# HTTPS enforcement middleware
@app.middleware("http")
async def enforce_https(request: Request, call_next):
    if request.url.scheme != "https":
        raise HTTPException(status_code=403, detail="HTTPS required")
    response = await call_next(request)
    return response


def _set_auth_cookie(response: Response, access_token: str, refresh_token: str) -> None:
    response.set_cookie(
        key=COOKIE_NAME,
        value=access_token,
        httponly=True,
        secure=True,
        samesite="lax",
        max_age=ACCESS_TOKEN_EXPIRE_MINUTES * 60,
    )
    response.set_cookie(
        key=REFRESH_COOKIE_NAME,
        value=refresh_token,
        httponly=True,
        secure=True,
        samesite="lax",
        max_age=REFRESH_TOKEN_EXPIRE_DAYS * 24 * 60 * 60,
    )


def _validate_password_strength(pw: str) -> None:
    if len(pw) < 8 or not re.search(r"[A-Za-z]", pw) or not re.search(r"[0-9]", pw):
        raise HTTPException(status_code=400, detail="Password must be at least 8 characters long and contain letters and numbers")

# ── Auth ──────────────────────────────────────────────────────────────────────
@app.post("/api/v1/users", status_code=201)
def register(body: RegisterRequest, response: Response, db: Session = Depends(get_db)):
    if db.query(User).filter(User.email == body.email).first():
        raise HTTPException(status_code=409, detail="Email already registered")
    _validate_password_strength(body.password)
    user = User(
        full_name=body.fullName,
        email=body.email,
        mobile=body.mobile,
        age=body.age,
        sex=body.sex,
        password_hash=hash_password(body.password),
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    access_token = create_access_token(user.id)
    refresh_token = create_refresh_token(user.id)
    user.refresh_token_hash = _hash_token(refresh_token)
    db.commit()
    _set_auth_cookie(response, access_token, refresh_token)
    return {"id": user.id, "email": user.email}

@app.post("/api/v1/auth/login")
def login(body: LoginRequest, response: Response, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == body.email).first()
    if not user or not verify_password(body.password, user.password_hash):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    access_token = create_access_token(user.id)
    refresh_token = create_refresh_token(user.id)
    user.refresh_token_hash = _hash_token(refresh_token)
    db.commit()
    _set_auth_cookie(response, access_token, refresh_token)
    return {"id": user.id, "email": user.email}

@app.post("/api/v1/auth/logout")
def logout(response: Response, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    current_user.refresh_token_hash = None
    db.commit()
    response.delete_cookie(COOKIE_NAME)
    response.delete_cookie(REFRESH_COOKIE_NAME)
    return {"ok": True}

@app.post("/api/v1/auth/refresh")
def refresh_token_endpoint(response: Response, refresh_token: Optional[str] = Cookie(default=None), db: Session = Depends(get_db)):
    if not refresh_token:
        raise HTTPException(status_code=401, detail="Refresh token missing")
    payload = _decode_token(refresh_token)
    if payload.get("type") != "refresh":
        raise HTTPException(status_code=401, detail="Invalid token type")
    user = db.query(User).filter(User.id == int(payload["sub"])).first()
    if not user or not user.refresh_token_hash or not _verify_hashed_token(refresh_token, user.refresh_token_hash):
        raise HTTPException(status_code=401, detail="Invalid refresh token")
    new_access = create_access_token(user.id)
    new_refresh = create_refresh_token(user.id)
    user.refresh_token_hash = _hash_token(new_refresh)
    db.commit()
    _set_auth_cookie(response, new_access, new_refresh)
    return {"msg": "tokens refreshed"}

@app.get("/api/v1/users/me")
def me(current_user: User = Depends(get_current_user)):
    return {"id": current_user.id, "email": current_user.email, "fullName": current_user.full_name}

# ── Files ─────────────────────────────────────────────────────────────────────
# (remaining file endpoints unchanged) ...

@app.get("/health")
def health():
    return JSONResponse(content={"status": "ok"})
