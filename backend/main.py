# backend/main.py

import uuid
import datetime
import asyncio

from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware

from sqlalchemy import select, text
from db import langgraph_semaphore, SessionLocal
from ingestor import Ingestor
from agents.extractor import extractor_agent
from agents.dictionary_agent import dictionary_agent
from agents.analyst_agent import analyst_agent
from models import Metric  # SQLAlchemy ORM model for metrics :contentReference[oaicite:0]{index=0}

app = FastAPI(title="Autonomous Analytics MVP")

# CORS setup (allow all origins for simplicity; adjust in prod)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# ————————————————————————————————————————————————
# In-memory status store: { run_id: { table: { agent: status_dict } } }
# ————————————————————————————————————————————————
ingest_runs: dict[str, dict[str, dict[str, dict]]] = {}

def _now_iso() -> str:
    return datetime.datetime.utcnow().isoformat()

def init_run(run_id: str, tables: list[str]):
    """Initialize all statuses to 'pending'."""
    agents = ["extractor", "dictionary", "analyst"]
    ingest_runs[run_id] = {
        tbl: {
            ag: {"status": "pending", "started_at": None, "finished_at": None, "error": None}
            for ag in agents
        }
        for tbl in tables
    }

def update_status(run_id: str, table: str, agent: str, status: str, error: str = None):
    rec = ingest_runs[run_id][table][agent]
    rec["status"] = status
    if status == "running":
        rec["started_at"] = _now_iso()
    if status in ("done", "failed"):
        rec["finished_at"] = _now_iso()
    if error:
        rec["error"] = error

# ————————————————————————————————————————————————
# 1. Ingest endpoint with run_id
# ————————————————————————————————————————————————
@app.post("/ingest/")
async def ingest_endpoint(
    mode: str = Form(...),                      # "create" / "replace" / "append"
    table_name: str = Form(None),               # existing table name
    file: UploadFile = File(...),
    user: str = Form("anonymous")
):
    # 1. Ingest file
    content = await file.read()
    tables = await Ingestor.ingest_file(content, file.filename, mode, target_table=table_name, user=user)

    # 2. Create a new run_id and init statuses
    run_id = str(uuid.uuid4())
    init_run(run_id, tables)

    # 3. Launch the agents chain for each table
    async def run_pipeline(tbl: str):
        async with langgraph_semaphore:
            for agent_name, agent_func in [
                ("extractor", extractor_agent),
                ("dictionary", dictionary_agent),
                ("analyst", analyst_agent),
            ]:
                update_status(run_id, tbl, agent_name, "running")
                try:
                    await agent_func(tbl)
                    update_status(run_id, tbl, agent_name, "done")
                except Exception as e:
                    update_status(run_id, tbl, agent_name, "failed", str(e))
                    break

    for t in tables:
        asyncio.create_task(run_pipeline(t))

    return JSONResponse({"status": "started", "run_id": run_id, "tables": tables})

# ————————————————————————————————————————————————
# 2. Status endpoint
# ————————————————————————————————————————————————
@app.get("/ingest/{run_id}/status")
async def ingest_status(run_id: str):
    if run_id not in ingest_runs:
        raise HTTPException(status_code=404, detail="Run ID not found")
    return {"run_id": run_id, "status": ingest_runs[run_id]}

# ————————————————————————————————————————————————
# 3. Metrics endpoints
# ————————————————————————————————————————————————

@app.get("/metrics/")
async def list_metrics():
    """Return a list of all defined metrics (id, name, viz hint, etc.)."""
    async with SessionLocal() as session:
        result = await session.execute(select(Metric))
        metrics = result.scalars().all()

    # Serialize ORM objects to plain dicts
    return [
        {
            "id": m.id,
            "name": m.metric_name,
            "sql_definition": m.sql_definition,
            "viz": m.viz_hint,
            "importance_score": m.importance_score,
            "tags": m.tags,
        }
        for m in metrics
    ]

@app.get("/metric/{metric_id}")
async def run_metric(metric_id: int):
    """
    Execute the SQL for a specific metric and return its data and viz hint.
    """
    async with SessionLocal() as session:
        metric = await session.get(Metric, metric_id)
        if not metric:
            raise HTTPException(status_code=404, detail="Metric not found")

        try:
            # Run the metric's SQL definition
            result = await session.execute(text(metric.sql_definition))
            rows = result.fetchall()
            cols = result.keys()
            data = [dict(zip(cols, row)) for row in rows]
        except Exception as e:
            raise HTTPException(status_code=400, detail=f"Error executing metric SQL: {e}")

    return {
        "data": data,
        "viz": metric.viz_hint
    }
