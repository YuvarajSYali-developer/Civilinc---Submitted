# CivilInc

CivilInc is a full-stack civic infrastructure platform for complaint tracking, project coordination, analytics, GIS mapping, and role-based municipal operations.

## Overview

- `frontend/`: Vue 3, Vite, Tailwind CSS
- `backend/`: FastAPI, SQLAlchemy, Alembic
- `ai/`: ML training, model artifacts, evaluation outputs
- `data/`: raw and processed datasets
- `infra/`: deployment and Nginx configs

## Tech stack

- Frontend: Vue 3, Vue Router, Pinia, Tailwind CSS, Axios
- Backend: FastAPI, SQLAlchemy, Alembic, PostgreSQL, Redis, AsyncPG
- AI/Data: scikit-learn, XGBoost, LightGBM, pandas, NumPy

## Quick start with Docker

This is the easiest way for a new contributor to run the full app.

### Prerequisites

- Git
- Docker Desktop

### 1. Clone the repository

```bash
git clone <your-repo-url>
cd civilinc
```

### 2. Create the backend env file

```powershell
Copy-Item backend\.env.example backend\.env
```

### 3. Start the app

```bash
docker compose up --build
```

### 4. Open the services

- Frontend: `http://localhost:5173`
- Backend API: `http://localhost:8000`
- API docs: `http://localhost:8000/api/docs`

## Manual local development

Use this flow if you want to run frontend and backend separately.

### Prerequisites

- Python 3.12
- Node.js 20 or 22
- PostgreSQL 16+
- Redis 7+

### Backend

```powershell
cd backend
py -3.12 -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
Copy-Item .env.example .env
alembic upgrade head
python scripts\seed.py
uvicorn app.main:app --reload
```

Backend URLs:

- `http://127.0.0.1:8000`
- `http://127.0.0.1:8000/api/docs`

### Frontend

Open a second terminal:

```powershell
cd frontend
npm install
npm run dev
```

Frontend URL:

- `http://localhost:5173`

## Environment configuration

The backend reads settings from `backend/.env`.

Base development values:

```env
APP_ENV=development
DEBUG=true
SECRET_KEY=your-super-secret-key-change-in-production-min-64-chars
DATABASE_URL=postgresql+asyncpg://civilinc:civilinc_dev@localhost:5432/civilinc
REDIS_URL=redis://localhost:6379/0
BACKEND_CORS_ORIGINS=["http://localhost:3000","http://localhost:5173"]
```

## Database setup for manual runs

Create the local PostgreSQL user and database:

```sql
CREATE USER civilinc WITH PASSWORD 'civilinc_dev';
CREATE DATABASE civilinc OWNER civilinc;
```

## Demo accounts

- Commissioner: `commissioner@civilinc.gov.in` / `Admin@1234`
- Engineer: `engineer.roads@civilinc.gov.in` / `Engineer@1234`
- Coordinator: `coordinator@civilinc.gov.in` / `Coord@1234`
- Citizen: `citizen1@example.com` / `Citizen@1234`

## Useful commands

### Frontend

```powershell
cd frontend
npm run dev
npm run build
npm run preview
```

### Backend

```powershell
cd backend
venv\Scripts\activate
pytest
```

### Docker

```bash
docker compose up --build
docker compose down
```

## Project structure

```text
civilinc/
├── .github/
├── ai/
├── backend/
│   ├── alembic/
│   ├── app/
│   ├── scripts/
│   ├── tests/
│   ├── .env.example
│   └── requirements.txt
├── data/
├── docs/
├── frontend/
│   ├── public/
│   ├── src/
│   ├── package.json
│   ├── tsconfig.json
│   └── vite.config.ts
├── infra/
├── docker-compose.yml
└── Readme.md
```

## Contributor notes

- The landing page source is `frontend/src/content/landing-page.html`.
- Do not edit `frontend/dist/`; it is generated output.
- Keep secrets out of Git. Commit `backend/.env.example`, not `backend/.env`.
- Local environments, build artifacts, logs, and machine-specific files are ignored through `.gitignore`.

## Preparing this folder for GitHub

This project folder currently sits inside a larger Git repository on your machine. To avoid pushing unrelated files from your home directory, create a dedicated Git repo from this folder itself before pushing.

Run these commands from `civilinc/`:

```bash
git init
git add .
git commit -m "Initial clean project commit"
git branch -M main
git remote add origin <your-github-repo-url>
git push -u origin main
```

## Troubleshooting

### Frontend build issues

```powershell
cd frontend
npm install
npm run build
```

The frontend includes the required TypeScript config files for `vue-tsc`.

### Backend dependency issues

```powershell
cd backend
py -3.12 -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
```

### bcrypt issue

```powershell
pip uninstall bcrypt -y
pip install bcrypt==4.0.1
```

## Deployment references

- API deployment notes: `docs/DEPLOYMENT.md`
- Nginx production config: `infra/nginx/nginx.prod.conf`
