# ChatDoc — AI Document Chatbot Platform

A self-hosted platform for chatting with your documents. Upload PDFs, Word files, spreadsheets, and Markdown — then ask questions in natural language. Supports OpenAI, Gemini, DeepSeek, OpenRouter, and Ollama.

---

## Requirements

| Tool | Minimum version |
|------|-----------------|
| Docker | 24.x |
| Docker Compose | 2.x (plugin, not standalone) |
| Git | any |

No Python or Node.js needed on the host — everything runs inside containers.

---

## Quick Start

### 1. Clone and configure

```bash
git clone https://github.com/iqbalmbadhan/chatdoc.git
cd chatdoc
cp .env.example .env
```

Open `.env` and set at minimum:

```env
# Required — change before any internet-facing deployment
JWT_SECRET=replace-with-a-long-random-string

# At least one AI provider key (or use Ollama — see below)
OPENAI_API_KEY=sk-...
```

Everything else has working defaults for local development.

### 2. Start the platform

```bash
docker compose up -d
```

This starts PostgreSQL, Redis, Qdrant, the FastAPI backend, the Celery worker, and the Next.js frontend. The first run downloads images and builds containers — allow 3–5 minutes.

### 3. Open the app

| URL | Description |
|-----|-------------|
| http://localhost:3000 | Chat interface |
| http://localhost:3000/admin | Admin dashboard |
| http://localhost:8000/api/docs | API documentation |

**Default admin credentials**

```
Email:    admin@example.com
Password: admin123
```

Change these immediately after first login under **Admin → Settings**.

---

## Environment Variables

Copy `.env.example` to `.env`. Only `JWT_SECRET` must be changed; everything else works locally with its default.

```env
# ─── Security ─────────────────────────────────────────────────────────────────
JWT_SECRET=replace-with-a-long-random-string

# ─── Admin defaults ───────────────────────────────────────────────────────────
DEFAULT_ADMIN_EMAIL=admin@example.com
DEFAULT_ADMIN_PASSWORD=admin123

# ─── Database ─────────────────────────────────────────────────────────────────
POSTGRES_USER=chatdoc
POSTGRES_PASSWORD=chatdoc_secret
POSTGRES_DB=chatdoc

# ─── Redis ────────────────────────────────────────────────────────────────────
REDIS_PASSWORD=redis_secret

# ─── AI Providers (add whichever you use) ────────────────────────────────────
OPENAI_API_KEY=
GEMINI_API_KEY=
DEEPSEEK_API_KEY=
OPENROUTER_API_KEY=
QWEN_API_KEY=

# ─── Frontend ─────────────────────────────────────────────────────────────────
NEXT_PUBLIC_API_URL=http://localhost:8000
NEXT_PUBLIC_WS_URL=ws://localhost:8000

# ─── Optional ─────────────────────────────────────────────────────────────────
ENVIRONMENT=production
MAX_UPLOAD_SIZE_MB=50
```

---

## Features

### Chat Interface
- Streaming chat UI with source citations (filename, score, excerpt)
- Conversation history sidebar
- Dark/light mode, PWA-installable on Android/iPhone/Desktop
- Mobile-first, keyboard-safe layouts

### Document Management
- Formats: PDF, DOCX, TXT, CSV, XLSX, Markdown
- Text extraction → chunking → local embeddings → Qdrant vector index
- Per-document re-indexing with custom chunk size and embedding model
- Status tracking: pending / processing / indexed / failed

### Multi-Model AI Support

| Provider | Chat models | Embeddings |
|----------|-------------|------------|
| OpenAI | GPT-4o, GPT-4o-mini | text-embedding-3-small/large |
| Google Gemini | 1.5 Flash, 1.5 Pro | text-embedding-004 |
| DeepSeek | deepseek-chat, deepseek-r1 | — |
| OpenRouter | 100+ models | — |
| Ollama (local) | Llama3, Mistral, Qwen, … | nomic-embed-text |

### Admin Dashboard (10 sections)

| Section | Description |
|---------|-------------|
| Overview | Live stats: chats, tokens, cost, active users |
| Documents | Upload, index, manage document library |
| AI Models | Configure providers and default model |
| API Keys | Store and rotate keys (Fernet-encrypted at rest) |
| Analytics | Token usage, cost, latency trends |
| Visitors | Browser, device, country breakdown |
| Chats | Full chat history across all sessions |
| Logs | System event log |
| Settings | RAG tuning, rate limits, privacy controls |
| System | Service health: Postgres, Redis, Qdrant, Ollama |

---

## Using Ollama (local AI, no API key required)

Ollama is **not started by default** — it needs several GB of disk space and significant RAM. To enable it:

```bash
# Start with Ollama included
docker compose --profile ollama up -d

# Pull a language model and an embedding model
docker exec chatdoc-ollama ollama pull llama3
docker exec chatdoc-ollama ollama pull nomic-embed-text
```

Then set Ollama as the default provider in **Admin → AI Models**.

---

## Architecture

```
┌─────────────────────────────────────────────────────────┐
│  Browser / Mobile                                        │
│  Next.js 15  (port 3000)                                 │
└──────────────────────┬──────────────────────────────────┘
                       │ HTTP / WebSocket
┌──────────────────────▼──────────────────────────────────┐
│  FastAPI  (port 8000)                                    │
│  • REST API + SSE streaming                              │
│  • JWT auth + rate limiting                              │
│  • RAG pipeline: embed → search → inject context         │
└───────┬─────────────┬────────────────┬───────────────────┘
        │             │                │
   ┌────▼────┐  ┌─────▼─────┐  ┌──────▼──────┐
   │Postgres │  │  Qdrant   │  │   Redis     │
   │(users,  │  │(vectors)  │  │(cache,      │
   │ chats,  │  └───────────┘  │ sessions,   │
   │ docs)   │                 │ task queue) │
   └─────────┘                 └──────┬──────┘
                                      │
                               ┌──────▼──────┐
                               │   Celery    │
                               │  (document  │
                               │  indexing)  │
                               └─────────────┘
```

**RAG pipeline**

1. Document uploaded → Celery queues indexing task
2. Worker extracts text → splits into 512-token chunks (configurable)
3. `sentence-transformers/all-MiniLM-L6-v2` generates 384-dim embeddings — runs locally, no API needed
4. Vectors stored in Qdrant (cosine similarity index)
5. At chat time: query is embedded → top-K chunks retrieved → injected as context → sent to AI provider

---

## Development Setup (without Docker)

### Backend

```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

# Start external services only
docker compose up -d postgres redis qdrant

# Run the API server
uvicorn main:app --reload --port 8000
```

### Frontend

```bash
cd frontend
npm install
# create .env.local with NEXT_PUBLIC_API_URL=http://localhost:8000
npm run dev
```

### Celery worker

```bash
cd backend
source .venv/bin/activate
celery -A app.core.celery_app worker --loglevel=info --concurrency=4
```

### Database migrations

```bash
cd backend
alembic revision --autogenerate -m "describe your change"
alembic upgrade head
```

---

## Scaling

The platform is built to handle ~10,000 requests per minute:

- **PostgreSQL** connection pool: 30 persistent + 60 overflow per backend instance
- **Redis** pool: 200 connections, `allkeys-lru` eviction, 512 MB cap
- **Rate limiting**: 200 req/min per IP (adjustable in Settings)
- **Async-first**: all database, Redis, and Qdrant I/O is non-blocking
- **Background indexing**: document processing in Celery workers never blocks the API

For higher load, run multiple backend replicas behind a load balancer and scale Celery worker concurrency.

---

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Frontend | Next.js 15, TypeScript, TailwindCSS, shadcn/ui |
| State | Zustand |
| Animations | Framer Motion |
| Charts | Recharts |
| Backend | Python 3.12, FastAPI, SQLAlchemy 2.0 async |
| Validation | Pydantic v2 |
| Auth | JWT (python-jose) + bcrypt |
| Encryption | Fernet (cryptography library) |
| Vector DB | Qdrant |
| Relational DB | PostgreSQL 16 |
| Cache / Queue | Redis 7 + Celery |
| Embeddings | sentence-transformers (local) |
| Document parsing | PyMuPDF, python-docx, pandas, openpyxl |
| Container | Docker Compose |

---

## Stopping and Cleanup

```bash
# Stop all containers, keep data volumes
docker compose down

# Stop and delete all data (irreversible)
docker compose down -v
```

---

## Troubleshooting

**Port already in use**

```bash
# Find what is using port 5432 (or 6379, 6333, 8000, 3000)
sudo lsof -i :5432
```

**Backend returns 500 on first request**

The database or Redis may still be initializing. Wait a moment, then check:

```bash
docker compose ps                        # all services should show "healthy"
docker compose logs backend --tail=50
```

**Document stuck in "processing" status**

```bash
docker compose logs celery_worker --tail=50
```

**Ollama not responding**

```bash
docker exec chatdoc-ollama ollama list   # verify the model is downloaded
docker compose logs ollama --tail=30
```

---

## License

MIT
