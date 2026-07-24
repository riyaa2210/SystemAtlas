# Living Architecture Map (LAM)

> **AI-powered software architecture visualization and code intelligence platform.**

Connect any public GitHub repository, automatically scan its codebase, generate an interactive architecture graph, discover risks, and ask AI questions about your code — all from a clean SaaS dashboard.

---

## Live Demo

| Service | URL |
|---|---|
| Frontend | https://lam-app.vercel.app *(deploy to get URL)* |
| Backend API | https://lam-backend.onrender.com *(deploy to get URL)* |
| API Docs | https://lam-backend.onrender.com/docs |

---

## Features

| Feature | Description |
|---|---|
| **GitHub Scanner** | Connect any public repo — auto-detects languages, frameworks, dependencies |
| **Code Analysis** | AST/regex extraction of classes, functions, imports, API routes, DB calls |
| **Architecture Graph** | Interactive React Flow canvas — pan, zoom, click nodes, search, edge highlighting |
| **Architecture Score** | 0–100 health score based on coupling, circular deps, dead modules, docs coverage |
| **Risk Detection** | Circular dependencies, highly-coupled modules, dead code, missing documentation |
| **AI Copilot** | Ask natural language questions about your codebase, powered by Gemini 1.5 Flash |

---

## Tech Stack

```
┌─────────────────────────────────────────────────────────┐
│  Frontend: Next.js 15 · TypeScript · Tailwind · React Flow │
│  Deployed: Vercel                                         │
└───────────────────────┬─────────────────────────────────┘
                        │ REST API
┌───────────────────────▼─────────────────────────────────┐
│  Backend: FastAPI · Python 3.10 · SQLAlchemy · Pydantic  │
│  Deployed: Render                                         │
└──────┬──────────┬──────────┬──────────┬─────────────────┘
       │          │          │          │
  PostgreSQL   Neo4j     GitHub     Gemini
  (Supabase)  (Aura)      API      1.5 Flash
```

---

## Project Structure

```
LAM/
├── backend/
│   ├── app/
│   │   ├── api/v1/          # Route handlers (auth, repositories, graph, analytics, copilot)
│   │   ├── core/            # Pure business logic — zero framework dependencies
│   │   │   ├── auth/        # JWT + bcrypt password hashing
│   │   │   ├── scanner/     # GitHub API client, git clone, language detection, manifest parsing
│   │   │   ├── analyzer/    # Python AST + JS/Java regex code analysis
│   │   │   ├── graph/       # Neo4j graph builder, Cypher queries, risk detector
│   │   │   ├── analytics/   # Architecture score computation
│   │   │   └── copilot/     # Gemini API client, context assembler
│   │   ├── services/        # Use-case orchestration (scan pipeline, auth flow)
│   │   ├── repositories/    # Data access layer (PostgreSQL + Neo4j)
│   │   ├── models/          # SQLAlchemy ORM models
│   │   ├── schemas/         # Pydantic request/response schemas
│   │   └── db/              # DB connections + Alembic migrations
│   └── tests/
│       ├── unit/            # Scanner, analyzer, JWT tests (no DB needed)
│       └── integration/     # Full API tests (needs Supabase)
│
└── frontend/
    └── src/
        ├── app/             # Next.js 15 App Router
        │   ├── (auth)/      # Login, Register
        │   └── (dashboard)/ # Dashboard, Repositories, Graph, Analytics, Copilot, Settings
        ├── components/      # Auth forms, graph nodes, analytics cards, copilot chat
        ├── hooks/           # useRepositories, useGraph, useAnalytics, useCopilot
        ├── lib/             # API client (axios), Zustand stores
        └── types/           # TypeScript type definitions
```

---

## Setup

### Prerequisites

- Python 3.10+
- Node.js 20+
- [Supabase](https://supabase.com) account (free tier)
- [Neo4j Aura](https://neo4j.com/cloud/platform/aura-graph-database/) account (free tier)
- [Gemini API key](https://aistudio.google.com/app/apikey) (free tier)
- [GitHub PAT](https://github.com/settings/tokens) (optional, for higher rate limits)

### 1. Clone and configure

```bash
git clone https://github.com/yourusername/lam.git
cd lam
```

### 2. Backend setup

```bash
cd backend

# Create virtual environment
python -m venv .venv
.venv\Scripts\activate       # Windows
# source .venv/bin/activate  # Mac/Linux

# Install dependencies
pip install -r requirements.txt

# Configure environment
cp .env.example .env
# Edit .env — fill in DATABASE_URL, NEO4J_*, SECRET_KEY, GEMINI_API_KEY
```

**Generate a SECRET_KEY:**
```bash
python -c "import secrets; print(secrets.token_hex(32))"
```

**Verify setup:**
```bash
python setup.py
```

**Start the backend:**
```bash
uvicorn app.main:app --reload
# API: http://localhost:8000
# Swagger: http://localhost:8000/docs
```

### 3. Frontend setup

```bash
cd frontend

npm install

cp .env.local.example .env.local
# Edit .env.local: NEXT_PUBLIC_API_URL=http://localhost:8000/api/v1

npm run dev
# App: http://localhost:3000
```

### 4. Database setup (Supabase)

1. Create a project at [supabase.com](https://supabase.com)
2. Go to **Project Settings → Database → Connection String → URI**
3. Copy the URI and set it as `DATABASE_URL` in `backend/.env`
   - Change `postgresql://` to `postgresql+asyncpg://`
4. Restart the backend — tables are created automatically

### 5. Graph database setup (Neo4j Aura)

1. Create a free instance at [Neo4j Aura](https://neo4j.com/cloud/platform/aura-graph-database/)
2. Download the credentials file shown during creation
3. Set `NEO4J_URI`, `NEO4J_USERNAME`, `NEO4J_PASSWORD` in `backend/.env`

---

## API Reference

All endpoints are documented interactively at `http://localhost:8000/docs`

```
POST /api/v1/auth/register          Register a new account
POST /api/v1/auth/login             Login → JWT token
GET  /api/v1/auth/me                Get current user profile

GET  /api/v1/repositories           List repositories
POST /api/v1/repositories           Add a GitHub repository
GET  /api/v1/repositories/{id}      Get repository details
DELETE /api/v1/repositories/{id}    Delete repository
POST /api/v1/repositories/{id}/scan Trigger a scan (async)
GET  /api/v1/repositories/{id}/scan List scan history
GET  /api/v1/repositories/{id}/scan/{job_id}  Get scan status

GET  /api/v1/graph/{repo_id}                  Full architecture graph
GET  /api/v1/graph/{repo_id}/node/{node_id}   Node detail + neighbors

GET  /api/v1/analytics/{repo_id}              Architecture metrics
GET  /api/v1/analytics/{repo_id}/risks        Risk items list

POST /api/v1/copilot/ask            Ask AI about the codebase
```

---

## Running Tests

```bash
cd backend

# Unit tests (no database required — run these first)
python -m pytest tests/unit/ tests/test_auth_quick.py -v

# Integration tests (requires Supabase connection)
python -m pytest tests/integration/ -v
```

---

## Deployment

### Backend → Render

1. Push to GitHub
2. Create a new **Web Service** on [Render](https://render.com)
3. Connect your GitHub repo, set root directory to `backend`
4. Build command: `pip install -r requirements.txt`
5. Start command: `uvicorn app.main:app --host 0.0.0.0 --port $PORT`
6. Add all environment variables from `.env.example` in the Render dashboard

### Frontend → Vercel

1. Import the repo on [Vercel](https://vercel.com)
2. Set root directory to `frontend`
3. Add environment variable: `NEXT_PUBLIC_API_URL=https://your-render-url.onrender.com/api/v1`
4. Deploy

---

## Architecture Decisions

| Decision | Why |
|---|---|
| FastAPI over Django | Async-native, automatic OpenAPI docs, ideal for Python AI/data ecosystem |
| BackgroundTasks over Celery | No Redis needed; scan jobs are per-user, not high-volume |
| Neo4j for graph | Circular dependency detection and path traversal are natural Cypher queries |
| Python `ast` for parsing | More reliable than regex for Python; built-in, no extra deps |
| Regex for JS/Java | Tree-sitter bindings are brittle on Windows; regex covers 90% of cases |
| Structured context over embeddings | Embeddings add cost + complexity; structured prompts are faster and more predictable |
| Zustand over Redux | Much simpler for the state complexity here |
| Next.js App Router | Current best practice; route groups cleanly separate auth/dashboard |

---

## Scan Pipeline

```
User submits GitHub URL
    ↓
Fetch metadata from GitHub API (name, branch, languages)
    ↓
Shallow git clone to /tmp/{job_id}/  (depth=1, ~5-30s)
    ↓
Language detection + manifest parsing (package.json, requirements.txt, pom.xml...)
    ↓
File-by-file AST/regex analysis → extract classes, functions, imports, APIs, DB calls
    ↓
Build Neo4j graph: Repository → Module → File → Api nodes + IMPORTS/DEFINES edges
    ↓
Risk detection: circular deps (DFS), high coupling (degree), dead modules (in-degree=0)
    ↓
Architecture score (0-100) computed and stored in PostgreSQL
    ↓
Temp directory cleaned up
```

---

## Future Improvements

- GitHub OAuth login
- Private repository support via GitHub App
- Full Tree-sitter integration for Go, Rust, C# analysis
- Vector embeddings for semantic code search
- Architecture diff on PR (before/after graph comparison)
- Team workspaces and shared repositories
- Export graph as SVG/PNG
- Webhook-based auto-rescan on push
- Custom architecture rules (e.g. "service A should not import service B")

---

## Interview Talking Points

**System Design**
- "The scan runs as a FastAPI `BackgroundTask` — the API returns 202 immediately, the client polls for status every 2 seconds. No message queue needed at this scale."
- "Neo4j and PostgreSQL serve different purposes: PostgreSQL owns users, repos, and job state (relational, ACID); Neo4j owns the graph structure (natural for traversal queries)."

**Architecture**
- "I follow Clean Architecture: `core/` has zero framework dependencies — it could be dropped into a Django or Flask project unchanged. `services/` orchestrates, `repositories/` owns data access, `api/` is just HTTP glue."

**AI**
- "I deliberately avoided embeddings. Structured context injection gives predictable, fast, cheap answers. Embeddings would only help for 'find code similar to X' queries — not for architectural questions."

**Trade-offs**
- "I used regex for JS/Java analysis instead of Tree-sitter because the tree-sitter Python bindings are unstable on Windows and I wanted zero installation friction. The regex covers ~90% of real-world patterns."
