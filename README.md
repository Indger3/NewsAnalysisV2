# NewsAnalysisV1

AI-powered news article analysis with Named Entity Recognition. Paste a news article, authenticate, and get structured NLP analysis powered by a custom-trained spaCy model.

**Architecture:** React SPA → FastAPI backend → spaCy NLP pipeline

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
├── backend/
│   ├── app/
│   │   ├── main.py                     # FastAPI app entry point
│   │   ├── settings.py                 # Config & environment variables
│   │   ├── celery_main.py              # Celery worker config
│   │   ├── routes/
│   │   │   ├── auth_routes.py          # Login endpoint
│   │   │   └── nlp_routes.py           # Entity extraction endpoint
│   │   ├── bl/
│   │   │   └── entity_ops.py           # NER business logic
│   │   ├── utils/
│   │   │   ├── auth.py                 # JWT creation & validation
│   │   │   └── app_logger.py           # Loguru setup
│   │   ├── tasks/
│   │   │   └── news_analysis_tasks.py  # Celery async tasks
│   │   └── static/
│   │       └── improved_modelv2/       # Custom spaCy NER model
│   └── requirements.txt
└── frontend/
    ├── src/
    │   ├── pages/
    │   │   ├── LoginPage.jsx           # Auth form
    │   │   └── AnalysisPage.jsx        # Main NLP analysis interface
    │   ├── components/
    │   │   ├── ArticlePanel.jsx        # Article text input + analyze button
    │   │   ├── ResultsPanel.jsx        # Results container
    │   │   └── results/                # EntitiesCard, SummaryCard, etc.
    │   ├── context/
    │   │   └── AuthContext.jsx         # Global auth state & token management
    │   └── api/
    │       ├── rest_client.js          # Axios instance with auth interceptors
    │       ├── auth.api.js             # Login API calls
    │       └── nlp.api.js              # NLP analysis API calls
    └── package.json
```

---

## API Endpoints

Base URL prefix: `/v1`

| Method | Path | Auth | Description |
|---|---|---|---|
| GET | `/` | No | Health check / welcome |
| POST | `/auth/login` | No | Login and receive JWT bearer token |
| POST | `/entities` | Bearer | Extract named entities from article text |

### Auth Flow
```
POST /v1/auth/login
Body: { "username": "admin", "password": "password" }

Response: { "access_token": "<jwt>", "token_type": "bearer" }
```
Token is valid for 8 hours. Include it on all protected requests:
```
Authorization: Bearer <access_token>
```

### Entity Extraction
```
POST /v1/entities
Authorization: Bearer <token>
Body: { "text": "<article text>" }

Response: { "entities": [{ "text": "...", "label": "..." }, ...] }
```

---

## Frontend Pages

| Page | Route | Access | Description |
|---|---|---|---|
| Login | `/login` | Public | Username/password form; redirects to analysis on success |
| Analysis | `/` | Protected | Article input + NER results; auto-redirects to `/login` if unauthenticated |

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

### Celery Worker (optional)
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

This starts the FastAPI backend (with debugger attached) and the Vite dev server simultaneously. The frontend will open in your browser automatically.

Individual configurations are also available:
- **Python Debugger: FastAPI** — backend only, with breakpoint support
- **React: Vite Dev Server** — frontend only
