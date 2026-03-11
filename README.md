![Python](https://img.shields.io/badge/python-3.11+-blue?logo=python&logoColor=white)
![FastAPI](https://img.shields.io/badge/FastAPI-0.111+-009688?logo=fastapi&logoColor=white)
![SQLAlchemy](https://img.shields.io/badge/SQLAlchemy-2.0-red)
![Docker](https://img.shields.io/badge/docker-ready-2496ED?logo=docker&logoColor=white)
![License](https://img.shields.io/badge/license-MIT-green)
[![Buy on Gumroad](https://img.shields.io/badge/Buy%20on-Gumroad-FF90E8)](https://vitan0.gumroad.com/l/lufbvz)

# FastAPI Production Starter Kit 🚀

A production-ready FastAPI template with JWT auth, async SQLAlchemy 2.0, Alembic migrations, rate limiting, structured logging, and Docker support.

---

## Features

- ⚡ **FastAPI 0.110+** — async lifespan, automatic OpenAPI docs
- 🗄️ **SQLAlchemy 2.0** — async sessions with asyncpg driver
- 🔄 **Alembic** — database migrations
- 🔐 **JWT Auth** — access token (30 min) + refresh token (7 days) via python-jose
- 🔒 **Bcrypt** — password hashing with passlib
- ⚙️ **Pydantic v2 Settings** — typed config from `.env`
- 🚦 **Rate Limiting** — slowapi on `/login` and `/register`
- 📋 **Structured Logging** — structlog (JSON in prod, pretty in dev)
- 🐳 **Docker** — multi-stage build, non-root user
- 🧪 **Tests** — pytest-asyncio with in-memory SQLite

---

## Quick Start

### Option 1: Docker Compose (recommended)

```bash
# 1. Clone and enter the project
git clone <your-repo> fastapi-starter && cd fastapi-starter

# 2. Copy and configure environment
cp .env.example .env
# Edit .env and set a strong SECRET_KEY:
# openssl rand -hex 32

# 3. Start all services (app + PostgreSQL + pgAdmin)
docker-compose up --build

# App: http://localhost:8000
# Docs (debug mode): http://localhost:8000/docs
# pgAdmin: http://localhost:5050  (admin@admin.com / admin)
```

### Option 2: Local development

```bash
# 1. Create virtual environment
python3.12 -m venv .venv && source .venv/bin/activate

# 2. Install dependencies
pip install -r requirements.txt

# 3. Set up environment
cp .env.example .env
# Edit .env — set DATABASE_URL to your local postgres

# 4. Run migrations
alembic upgrade head

# 5. Start server
uvicorn app.main:app --reload --port 8000
```

---

## Environment Variables

| Variable | Default | Description |
|---|---|---|
| `APP_NAME` | `FastAPI Starter` | Application name |
| `APP_VERSION` | `1.0.0` | Application version |
| `DEBUG` | `false` | Enable debug mode (shows /docs, verbose logs) |
| `ENVIRONMENT` | `production` | Environment name |
| `DATABASE_URL` | — | PostgreSQL connection string (asyncpg) |
| `SECRET_KEY` | — | **Required** JWT signing key (min 32 chars) |
| `ALGORITHM` | `HS256` | JWT algorithm |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | `30` | Access token TTL in minutes |
| `REFRESH_TOKEN_EXPIRE_DAYS` | `7` | Refresh token TTL in days |
| `CORS_ORIGINS` | `http://localhost:3000` | Comma-separated allowed origins |
| `CORS_ALLOW_CREDENTIALS` | `true` | Allow cookies in CORS |
| `RATE_LIMIT_TIMES` | `5` | Max requests per window |
| `RATE_LIMIT_SECONDS` | `60` | Rate limit window in seconds |

> Generate a secure SECRET_KEY:
> ```bash
> openssl rand -hex 32
> ```

---

## API Endpoints

Base URL: `http://localhost:8000/api/v1`

### Authentication

#### `POST /auth/register` — Register a new user

**Rate limited: 5 req/60s**

```bash
curl -X POST http://localhost:8000/api/v1/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "email": "alice@example.com",
    "username": "alice",
    "password": "SecurePass1"
  }'
```

**Response 201:**
```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "email": "alice@example.com",
  "username": "alice",
  "is_active": true,
  "is_admin": false,
  "created_at": "2024-01-01T12:00:00Z",
  "updated_at": "2024-01-01T12:00:00Z"
}
```

---

#### `POST /auth/login` — Login and get tokens

**Rate limited: 5 req/60s**

```bash
curl -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "email": "alice@example.com",
    "password": "SecurePass1"
  }'
```

**Response 200:**
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer"
}
```

---

#### `POST /auth/refresh` — Refresh access token

```bash
curl -X POST http://localhost:8000/api/v1/auth/refresh \
  -H "Content-Type: application/json" \
  -d '{
    "refresh_token": "<your_refresh_token>"
  }'
```

**Response 200:** (new token pair)
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer"
}
```

---

### Users

#### `GET /users/me` — Get current user profile

**Requires:** `Authorization: Bearer <access_token>`

```bash
curl http://localhost:8000/api/v1/users/me \
  -H "Authorization: Bearer <access_token>"
```

**Response 200:**
```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "email": "alice@example.com",
  "username": "alice",
  "is_active": true,
  "is_admin": false,
  "created_at": "2024-01-01T12:00:00Z",
  "updated_at": "2024-01-01T12:00:00Z"
}
```

---

#### `GET /users/?skip=0&limit=100` — List all users (admin only)

**Requires:** `Authorization: Bearer <admin_access_token>`

```bash
curl "http://localhost:8000/api/v1/users/?skip=0&limit=10" \
  -H "Authorization: Bearer <admin_token>"
```

**Response 200:** Array of user objects

---

### Health Check

```bash
curl http://localhost:8000/health
# {"status": "ok", "version": "1.0.0"}
```

---

## Running Tests

Tests use an **in-memory SQLite** database — no PostgreSQL needed.

```bash
# Install test dependencies
pip install -r requirements.txt

# Run all tests
pytest

# Verbose output
pytest -v

# Run specific test file
pytest tests/test_auth.py -v

# With coverage
pip install pytest-cov
pytest --cov=app --cov-report=html
```

---

## Database Migrations

```bash
# Apply all migrations
alembic upgrade head

# Downgrade one step
alembic downgrade -1

# Create a new migration
alembic revision --autogenerate -m "add some table"

# Show migration history
alembic history

# Show current revision
alembic current
```

---

## Project Structure

```
fastapi-starter/
├── app/
│   ├── __init__.py
│   ├── main.py          # FastAPI app, lifespan, routers, exception handlers
│   ├── config.py        # Pydantic Settings (reads from .env)
│   ├── database.py      # Async SQLAlchemy engine, session factory, Base
│   ├── models/
│   │   ├── __init__.py
│   │   └── user.py      # User ORM model (UUID PK, email, username, etc.)
│   ├── schemas/
│   │   ├── __init__.py
│   │   └── user.py      # Pydantic v2 schemas for request/response
│   ├── routers/
│   │   ├── __init__.py
│   │   ├── auth.py      # /register, /login, /refresh + rate limiting
│   │   └── users.py     # /me, /users + auth dependencies
│   ├── services/
│   │   ├── __init__.py
│   │   └── auth.py      # JWT encode/decode, bcrypt, DB user helpers
│   └── middleware/
│       ├── __init__.py
│       └── cors.py      # CORS setup helper
├── alembic/
│   ├── env.py           # Async Alembic environment
│   ├── script.py.mako   # Migration template
│   └── versions/
│       └── 001_initial.py  # Create users table
├── tests/
│   ├── __init__.py
│   ├── conftest.py      # Fixtures: test client, DB, users, tokens
│   ├── test_auth.py     # Tests for register/login/refresh
│   └── test_users.py    # Tests for /me and /users
├── .env.example
├── .gitignore
├── alembic.ini
├── docker-compose.yml   # app + postgres:15 + pgadmin
├── Dockerfile           # Multi-stage, non-root user
├── pyproject.toml       # Dependencies + Ruff config
├── requirements.txt
└── README.md
```

---

## Making a User Admin

Connect to PostgreSQL and update directly:

```sql
UPDATE users SET is_admin = true WHERE email = 'alice@example.com';
```

Or via Docker:
```bash
docker-compose exec db psql -U postgres -d fastapi_db \
  -c "UPDATE users SET is_admin = true WHERE email = 'alice@example.com';"
```

---

## Security Notes

- Always set a strong `SECRET_KEY` in production (`openssl rand -hex 32`)
- In production, set `DEBUG=false` (disables `/docs` and `/redoc`)
- Rate limiting defaults: 5 requests per 60 seconds on `/login` and `/register`
- Passwords require: min 8 chars, at least 1 uppercase letter, at least 1 digit
- App runs as non-root user inside Docker
- Refresh tokens are single-use by design (new pair issued on each refresh)

---

## License

MIT
