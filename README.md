# NewsAnalysisV1

AI-powered news article analysis pipeline. Ingest articles, trigger an async NLP workflow, and get structured analysis — entity recognition, summarization, and relation extraction — powered by custom-trained spaCy and transformer models. Includes role-based access control (RBAC) and an admin console.

**Architecture:** React SPA → FastAPI backend → Celery workers → spaCy NLP pipeline → PostgreSQL

---

## Tech Stack

### Backend
| Category | Technology |
|---|---|
| Framework | FastAPI 0.136 |
| Server | Uvicorn / Gunicorn |
| NLP | spaCy 3.8 (custom model `improved_modelv2`) |
| ML | HuggingFace Transformers, PyTorch |
| Auth | JWT via python-jose + passlib/bcrypt |
| Task Queue | Celery + RabbitMQ |
| Database | PostgreSQL + SQLAlchemy |
| Logging | Loguru |

### Frontend
| Category | Technology |
|---|---|
| Framework | React 19 + Vite 8 |
| Routing | React Router DOM 7 |
| UI | Material-UI (MUI) v9 |
| HTTP | Axios with JWT Bearer interceptors |

---

## Project Structure

```
NewsAnalysisV1/
├── .env
├── .git/
├── .gitignore
├── .venv/
├── .vscode/
├── README.md
├── backend/
│   ├── .gitignore
│   ├── requirements.txt
│   └── app/
│       ├── celery_main.py                   # Celery worker config
│       ├── main.py                          # FastAPI app entry point
│       ├── settings.py                      # Config & environment variables
│       ├── bl/
│       │   ├── batch_analysis_ops.py        # Batch analysis orchestration
│       │   ├── entity_ops.py                # NER business logic
│       │   ├── metadata_ops.py              # Metadata extraction/ops
│       │   ├── normalization_ops.py         # Normalization helpers
│       │   ├── relation_ops.py              # Relation extraction logic
│       │   ├── summary_ops.py               # Summarization logic
│       │   └── taxonomy_ops.py              # Taxonomy classification ops
│       ├── config/
│       │   ├── normalization_config.json    # Normalization rules/config
│       │   ├── relations.yaml               # Relation definitions
│       │   └── workflow.json                # Pipeline/workflow definition
│       ├── dal/
│       │   ├── admin_dal.py                 # RBAC admin DB access
│       │   ├── app_db.py                    # SQLAlchemy session / DB connection
│       │   ├── db_models.py                 # ORM models
│       │   └── user_dal.py                  # User DB access
│       ├── routes/
│       │   ├── admin_routes.py              # Admin API endpoints
│       │   ├── auth_routes.py               # Auth endpoints (signup/login)
│       │   ├── ingest_routes.py             # Article ingest endpoints
│       │   ├── nlp_routes.py                # NLP endpoints (entities/summarize/relations)
│       │   └── pipeline_routes.py           # Pipeline trigger/status/results endpoints
│       ├── static/
│       │   ├── improved_modelv2/
│       │   │   ├── config.cfg               # Model config
│       │   │   ├── meta.json                # Model metadata
│       │   │   ├── tokenizer                # Tokenizer resources
│       │   │   ├── ner/
│       │   │   │   ├── cfg                  # NER config
│       │   │   │   ├── model                # NER model files
│       │   │   │   └── moves                # NER state/moves
│       │   │   └── vocab/
│       │   │       ├── key2row
│       │   │       ├── lookups.bin
│       │   │       ├── strings.json
│       │   │       ├── vectors
│       │   │       └── vectors.cfg
│       │   └── taxonomy_model/
│       │       ├── taxonomy_model_v2.pkl    # Serialized taxonomy model
│       │       └── taxonomy_model_v2.py     # Taxonomy model wrapper
│       ├── tasks/
│       │   ├── news_analysis_tasks.py       # Celery NLP tasks
│       │   └── pipeline_tasks.py            # Celery pipeline orchestration tasks
│       └── utils/
│           ├── app_logger.py                # Loguru setup
│           └── auth.py                      # JWT helpers & RBAC guards
└── frontend/
    ├── .gitignore
    ├── README.md
    ├── eslint.config.js
    ├── index.html
    ├── node_modules/
    ├── package-lock.json
    ├── package.json
    ├── public/
    ├── vite.config.js
    └── src/
        ├── App.css
        ├── App.jsx                          # Root React component
        ├── index.css
        ├── main.jsx                         # React app entry
        ├── settings.js
        ├── theme.js
        ├── api/
        │   ├── admin.api.js                 # Admin API client
        │   ├── auth.api.js                  # Auth API client
        │   ├── nlp.api.js                   # NLP API client
        │   └── rest_client.js               # Axios instance with auth interceptors
        ├── assets/
        ├── components/
        │   ├── AnalysisSettings.jsx         # Analysis configuration controls
        │   ├── ArticlePanel.jsx             # Article input + analyze button
        │   ├── ResultsPanel.jsx             # Results container / cards layout
        │   ├── pipeline/
        │   │   ├── ArticleDetailDrawer.jsx
        │   │   └── ArticleStatusTable.jsx
        │   └── results/
        │       ├── EntitiesCard.jsx
        │       ├── MetadataCard.jsx
        │       ├── NormalizationCard.jsx
        │       ├── RelationshipsCard.jsx
        │       ├── SectionCard.jsx
        │       ├── SummaryCard.jsx
        │       └── TaxonomyCard.jsx
        ├── contexts/
        │   └── AuthContext.jsx               # Global auth state & token handling
        ├── pages/
        │   ├── AdminPage.jsx
        │   ├── AnalysisPage.jsx
        │   ├── LoginPage.jsx
        │   ├── PipelinePage.jsx
        │   └── SignupPage.jsx
        ├── router/
        │   └── index.jsx                     # Routes with RBAC guards
        └── utils/
            └── text.js                       # Text helper utilities
```

---

## API Endpoints

Base URL prefix: `/v1`

### Auth

| Method | Path | Auth | Description |
|---|---|---|---|
| POST | `/auth/signup` | No | Register a new user account |
| POST | `/auth/login` | No | Login and receive JWT bearer token |

#### Signup
```
POST /v1/auth/signup
Body: { "email": "user@example.com", "password": "secret", "name": "Alice" }

Response 201: { "id": "<uuid>", "email": "user@example.com", "name": "Alice" }
```

#### Login
```
POST /v1/auth/login
Body: { "email": "user@example.com", "password": "secret" }

Response: {
  "access_token": "<jwt>",
  "token_type": "bearer",
  "user": {
    "id": "<uuid>",
    "email": "user@example.com",
    "name": "Alice",
    "pages": [{ "slug": "analysis", "label": "Analysis", "icon": "..." }, ...]
  }
}
```
Token is valid for 8 hours. Include it on all protected requests:
```
Authorization: Bearer <access_token>
```
The `pages` array in the login response drives client-side route access — the frontend only shows pages the user's roles grant.

---

### NLP (ad-hoc, no persistence)

| Method | Path | Auth | Description |
|---|---|---|---|
| POST | `/entities` | Bearer | Extract named entities from article text |
| POST | `/summarize` | Bearer | Summarize article text |
| POST | `/relations` | Bearer | Extract entity relationships as triples |
| POST | `/metadata` | Bearer | Extract article metadata (planned) |
| POST | `/taxonomy` | Bearer | Classify into taxonomy categories (planned) |

```
POST /v1/entities
Body: { "text": "<article text>" }
Response: { "entities": [{ "text": "...", "label": "..." }, ...] }

POST /v1/summarize
Body: { "text": "<article text>", "n": 3 }   // n = number of sentences (optional)

POST /v1/relations
Body: { "text": "<article text>", "confidence": 0.6 }
Response: { "triples": [{ "subject": "...", "predicate": "...", "object": "..." }, ...] }
```

---

### Ingest

| Method | Path | Auth | Description |
|---|---|---|---|
| POST | `/ingest/article` | Bearer | Persist an article to the database |

```
POST /v1/ingest/article
Body: {
  "source": "Reuters",
  "url": "https://...",
  "body": "<full article text>",
  "title": "...",             // optional
  "published_at": "...",      // optional ISO-8601
  "language": "en",           // optional
  "authors": ["Jane Smith"]   // optional
}

Response: { "article_id": 42, "word_count": 512 }
```
Duplicate URLs return `{ "error": "article with this URL already exists" }`.

---

### Pipeline

| Method | Path | Auth | Description |
|---|---|---|---|
| GET | `/pipeline/articles` | Bearer | List all ingested articles with latest run status |
| GET | `/pipeline/articles/{id}` | Bearer | Get article body and metadata |
| POST | `/pipeline/articles/{id}/trigger` | Bearer | Trigger async NLP pipeline for an article |
| GET | `/pipeline/articles/{id}/status` | Bearer | Poll pipeline run status and step-level detail |
| GET | `/pipeline/articles/{id}/results` | Bearer | Get persisted analysis results (summary, entities, relationships) |

#### Trigger pipeline
```
POST /v1/pipeline/articles/42/trigger

Response: {
  "article_id": 42,
  "run_id": 7,
  "status": "running",
  "steps_queued": 3
}
```
Re-triggering clears prior results and starts a fresh workflow run. Returns `409` if already running.

#### Poll status
```
GET /v1/pipeline/articles/42/status

Response: {
  "article_id": 42,
  "pipeline_status": "running",
  "latest_run": {
    "run_id": 7,
    "workflow_name": "news_analysis",
    "status": "running",
    "triggered_at": "...",
    "steps": [
      { "step_order": 1, "step_name": "entity_extraction", "status": "completed", ... },
      { "step_order": 2, "step_name": "summarization", "status": "running", ... },
      ...
    ]
  }
}
```

#### Get results
```
GET /v1/pipeline/articles/42/results

Response: {
  "article_id": 42,
  "summary": "...",
  "entities": [{ "entity": "...", "label": "ORG" }, ...],
  "relationships": [{ "subj": "...", "verb": "...", "obj": "...", "confidence": 0.87 }, ...]
}
```

---

### Admin (requires admin role)

| Method | Path | Description |
|---|---|---|
| GET | `/admin/users` | List all users with roles and page access |
| PUT | `/admin/users/{id}` | Activate or deactivate a user |
| PUT | `/admin/users/{id}/roles` | Assign roles to a user |
| GET | `/admin/roles` | List all roles with assigned pages |
| POST | `/admin/roles` | Create a new role |
| DELETE | `/admin/roles/{id}` | Delete a role |
| PUT | `/admin/roles/{id}/pages` | Assign pages to a role |
| GET | `/admin/pages` | List all registered pages |
| POST | `/admin/pages` | Create a new page |
| DELETE | `/admin/pages/{id}` | Delete a page |

---

## Frontend Pages

| Page | Route | Access | Description |
|---|---|---|---|
| Login | `/login` | Public | Email/password login; redirects to `/` on success |
| Signup | `/signup` | Public | New user registration form |
| Analysis | `/` | `analysis` page role | Ad-hoc article text input with live NLP results |
| Pipeline | `/pipeline` | `pipeline` page role | Article pipeline monitor — ingest, trigger, track step status, view results |
| Admin | `/admin` | `admin` page role | RBAC console — manage users, roles, and page access |
| Unauthorized | `/unauthorized` | Any authenticated | Shown when a user lacks the required page role |

Page access is enforced on both the server (JWT + role check) and the client (route guard reads `user.pages` from the login response).

---

## RBAC Model

```
Users ──< user_roles >── Roles ──< role_pages >── Pages
```

- **Users** are assigned one or more **Roles**.
- **Roles** grant access to one or more **Pages** (identified by `slug`).
- The login response includes the user's effective page list; the frontend router uses it to permit or deny navigation.
- Admin endpoints require a role named `admin` (enforced via `require_admin` dependency).

---

## Environment Variables

### Backend
Create a `.env` file in `/backend` or export these in your shell:

```env
APP_DB_CONN=postgresql://user:password@localhost:5432/news_analysis
SECRET_KEY=your-secret-key-here
ACCESS_TOKEN_EXPIRE_MINUTES=480
DEMO_USERNAME=admin
DEMO_PASSWORD=password
```

### Frontend
Create `.env.local` in `/frontend` to override defaults:

```env
VITE_API_BASE_URL=http://localhost:8000
```

---

## How to Run

**Prerequisites:** Python 3.10+, Node 18+, PostgreSQL, RabbitMQ

### Backend
```bash
cd backend
python -m venv .venv
source .venv/bin/activate       # Windows: .venv\Scripts\activate
pip install -r requirements.txt
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

API docs available at [http://localhost:8000/docs](http://localhost:8000/docs)

### Frontend
```bash
cd frontend
npm install
npm run dev
```

App available at [http://localhost:5173](http://localhost:5173)

### Celery Worker
Required for the async pipeline to execute NLP steps:
```bash
cd backend
celery -A app.celery_main worker --loglevel=info
```

---

## Running in VSCode

The repo includes a `.vscode/launch.json` with configurations for both servers and a compound launch:

1. Open the repo root in VSCode
2. Open the **Run & Debug** panel (`Ctrl+Shift+D` / `Cmd+Shift+D`)
3. Select **"Full Stack: FastAPI + React"** from the dropdown
4. Press **F5**

This starts the FastAPI backend (with debugger attached) and the Vite dev server simultaneously.

Individual configurations are also available:
- **Python Debugger: FastAPI** — backend only, with breakpoint support
- **React: Vite Dev Server** — frontend only
