# NirmaanAI - construction site PPE monitoring

Upload a site video. A YOLO model checks hardhats, safety vests and masks once per second of footage.
You get a compliance percentage, a risk level, a log of violations with timestamps, and snapshots of the worst moments.

```
React + Vite (frontend)  ->  FastAPI (backend)  ->  SQLite / PostgreSQL
                                  |
                          background worker -> YOLO (model from Hugging Face)
```

## Run locally

**Backend** (Python 3.10-3.13)
```bash
cd backend
python -m venv .venv && source .venv/bin/activate      # Windows: .venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env                                    # optional, defaults work
uvicorn app.main:app --reload
```
API docs: http://localhost:8000/docs. The model downloads from Hugging Face on the first analysis.

**Frontend** (Node 18+)
```bash
cd frontend
npm install
cp .env.example .env        # VITE_API_URL=http://127.0.0.1:8000
npm run dev
```
Open http://localhost:5173.

**Everything with Docker:** `docker compose up --build` (Postgres + API + frontend).

**Tests:** `cd backend && pip install -r requirements-dev.txt && pytest` (uses a fake model, so no download).

## API

| Method | Path | What it does |
|---|---|---|
| POST | `/api/vision/analyze` | Upload a video, returns `{id}` immediately (202) |
| GET | `/api/vision/analyses` | List analyses |
| GET | `/api/vision/analyses/{id}` | Status, progress, results, incidents, snapshots |
| DELETE | `/api/vision/analyses/{id}` | Delete an analysis and its snapshots |
| GET | `/api/incidents` | Violations, filter by `analysis_id` and `type` |
| GET | `/api/risk/{id}` | Risk score, reasons, recommendations |
| GET | `/api/dashboard/summary` | Totals, trend, risk distribution |

## How the numbers work

- One frame is analyzed every `SAMPLE_EVERY_SECONDS` (default 1.0).
- Compliance = `1 - violations / (workers x required PPE items)`, summed over all analyzed frames. A violation count per item is capped at the number of workers in that frame. Choose required items with `REQUIRED_PPE`.
- Worker counts are per frame (peak and average). Workers are **not tracked across frames**, so "unique people" is not reported.
- Risk score (0-100) = 60% non-compliance + 25% share of frames with a violation + 15% worst frame. Levels: low < 20, medium < 45, high < 70, critical.

## Security notes

Fixed from the original version: client filenames are never used on disk (random names), file type/size/duration are enforced on the server, uploaded videos are deleted after analysis, analysis runs in a background worker instead of blocking the API, upload queue is capped, CORS is configurable.

Still your job before going public:
- **There is no login.** Anyone who can reach the API can upload videos and use your CPU. Put it behind auth or a private network.
- **The model file is a pickle (`.pt`).** Loading a tampered file can run code. Set `MODEL_REVISION` to a commit hash you have reviewed, or host the weights yourself.
- Tables are created on startup. For schema changes later, add Alembic migrations.
- The job queue lives in memory: a restart marks running jobs as failed (the user re-uploads).

## Deploy on Render

`render.yaml` is a Blueprint: Postgres, a Docker web service for the API, and a static site for the frontend.
After the first deploy, set `VITE_API_URL` (frontend) and `CORS_ORIGINS` (API) to each other's URLs, then redeploy the frontend.
The API needs about 2 GB RAM for YOLO; check Render's current plans and pricing.

## Layout

```
backend/app/   main.py, config.py, database.py, models.py, schemas.py
               routes/    vision, incidents, risk, dashboard
               services/  video_analyzer, risk, jobs, storage
backend/tests/ API tests
frontend/src/  pages/ (Dashboard, Analyze, History, AnalysisDetail), components/, services/api.ts
```
