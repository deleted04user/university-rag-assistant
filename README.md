# University RAG Assistant

![FastAPI](https://img.shields.io/badge/FastAPI-0.115-009688?logo=fastapi&logoColor=white)
![Python](https://img.shields.io/badge/Python-3.10%2B-3776AB?logo=python&logoColor=white)
![PostgreSQL](https://img.shields.io/badge/PostgreSQL-16-4169E1?logo=postgresql&logoColor=white)
![License](https://img.shields.io/badge/license-MIT-22c55e)

A full-stack French university portal with role-based access, academic data management, and a lightweight local retrieval-augmented assistant. It runs without a paid AI API and can use SQLite for a zero-configuration demo or PostgreSQL through Docker.

## Features

- Student registration and JWT authentication
- Course catalogue and timetable browsing
- Admin dashboard for users, courses, schedules, and university information
- Hybrid question-answering pipeline with deterministic intents and local TF-IDF retrieval
- Rebuildable knowledge index based on live database content
- Responsive vanilla JavaScript frontend and interactive FastAPI documentation

## Architecture

```mermaid
flowchart TD
    UI[Web portal] --> API[FastAPI REST API]
    API --> AUTH[JWT and role checks]
    API --> DB[(SQLite or PostgreSQL)]
    API --> CHAT[Hybrid assistant]
    CHAT --> NLP[Intent rules]
    CHAT --> RAG[TF-IDF retrieval]
    RAG --> DB
```

## Tech stack

| Layer | Technology |
|---|---|
| Frontend | HTML5, CSS3, vanilla JavaScript |
| API | FastAPI, Pydantic, Uvicorn |
| Persistence | SQLAlchemy, SQLite / PostgreSQL |
| Authentication | JWT, Passlib, role-based authorization |
| Retrieval | scikit-learn TF-IDF, cosine similarity, Joblib |

## Quick start

### 1. Backend

```bash
cd backend
python -m venv .venv
source .venv/bin/activate       # Linux/macOS
# .venv\Scripts\activate        # Windows
pip install -r requirements.txt
cp .env.example .env
uvicorn app.main:app --reload --port 8001
```

### 2. Frontend

In a second terminal:

```bash
cd frontend
python -m http.server 8080
```

Open `http://127.0.0.1:8080`. API documentation is available at `http://127.0.0.1:8001/docs`.

On Windows, `start_project.ps1` starts both services after the backend environment has been created.

## Demo accounts

| Role | Email | Password |
|---|---|---|
| Student | `student@univ-demo.fr` | `student123` |
| Administrator | `admin@univ-demo.fr` | `admin123` |

These accounts are development fixtures. Replace them and set a strong `SECRET_KEY` before deployment.

## PostgreSQL option

```bash
docker compose up -d
```

Then set `DATABASE_URL=postgresql://univ:univ@127.0.0.1:5432/univ` in `backend/.env`.

## Repository structure

```text
.
├── backend/
│   ├── app/              # API, models, routers, auth, and retrieval services
│   ├── requirements.txt
│   └── .env.example
├── frontend/             # Static web application
├── docker-compose.yml    # Optional PostgreSQL service
└── Pfa_2.pdf             # Academic project brief/report
```

## Author

**Oussama Oulkaid** — Computer Science Engineering student at EMSI Casablanca.

## License

Released under the [MIT License](LICENSE).
