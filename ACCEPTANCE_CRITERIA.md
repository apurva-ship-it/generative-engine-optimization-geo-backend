# Acceptance Criteria for BUG-013

The purpose of this sub‑task is to ensure that the backend integration tests can run successfully.

## Required Criteria
1. **`requirements.txt`** must list all runtime and test dependencies, including `pytest` and `pytest‑asyncio`.
2. The project must contain a **FastAPI** application entry point (`backend/main.py`) that creates the app, includes routers, and configures CORS using the `ALLOWED_ORIGINS` setting.
3. **SQLAlchemy** integration must be asynchronous:
   - `backend/database.py` provides `engine`, `AsyncSessionLocal`, `Base`, and a `get_db` dependency.
4. A **User** model (`backend/models/user.py`) with at least the fields `id`, `email`, `hashed_password`, `is_active`, and timestamps.
5. **Pydantic v2** schemas (`backend/schemas/user.py`, `backend/schemas/token.py`) use `model_config = ConfigDict(from_attributes=True)`.
6. **Authentication** implementation (`backend/auth_utils.py`, `backend/routers/auth.py`) provides:
   - Register (`POST /api/v1/auth/register`)
   - Login (`POST /api/v1/auth/login`)
   - Token refresh (`POST /api/v1/auth/refresh`)
   - JWT access tokens expire in **30 minutes** and contain the user id in the `sub` claim.
7. **Password handling** uses `passlib` with bcrypt – passwords are never stored or returned in plain text.
8. **Dependency injection** is used throughout routers; endpoints depend on `db: Annotated[AsyncSession, Depends(get_db)]`.
9. **User CRUD** router (`backend/routers/users.py`) implements GET (list/me), POST (create), PUT (update), DELETE (remove) with appropriate authentication and role checks.
10. **Tests** (`backend/tests/`):
    - `conftest.py` sets up an async test database and `AsyncClient` fixture.
    - `test_auth.py` covers registration, login, wrong credentials, and token refresh.
    - `test_users.py` covers protected CRUD operations.
    - All tests are marked with `@pytest.mark.asyncio` and run without external services.
11. **Alembic migrations** exist for the initial schema (`backend/alembic/versions/...`). The project never calls `Base.metadata.create_all()` directly.
12. **CORS** is enforced according to `ALLOWED_ORIGINS`; requests from other origins receive a 403 response.
13. The code passes **ruff** linting and **mypy** static type checks.
14. Running `pytest` from the repository root executes the integration test suite successfully.

These criteria are used by the automated grader to verify that the implementation is complete and functional.
