from __future__ import annotations

import os
import uuid
import re
import time
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional, Dict, List

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
ENVIRONMENT = os.getenv("ENV", "development")

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

# ── Rate limiting (simple in‑memory) ────────────────────────────────────────
_login_attempts: Dict[str, List[float]] = {}
LOGIN_LIMIT = 5  # attempts
LOGIN_WINDOW = 60  # seconds

def _check_rate_limit(ip: str) -> None:
    now = time.time()
    attempts = _login_attempts.get(ip, [])
    attempts = [t for t in attempts if now - t < LOGIN_WINDOW]
    if len(attempts) >= LOGIN_LIMIT:
        raise HTTPException(status_code=429, detail="Too many attempts")
    attempts.append(now)
    _login_attempts[ip] = attempts

# Apply to mutating endpoints
def rate_limit_dep(request: Request):
    _check_rate_limit(request.client.host)

# ── App ───────────────────────────────────────────────────────────────────────
app = FastAPI(title="DocVault API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.middleware("http")
async def enforce_https(request: Request, call_next):
    if ENVIRONMENT == "production" and request.url.scheme != "https":
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
    # At least 8 chars, one letter, one number, one special char
    if (
        len(pw) < 8
        or not re.search(r"[A-Za-z]", pw)
        or not re.search(r"[0-9]", pw)
        or not re.search(r"[!@#$%^&*()_+=\-{}\[\]|\\:;\"'<>,.?/]", pw)
    ):
        raise HTTPException(status_code=400, detail="Password must be at least 8 characters long, contain letters, numbers, and a special character")

# ── Auth ──────────────────────────────────────────────────────────────────────
@app.post("/api/v1/users", status_code=201, dependencies=[Depends(rate_limit_dep)])
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

@app.post("/api/v1/auth/login", dependencies=[Depends(rate_limit_dep)])
def login(body: LoginRequest, request: Request, response: Response, db: Session = Depends(get_db)):
    _check_rate_limit(request.client.host)
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
    # Expire refresh token cookie
    response.set_cookie(key=REFRESH_COOKIE_NAME, value="", httponly=True, secure=True, samesite="lax", max_age=0)
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
def _allowed_file(filename: str) -> bool:
    ext = filename.rsplit(".", 1)[-1].lower() if "." in filename else ""
    return ext in ALLOWED_EXTENSIONS

@app.get("/api/v1/files")
def list_files(limit: int = Query(20, ge=1, le=100), offset: int = Query(0, ge=0), current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    q = db.query(FileRecord).filter(FileRecord.owner_id == current_user.id, FileRecord.deleted_at.is_(None)).order_by(FileRecord.created_at.desc())
    total = q.count()
    items = q.offset(offset).limit(limit).all()
    return {
        "total": total,
        "limit": limit,
        "offset": offset,
        "items": [
            {
                "id": f.id,
                "name": f.name,
                "mime_type": f.mime_type,
                "size_bytes": f.size_bytes,
                "created_at": f.created_at.isoformat(),
                "version_count": f.versions.count(),
            }
            for f in items
        ],
    }

@app.post("/api/v1/files/upload", status_code=201, dependencies=[Depends(rate_limit_dep)])
def upload_file(file: UploadFile = File(...), current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    if not _allowed_file(file.filename):
        raise HTTPException(status_code=415, detail="Unsupported file type")
    content = file.file.read()
    if len(content) > MAX_FILE_SIZE:
        raise HTTPException(status_code=413, detail="File too large")
    # Check for existing file name
    existing = db.query(FileRecord).filter(FileRecord.owner_id == current_user.id, FileRecord.name == file.filename, FileRecord.deleted_at.is_(None)).first()
    ext = file.filename.rsplit(".", 1)[-1].lower()
    storage_name = f"{uuid.uuid4().hex}.{ext}"
    storage_path = UPLOAD_DIR / storage_name
    storage_path.write_bytes(content)
    if existing:
        # create new version
        latest = existing.versions.order_by(FileVersion.version_number.desc()).first()
        next_ver = (latest.version_number + 1) if latest else 1
        ver = FileVersion(file_id=existing.id, version_number=next_ver, storage_path=str(storage_path), size_bytes=len(content))
        db.add(ver)
        existing.size_bytes = len(content)
        db.commit()
        return {"id": existing.id, "name": existing.name, "size_bytes": existing.size_bytes, "version": next_ver}
    else:
        rec = FileRecord(name=file.filename, mime_type=file.content_type, size_bytes=len(content), owner_id=current_user.id)
        db.add(rec)
        db.flush()
        ver = FileVersion(file_id=rec.id, version_number=1, storage_path=str(storage_path), size_bytes=len(content))
        db.add(ver)
        db.commit()
        db.refresh(rec)
        return {"id": rec.id, "name": rec.name, "size_bytes": rec.size_bytes, "version": 1}

@app.patch("/api/v1/files/{file_id}", dependencies=[Depends(rate_limit_dep)])
def upload_new_version(file_id: int, file: UploadFile = File(...), current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    if not _allowed_file(file.filename):
        raise HTTPException(status_code=415, detail="Unsupported file type")
    rec = db.query(FileRecord).filter(FileRecord.id == file_id, FileRecord.owner_id == current_user.id, FileRecord.deleted_at.is_(None)).first()
    if not rec:
        raise HTTPException(status_code=404, detail="File not found")
    content = file.file.read()
    if len(content) > MAX_FILE_SIZE:
        raise HTTPException(status_code=413, detail="File too large")
    ext = rec.name.rsplit(".", 1)[-1].lower()
    storage_name = f"{uuid.uuid4().hex}.{ext}"
    storage_path = UPLOAD_DIR / storage_name
    storage_path.write_bytes(content)
    latest = rec.versions.order_by(FileVersion.version_number.desc()).first()
    next_ver = (latest.version_number + 1) if latest else 1
    ver = FileVersion(file_id=rec.id, version_number=next_ver, storage_path=str(storage_path), size_bytes=len(content))
    db.add(ver)
    rec.size_bytes = len(content)
    db.commit()
    return {"id": rec.id, "version": next_ver, "size_bytes": rec.size_bytes}

@app.get("/api/v1/files/{file_id}/download")
def download_file(file_id: int, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    rec = db.query(FileRecord).filter(FileRecord.id == file_id, FileRecord.owner_id == current_user.id, FileRecord.deleted_at.is_(None)).first()
    if not rec:
        raise HTTPException(status_code=404, detail="File not found")
    ver = rec.versions.order_by(FileVersion.version_number.desc()).first()
    return FileResponse(ver.storage_path, filename=rec.name)

@app.delete("/api/v1/files/{file_id}", status_code=204, dependencies=[Depends(rate_limit_dep)])
def delete_file(file_id: int, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    rec = db.query(FileRecord).filter(FileRecord.id == file_id, FileRecord.owner_id == current_user.id, FileRecord.deleted_at.is_(None)).first()
    if not rec:
        raise HTTPException(status_code=404, detail="File not found")
    rec.deleted_at = datetime.utcnow()
    db.commit()
    return Response(status_code=204)

@app.get("/api/v1/files/{file_id}/versions")
def list_versions(file_id: int, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    rec = db.query(FileRecord).filter(FileRecord.id == file_id, FileRecord.owner_id == current_user.id, FileRecord.deleted_at.is_(None)).first()
    if not rec:
        raise HTTPException(status_code=404, detail="File not found")
    return [
        {
            "id": v.id,
            "version_number": v.version_number,
            "size_bytes": v.size_bytes,
            "created_at": v.created_at.isoformat(),
        }
        for v in rec.versions.order_by(FileVersion.version_number.desc()).all()
    ]

# Root & health
@app.get("/")
def root():
    return JSONResponse(content={"message": "DocVault API"})

@app.get("/health")
def health():
    return JSONResponse(content={"status": "ok"})
