# NewsAnalysisV1 — Frontend

React 19 + Vite 8 SPA for the NewsAnalysisV1 platform.

## Stack

| Category | Technology |
|---|---|
| Framework | React 19 + Vite 8 |
| Routing | React Router DOM 7 |
| UI | Material-UI (MUI) v9 |
| HTTP | Axios with JWT Bearer interceptors |

## Pages

| Page | Route | Description |
|---|---|---|
| Login | `/login` | Email/password login |
| Signup | `/signup` | New user registration |
| Analysis | `/` | Ad-hoc NLP analysis (entities, summary, relations) |
| Pipeline | `/pipeline` | Article ingestion, pipeline trigger & step-level status monitor |
| Admin | `/admin` | RBAC console — manage users, roles, and page access |

Route access is controlled by the `pages` array returned on login. Each route requires the matching page `slug` to be present in the user's page list.

## Development

```bash
npm install
npm run dev       # http://localhost:5173
npm run build
npm run preview
```

Set `VITE_API_BASE_URL` in `.env.local` to point at a non-default backend:

```env
VITE_API_BASE_URL=http://localhost:8000
```

See the [root README](../README.md) for full project documentation.
