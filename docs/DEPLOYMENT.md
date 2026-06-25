# CivilInc 

## Prerequisites
- Docker 24+ & Docker Compose v2
- PostgreSQL 16
- Redis 7
- Node 20 (frontend build)
- Python 3.12 (backend)

## Quick Start (Local)

```bash
# 1. Clone and configure
git clone https://github.com/your-org/civilinc.git
cd civilinc
cp backend/.env.example backend/.env
# Edit backend/.env with your SECRET_KEY and database credentials

# 2. Start infrastructure
docker compose up db redis -d

# 3. Run migrations
cd backend
pip install -r requirements.txt
alembic upgrade head

# 4. Seed data
python scripts/seed.py

# 5. Train AI models (first time only)
cd ../ai/pipelines
python etl_master.py      # Generate datasets
python train_all.py       # Train all 7 AI systems

# 6. Start backend
cd ../../backend
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload

# 7. Start frontend (new terminal)
cd ../frontend
npm install
npm run dev
```

Access at: http://localhost:5173

## Production (Docker Compose)

```bash
docker compose up -d
```

## Railway (Backend)

```bash
railway login
railway init
railway add postgresql
railway add redis
railway up
```

Environment variables to set in Railway:
- `DATABASE_URL` (auto-set by Railway PostgreSQL addon)
- `REDIS_URL` (auto-set by Railway Redis addon)
- `SECRET_KEY` (generate with `openssl rand -base64 64`)
- `APP_ENV=production`
- `BACKEND_CORS_ORIGINS=["https://your-vercel-app.vercel.app"]`

## Vercel (Frontend)

```bash
cd frontend
npm install -g vercel
vercel --prod
```

Environment variables in Vercel:
- `VITE_API_URL=https://your-railway-backend.up.railway.app`
- `VITE_WS_URL=wss://your-railway-backend.up.railway.app`

## Alembic Migrations

```bash
# Create new migration
alembic revision --autogenerate -m "description"

# Apply migrations
alembic upgrade head

# Rollback one step
alembic downgrade -1
```

## Default Credentials

| Role | Email | Password |
|---|---|---|
| Commissioner | commissioner@civilinc.gov.in | Admin@1234 |
| Engineer | engineer.roads@civilinc.gov.in | Engineer@1234 |
| Coordinator | coordinator@civilinc.gov.in | Coord@1234 |
| Citizen | citizen1@example.com | Citizen@1234 |

## Health Checks

- Backend: `GET /health`
- Detailed: `GET /health/detailed`
- AI models: `GET /api/v1/ai/health`
- Metrics: `GET /metrics` (Prometheus format)
- API docs: `GET /api/docs`