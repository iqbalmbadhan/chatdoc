# ChatDoc — AI Document Chatbot Platform

A production-ready, locally-hosted AI document assistant. Upload PDFs, Word docs, CSVs, and more — then chat with your knowledgebase using any AI provider, all running locally via Docker Compose.

---

## Features

### Chat Interface
- ChatGPT-style streaming chat UI with source citations
- Conversation history sidebar
- Dark/light mode + PWA installable (Android/iPhone/Desktop)
- Mobile-first, touch-optimized, keyboard-safe layouts

### Document Management
- Upload: PDF, DOCX, TXT, CSV, Markdown
- Automatic text extraction → chunking → embedding → Qdrant vector indexing
- Re-index with custom chunk size & embedding model
- Drag-and-drop upload with progress indicator

### RAG System
- Semantic similarity search via Qdrant vector database
- Configurable chunk size, overlap, and top-K retrieval
- Source attribution with filename, score, and excerpt in every response

### Multi-Model AI Support

| Provider | Chat | Embeddings |
|----------|------|------------|
| OpenAI | ✅ GPT-4o, GPT-4o-mini | ✅ text-embedding-3 |
| Google Gemini | ✅ 1.5 Flash/Pro | ✅ text-embedding-004 |
| DeepSeek | ✅ deepseek-chat, R1 | ✅ |
| OpenRouter | ✅ 100+ models | ✅ |
| Ollama (local) | ✅ Llama3, Mistral, Qwen | ✅ nomic-embed-text |

### Admin Dashboard (10 pages)
- Overview with charts and KPIs
- Document management with upload, re-index, delete
- AI provider switching with test/validate
- API key management (AES-encrypted at rest)
- Usage analytics (tokens, cost, latency charts)
- Visitor analytics (country, browser, device)
- Full chat logs with search and CSV export
- System & admin activity logs
- Platform settings (RAG config, privacy, limits)
- System health monitoring (Postgres, Redis, Qdrant, Ollama)

---

## Quick Start

### Prerequisites
- Docker & Docker Compose v2+

### 1. Clone and configure

```bash
git clone https://github.com/iqbalmbadhan/chatdoc
cd chatdoc
cp .env.example .env
# Edit .env and add at least one API key, or leave blank to use Ollama
```

### 2. Start everything

```bash
docker compose up
```

> First start: Docker pulls images and the local embedding model downloads (~400MB). Takes 2-3 min.

### 3. Open the app

| URL | Description |
|-----|-------------|
| http://localhost:3000 | Chat interface |
| http://localhost:3000/admin | Admin dashboard |
| http://localhost:8000/api/docs | API documentation |

**Default admin:** `admin@example.com` / `admin123`  
⚠️ Change password on first login (Settings page)

---

## Architecture

```
chatdoc/
├── frontend/                    # Next.js 15 + TypeScript
│   ├── app/
│   │   ├── chat/               # Public chat interface
│   │   ├── admin/              # Protected admin (10 pages)
│   │   └── login/              # Admin login
│   ├── components/             # UI, chat, admin components
│   ├── store/                  # Zustand (auth, chat state)
│   └── lib/                    # Axios API client, utils
│
├── backend/                     # Python 3.12 + FastAPI
│   ├── app/
│   │   ├── api/routes/         # REST endpoints (/auth /chat /docs ...)
│   │   ├── auth/               # JWT dependency injection
│   │   ├── core/               # Config, DB, Redis, Celery
│   │   ├── models/             # SQLAlchemy ORM (6 models)
│   │   ├── schemas/            # Pydantic v2 schemas
│   │   ├── services/           # Business logic layer
│   │   ├── providers/          # AI provider abstractions (5 providers)
│   │   ├── rag/                # Document processor, embeddings, vector store
│   │   └── websocket/          # Real-time WebSocket manager
│   ├── alembic/                # DB migrations
│   └── storage/                # Uploaded files (bind mount)
│
├── docker-compose.yml          # One-command startup
└── .env.example
```

### Service Graph

```
Browser → Frontend (3000) → Backend API (8000) → PostgreSQL
                                                → Redis ← Celery Worker
                                                → Qdrant (6333)
                                                → Ollama (11434) [optional]
```

---

## Configuration

### Key Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `JWT_SECRET` | — | **Change in production** |
| `POSTGRES_PASSWORD` | `chatdoc_secret` | PostgreSQL password |
| `REDIS_PASSWORD` | `redis_secret` | Redis auth |
| `OPENAI_API_KEY` | — | Optional: OpenAI |
| `GEMINI_API_KEY` | — | Optional: Google Gemini |
| `OPENROUTER_API_KEY` | — | Optional: OpenRouter |
| `DEEPSEEK_API_KEY` | — | Optional: DeepSeek |

### Using Ollama (Free, runs locally)

Ollama is the default provider. Enable the Ollama service:

```bash
docker compose --profile ollama up
```

Pull models (inside the container):

```bash
docker exec chatdoc-ollama ollama pull llama3
docker exec chatdoc-ollama ollama pull nomic-embed-text
```

---

## Development

### Backend local dev

```bash
cd backend
python -m venv venv && source venv/bin/activate
pip install -r requirements.txt
docker compose up postgres redis qdrant -d
uvicorn main:app --reload
```

### Frontend local dev

```bash
cd frontend
npm install
npm run dev
```

### Database migrations

```bash
cd backend
alembic revision --autogenerate -m "describe change"
alembic upgrade head
```

---

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Frontend | Next.js 15, TypeScript, TailwindCSS, shadcn/ui |
| State management | Zustand |
| Animations | Framer Motion |
| Charts | Recharts |
| Backend | Python 3.12, FastAPI, SQLAlchemy 2.0 async |
| Validation | Pydantic v2 |
| Auth | JWT (python-jose) + bcrypt |
| Vector DB | Qdrant |
| Relational DB | PostgreSQL 16 |
| Cache / Queue | Redis 7 + Celery |
| Embeddings | sentence-transformers (local, no API needed) |
| Document parsing | PyMuPDF, python-docx, pandas |
| Container | Docker Compose |
| PWA | next-pwa (service workers, offline, installable) |

---

## Security

- JWT tokens with configurable expiry (default 60min access, 7d refresh)
- API keys XOR-encrypted before storage
- bcrypt password hashing
- Role-based access control (admin / user)
- CORS configured per environment
- File MIME type validation on upload

---

## Extending

### Add a new AI provider

1. Create `backend/app/providers/myprovider_provider.py` implementing `BaseProvider`
2. Register in `backend/app/providers/registry.py`

### Add a new document type

1. Add extractor to `DocumentProcessor` in `backend/app/rag/document_processor.py`
2. Add MIME type to `SUPPORTED_TYPES`
3. Update the frontend dropzone `accept` config

### Future SaaS add-ons (architecture ready)

- **Stripe subscriptions**: Add `plan` field to User model, add billing routes
- **Multi-tenant workspaces**: Add `workspace_id` FK to all data models
- **WhatsApp/Telegram bots**: New routers consuming `ChatService`
- **Embeddable widget**: Public CORS-open chat endpoint + React snippet
- **Voice chat**: WebRTC + Whisper transcription → ChatService

---

## License

MIT