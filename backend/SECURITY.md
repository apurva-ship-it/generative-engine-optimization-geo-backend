# Security Review — Token Handling

## Implemented Controls

### JWT Authentication
- **Access tokens**: 15-minute expiry (not 30), signed with HS256
- **Refresh tokens**: 7-day expiry, stored as httpOnly SameSite=Lax cookie
- **Access tokens**: Also stored as httpOnly SameSite=Lax cookie — never exposed to JavaScript
- **JTI-based revocation**: Each refresh token carries a unique `jti` claim; revoked JTIs are tracked in-memory, preventing replay after rotation

### Token Lifecycle
- `POST /v1/auth/login` — issues both access + refresh tokens as httpOnly cookies
- `POST /v1/auth/refresh` — rotates refresh token (old JTI revoked, new JTI issued); 401 on revoked/invalid token
- `POST /v1/auth/logout` — revokes refresh JTI, deletes both cookies

### Cookie Hardening
| Attribute | Value | Reason |
|-----------|-------|--------|
| `HttpOnly` | true | Blocks XSS from reading tokens |
| `SameSite` | Lax | Protects against CSRF on state-changing requests |
| `Secure` | false (dev) | Must be `true` in production behind HTTPS |

### Rate Limiting
- `RateLimitMiddleware` tracks failed auth attempts per IP with a 15-minute sliding window
- 5 failed attempts triggers a 15-minute block (HTTP 429)

### CORS
- Origins whitelist enforced at middleware level; unknown origins return 403
- Default allowed: `http://localhost:5173`, `http://localhost:3000`
- Production: set `ALLOWED_ORIGINS` env var to your domain

## Known Limitations (Acceptable for Demo)
- In-memory stores (`_users`, `_revoked_refresh_jti`, `_attempts_store`) are cleared on restart — use Redis/DB in production
- `SECRET_KEY` is hardcoded — move to env var in production
- Rate limit store not shared across multiple instances
