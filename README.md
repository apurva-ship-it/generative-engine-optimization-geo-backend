# DocVault — Production-Grade File Management App

Built by the PDLC Autonomous Agent Pipeline (May 2026).

---

## Tech Stack

### Backend
| Layer | Technology |
|-------|-----------|
| Runtime | Python 3.9+ |
| API Framework | **FastAPI** (async, OpenAPI auto-docs) |
| ORM | **SQLAlchemy** + **Alembic** migrations |
| Database (local) | SQLite (via `local_app.py`) |
| Database (production) | **AWS RDS PostgreSQL** |
| Auth | **JWT** — access token (60 min) + refresh token (7 days), stored as httpOnly cookies |
| Password hashing | **passlib + bcrypt** |
| File storage (local) | Local filesystem under `uploads/` |
| File storage (production) | **AWS S3** — presigned PUT/GET URLs (5 min expiry) |
| Rate limiting | In-memory sliding window (Redis in prod) |
| Testing | pytest + httpx |

### Frontend
| Layer | Technology |
|-------|-----------|
| Framework | **React 18** + **TypeScript** |
| Build tool | **Vite 5** |
| Routing | React Router v6 |
| Styling | **Tailwind CSS** + inline styles |
| Form validation | Yup |
| Testing | Vitest + Testing Library |

### Infrastructure (production)
| Layer | Technology |
|-------|-----------|
| Containers | **Docker** + **AWS ECS Fargate** |
| CDN | **AWS CloudFront** |
| Cache / Rate limit | **AWS ElastiCache Redis** |
| Secrets | **AWS Secrets Manager** |
| Observability | **AWS CloudWatch** |
| CI/CD | **GitHub Actions** → ECR → ECS Fargate |

---

## Architecture

```
Browser (React + Vite)
        │  HTTP (cookie-based JWT)
        ▼
  ┌─────────────────────────────────────────┐
  │           FastAPI  (port 8000)           │
  │                                         │
  │  /api/v1/auth/*   — register, login,    │
  │                     logout, /me         │
  │  /api/v1/files/*  — list, upload,       │
  │                     content, versions,  │
  │                     diff, delete        │
  │  /api/v1/presigned/* — S3 URLs (prod)   │
  │                                         │
  │  Middleware: CORS, Rate limiting        │
  └────────────┬──────────────┬────────────┘
               │              │
          SQLite/RDS        S3 / local
          (users, files,   (file bytes,
           versions)        all versions)
```

### Auth Flow
```
POST /api/v1/users  (register)
POST /api/v1/auth/login
      │
      └─► Sets httpOnly cookie: access_token (JWT, 60 min)
              │
              ▼
      All /api/v1/* routes read cookie → decode JWT → get user
```

### File Versioning
```
Upload file  → FileRecord created → FileVersion v1 stored
Edit & save  → FileVersion v2 stored (old version preserved)
GET /versions → list all versions with metadata
GET /diff?v1=1&v2=2 → unified diff between any two versions
```

---

## Local Setup

### Backend
```bash
cd sample_app/backend
pip install fastapi uvicorn "python-jose[cryptography]" "passlib[bcrypt]" sqlalchemy python-multipart "bcrypt==4.2.1"
uvicorn local_app:app --reload --port 8000
```
- API docs: http://localhost:8000/docs
- Health:   http://localhost:8000/health

### Frontend
```bash
cd sample_app/frontend
npm install
npm run dev
```
- App: http://localhost:5173

---

## Task Board (22 tasks)

| ID | Title | Status |
|----|-------|--------|
| TASK-001 | [BE] Create users table migration | ✅ MERGED |
| TASK-002 | [BE] Create refresh_tokens table migration | ✅ MERGED |
| TASK-003 | [BE] Create files table migration | ✅ MERGED |
| TASK-004 | [BE] Create file_versions table migration | ✅ MERGED |
| TASK-005 | [BE] Implement JWT auth router | 🔄 In progress |
| TASK-006 | [BE] Implement rate limiting middleware | ✅ MERGED |
| TASK-007 | [BE] Add CORS middleware | 🔄 In progress |
| TASK-008 | [BE] Create file CRUD router | ✅ MERGED |
| TASK-009 | [BE] Implement presigned URL generator | ✅ MERGED |
| TASK-010 | [FE] Create FileListTable component | ✅ MERGED |
| TASK-011 | [FE] Create UploadDropzone component | ✅ MERGED |
| TASK-012 | [FE] Show upload progress bars | 🔄 In progress |
| TASK-013 | [FE] Implement file editor panel | 🔄 In progress |
| TASK-014 | [FE] VersionDrawer component | 🔄 In progress |
| TASK-015 | [FE] ToastProvider component | ✅ MERGED |
| TASK-016 | [BE] Add soft delete handler | ✅ MERGED |
| TASK-017 | [BE] Implement diff endpoint | ✅ MERGED |
| TASK-018 | [QA] Unit tests for auth and file services | ⏳ Pending |
| TASK-019 | [QA] Integration tests for auth and files | ⏳ Pending |
| TASK-020 | [QA] End-to-end Playwright tests | ⏳ Pending |
| TASK-021 | [SEC] Security review of token handling | ⏳ Pending |
| TASK-022 | [API] Register Dockerfile and CI pipeline | ✅ MERGED |

---

## Supported File Types
`pdf` · `ppt` · `pptx` · `doc` · `docx` · `html` · `txt` · `json`
