"""
Self-contained DocVault backend for local development.
Uses SQLite + local filesystem — no AWS/Redis/PostgreSQL needed.

Run: uvicorn local_app:app --reload --port 8000
"""

from __future__ import annotations

import os
import uuid
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional

from fastapi import (
    Cookie, Depends, FastAPI, File, Form, HTTPException, Request,
    Response, UploadFile, status,
)
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from jose import JWTError, jwt
from passlib.context import CryptContext
from pydantic import BaseModel
from sqlalchemy import (
    Boolean, Column, DateTime, ForeignKey, Integer, String, create_engine, func,
)
from sqlalchemy.orm import DeclarativeBase, Session, relationship, sessionmaker

# ── Config ────────────────────────────────────────────────────────────────────
SECRET_KEY = os.getenv("JWT_SECRET", "dev-secret-change-in-prod")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60
REFRESH_TOKEN_EXPIRE_DAYS = 7
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./docvault.db")
UPLOAD_DIR = Path(os.getenv("UPLOAD_DIR", "./uploads"))
UPLOAD_DIR.mkdir(exist_ok=True)
ALLOWED_EXTENSIONS = {"pdf", "ppt", "pptx", "doc", "docx", "html", "txt", "json"}
COOKIE_NAME = "access_token"

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


def create_access_token(user_id: int) -> str:
    exp = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    return jwt.encode({"sub": str(user_id), "exp": exp}, SECRET_KEY, ALGORITHM)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def _decode_token(token: str) -> int:
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return int(payload["sub"])
    except (JWTError, KeyError, ValueError):
        raise HTTPException(status_code=401, detail="Invalid or expired session")


def get_current_user(
    access_token: Optional[str] = Cookie(default=None),
    db: Session = Depends(get_db),
) -> User:
    if not access_token:
        raise HTTPException(status_code=401, detail="Not authenticated")
    user_id = _decode_token(access_token)
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

class FileOut(BaseModel):
    id: int
    name: str
    mime_type: Optional[str] = None
    size_bytes: int
    created_at: datetime
    version_count: int

    class Config:
        from_attributes = True

class VersionOut(BaseModel):
    id: int
    version_number: int
    size_bytes: int
    created_at: datetime

# ── App ───────────────────────────────────────────────────────────────────────
app = FastAPI(title="DocVault API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

def _set_auth_cookie(response: Response, user_id: int) -> str:
    token = create_access_token(user_id)
    response.set_cookie(
        key=COOKIE_NAME,
        value=token,
        httponly=True,
        samesite="lax",
        max_age=ACCESS_TOKEN_EXPIRE_MINUTES * 60,
    )
    return token

# ── Auth ──────────────────────────────────────────────────────────────────────
@app.post("/api/v1/users", status_code=201)
def register(body: RegisterRequest, response: Response, db: Session = Depends(get_db)):
    if db.query(User).filter(User.email == body.email).first():
        raise HTTPException(status_code=409, detail="Email already registered")
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
    _set_auth_cookie(response, user.id)
    return {"id": user.id, "email": user.email}

@app.post("/api/v1/auth/login")
def login(body: LoginRequest, response: Response, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == body.email).first()
    if not user or not verify_password(body.password, user.password_hash):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    _set_auth_cookie(response, user.id)
    return {"id": user.id, "email": user.email}

@app.post("/api/v1/auth/logout")
def logout(response: Response):
    response.delete_cookie(COOKIE_NAME)
    return {"ok": True}

@app.get("/api/v1/users/me")
def me(current_user: User = Depends(get_current_user)):
    return {
        "id": current_user.id,
        "email": current_user.email,
        "fullName": current_user.full_name,
    }

# ── Files ─────────────────────────────────────────────────────────────────────
@app.get("/api/v1/files")
def list_files(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    files = (
        db.query(FileRecord)
        .filter(FileRecord.owner_id == current_user.id, FileRecord.deleted_at.is_(None))
        .order_by(FileRecord.created_at.desc())
        .all()
    )
    return [
        {
            "id": f.id,
            "name": f.name,
            "size": f.size_bytes,
            "lastModified": f.created_at.isoformat(),
            "versionCount": f.versions.count(),
        }
        for f in files
    ]

@app.post("/api/v1/files/upload", status_code=201)
def upload_file(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    filename = file.filename or "upload"
    ext = filename.rsplit(".", 1)[-1].lower() if "." in filename else ""
    if ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(status_code=415, detail=f"File type .{ext} not supported")

    content_bytes = file.file.read()
    storage_name = f"{uuid.uuid4().hex}.{ext}"
    storage_path = UPLOAD_DIR / storage_name
    storage_path.write_bytes(content_bytes)

    rec = FileRecord(
        name=filename,
        mime_type=file.content_type,
        size_bytes=len(content_bytes),
        owner_id=current_user.id,
    )
    db.add(rec)
    db.flush()

    ver = FileVersion(
        file_id=rec.id,
        version_number=1,
        storage_path=str(storage_path),
        size_bytes=len(content_bytes),
    )
    db.add(ver)
    db.commit()
    db.refresh(rec)

    try:
        content_text = content_bytes.decode("utf-8", errors="replace")
    except Exception:
        content_text = f"[Binary file — {len(content_bytes)} bytes]"

    return {
        "id": rec.id,
        "name": rec.name,
        "size": rec.size_bytes,
        "content": content_text,
        "versionCount": 1,
    }

@app.get("/api/v1/files/{file_id}/download")
def download_file(
    file_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    rec = _get_file_or_404(file_id, current_user.id, db)
    ver = rec.versions.order_by(FileVersion.version_number.desc()).first()
    if not ver:
        raise HTTPException(status_code=404)
    return FileResponse(ver.storage_path, filename=rec.name)

@app.get("/api/v1/files/{file_id}/content")
def get_content(
    file_id: int,
    version: Optional[int] = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    rec = _get_file_or_404(file_id, current_user.id, db)
    q = rec.versions
    if version:
        ver = q.filter(FileVersion.version_number == version).first()
    else:
        ver = q.order_by(FileVersion.version_number.desc()).first()
    if not ver:
        raise HTTPException(status_code=404)
    content = Path(ver.storage_path).read_text(errors="replace")
    return {"content": content, "version": ver.version_number, "name": rec.name}

@app.put("/api/v1/files/{file_id}/content")
def update_content(
    file_id: int,
    content: str = Form(...),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    rec = _get_file_or_404(file_id, current_user.id, db)
    last = rec.versions.order_by(FileVersion.version_number.desc()).first()
    next_num = (last.version_number + 1) if last else 1

    ext = rec.name.rsplit(".", 1)[-1].lower() if "." in rec.name else "txt"
    sp = UPLOAD_DIR / f"{uuid.uuid4().hex}.{ext}"
    sp.write_text(content)

    db.add(FileVersion(
        file_id=rec.id,
        version_number=next_num,
        storage_path=str(sp),
        size_bytes=len(content.encode()),
    ))
    rec.size_bytes = len(content.encode())
    db.commit()
    return {"version": next_num, "size_bytes": rec.size_bytes}

@app.get("/api/v1/files/{file_id}/versions")
def list_versions(
    file_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    rec = _get_file_or_404(file_id, current_user.id, db)
    return [
        {"id": v.id, "version_number": v.version_number, "size_bytes": v.size_bytes, "created_at": v.created_at.isoformat()}
        for v in rec.versions.order_by(FileVersion.version_number.desc()).all()
    ]

@app.get("/api/v1/files/{file_id}/diff")
def diff_versions(
    file_id: int,
    v1: int = 1,
    v2: int = 2,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    import difflib
    rec = _get_file_or_404(file_id, current_user.id, db)
    ver1 = db.query(FileVersion).filter(FileVersion.file_id == file_id, FileVersion.version_number == v1).first()
    ver2 = db.query(FileVersion).filter(FileVersion.file_id == file_id, FileVersion.version_number == v2).first()
    if not ver1 or not ver2:
        raise HTTPException(status_code=404, detail="Version not found")
    lines1 = Path(ver1.storage_path).read_text(errors="replace").splitlines(keepends=True)
    lines2 = Path(ver2.storage_path).read_text(errors="replace").splitlines(keepends=True)
    diff = list(difflib.unified_diff(lines1, lines2, fromfile=f"v{v1}", tofile=f"v{v2}"))
    return {"old_version": v1, "new_version": v2, "diff_lines": diff}

@app.delete("/api/v1/files/{file_id}", status_code=204)
def delete_file(
    file_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    rec = _get_file_or_404(file_id, current_user.id, db)
    rec.deleted_at = datetime.utcnow()
    db.commit()
    return Response(status_code=204)

def _get_file_or_404(file_id: int, owner_id: int, db: Session) -> FileRecord:
    rec = db.query(FileRecord).filter(
        FileRecord.id == file_id,
        FileRecord.owner_id == owner_id,
        FileRecord.deleted_at.is_(None),
    ).first()
    if not rec:
        raise HTTPException(status_code=404, detail="File not found")
    return rec

@app.get("/health")
def health():
    # Explicit JSONResponse ensures proper CORS headers are applied
    return JSONResponse(content={"status": "ok"})
