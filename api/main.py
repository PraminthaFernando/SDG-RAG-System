from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect, BackgroundTasks
from pathlib import Path
from fastapi.middleware.cors import CORSMiddleware
import asyncio
from sqlalchemy import text
import boto3
import os

# 🔥 DB IMPORTS
from RDS.database import SessionLocal
from RDS.crud_metadata import get_metadata
from RDS.crud_score import get_project_score as get_score_from_db
from RDS.crud_insights import (
    get_forestry_score_distribution,
    get_forestry_sdg_distribution,
    get_forestry_summary,
    get_forestry_sdg_avg,
    get_forestry_top_projects,
    get_forestry_emission_vs_score,
    get_forestry_category_performance,

    get_renewable_score_distribution,
    get_renewable_sdg_distribution,
    get_renewable_summary,
    get_renewable_sdg_avg,
    get_renewable_top_projects,
    get_renewable_emission_vs_score,
    get_renewable_category_performance,
    get_renewable_map_data,

    get_forestry_map_data
)

from fastapi import Depends
from sqlalchemy.orm import Session
from RDS.database import get_db


app = FastAPI()

# =========================================================
# 🔥 S3 CLIENT
# =========================================================
s3 = boto3.client(
    "s3",
    aws_access_key_id=os.getenv("AWS_ACCESS_KEY_ID"),
    aws_secret_access_key=os.getenv("AWS_SECRET_ACCESS_KEY"),
    region_name=os.getenv("AWS_REGION"),
)

BUCKET = os.getenv("AWS_BUCKET_NAME")

# =========================================================
# 🔥 CORS
# =========================================================
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# =========================================================
# 🔥 ROOT
# =========================================================
@app.get("/")
def root():
    return {"message": "API is running 🚀"}

# =========================================================
# 🔥 HELPER: DETECT SOURCE
# =========================================================
def detect_source(project_id: str):
    if project_id.startswith("VCS_"):
        return "verra"

    if project_id.startswith("GS_"):
        return "gs"

    return None

# =========================================================
# 🔥 RENEWABLE SUMMARY
# =========================================================
@app.get("/insights/renewable/summary")
def renewable_summary(db: Session = Depends(get_db)):
    return get_renewable_summary(db)

# =========================================================
# 🔥 RENEWABLE SCORE DISTRIBUTION
# =========================================================
@app.get("/insights/renewable/score-distribution")
def renewable_score_distribution(db: Session = Depends(get_db)):
    data = get_renewable_score_distribution(db)

    return {
        "sector": "renewable",
        "distribution": data
    }

# =========================================================
# 🔥 RENEWABLE SDG DISTRIBUTION
# =========================================================
@app.get("/insights/renewable/sdg-distribution")
def renewable_sdg_distribution(db: Session = Depends(get_db)):
    data = get_renewable_sdg_distribution(db)

    return {
        "sector": "renewable",
        "distribution": data
    }

# =========================================================
# 🔥 RENEWABLE SDG AVG
# =========================================================
@app.get("/insights/renewable/sdg-average")
def renewable_sdg_avg(db: Session = Depends(get_db)):
    return get_renewable_sdg_avg(db)

# =========================================================
# 🔥 RENEWABLE TOP PROJECTS
# =========================================================
@app.get("/insights/renewable/top-projects")
def renewable_top_projects(db: Session = Depends(get_db)):
    return get_renewable_top_projects(db)

# =========================================================
# 🔥 RENEWABLE EMISSION VS SCORE
# =========================================================
@app.get("/insights/renewable/emission-vs-score")
def renewable_emission_vs_score(db: Session = Depends(get_db)):
    return get_renewable_emission_vs_score(db)

# =========================================================
# 🔥 RENEWABLE CATEGORY PERFORMANCE
# =========================================================
@app.get("/insights/renewable/category-performance")
def renewable_category_performance(db: Session = Depends(get_db)):
    return get_renewable_category_performance(db)

# =========================================================
# 🔥 RENEWABLE MAP
# =========================================================
@app.get("/insights/renewable/map")
def renewable_map(db: Session = Depends(get_db)):
    return get_renewable_map_data(db)

# =========================================================
# 🔥 METADATA
# =========================================================
@app.get("/project/{project_id}")
def get_project_metadata(project_id: str):

    db = SessionLocal()

    try:
        source = detect_source(project_id)

        if source == "verra":
            result = get_metadata(db, project_id)

        elif source == "gs":
            result = db.execute(text("""
                SELECT *
                FROM gs_metadata
                WHERE project_id = :pid
            """), {"pid": project_id}).mappings().fetchone()

        else:
            result = None

        if not result:
            raise HTTPException(status_code=404, detail="Project not found")

        return dict(result)

    finally:
        db.close()

# =========================================================
# 🔥 FORESTRY SUMMARY
# =========================================================
@app.get("/insights/forestry/summary")
def forestry_summary(db: Session = Depends(get_db)):
    return get_forestry_summary(db)

# =========================================================
# 🔥 FORESTRY MAP
# =========================================================
@app.get("/insights/forestry/map")
def forestry_map():

    db = SessionLocal()

    try:
        data = get_forestry_map_data(db)
        return data

    finally:
        db.close()

# =========================================================
# 🔥 FORESTRY SDG AVG
# =========================================================
@app.get("/insights/forestry/sdg-average")
def forestry_sdg_avg(db: Session = Depends(get_db)):
    return get_forestry_sdg_avg(db)

# =========================================================
# 🔥 FORESTRY TOP PROJECTS
# =========================================================
@app.get("/insights/forestry/top-projects")
def forestry_top_projects(db: Session = Depends(get_db)):
    return get_forestry_top_projects(db)

# =========================================================
# 🔥 FORESTRY EMISSION VS SCORE
# =========================================================
@app.get("/insights/forestry/emission-vs-score")
def forestry_emission_vs_score(db: Session = Depends(get_db)):
    return get_forestry_emission_vs_score(db)

# =========================================================
# 🔥 FORESTRY CATEGORY PERFORMANCE
# =========================================================
@app.get("/insights/forestry/category-performance")
def forestry_category_performance(db: Session = Depends(get_db)):
    return get_forestry_category_performance(db)

# =========================================================
# 🔥 FORESTRY SCORE DISTRIBUTION
# =========================================================
@app.get("/insights/forestry/score-distribution")
def forestry_score_distribution(db: Session = Depends(get_db)):

    data = get_forestry_score_distribution(db)

    return {
        "sector": "forestry",
        "distribution": data
    }

# =========================================================
# 🔥 FORESTRY SDG DISTRIBUTION
# =========================================================
@app.get("/insights/forestry/sdg-distribution")
def forestry_sdg_distribution(db: Session = Depends(get_db)):

    data = get_forestry_sdg_distribution(db)

    return {
        "sector": "forestry",
        "distribution": data
    }

# =========================================================
# 🔥 LLM SIGNED URL
# =========================================================
@app.get("/project/{project_id}/llm-url")
def get_llm_signed_url(project_id: str):

    db = SessionLocal()

    try:
        result = db.execute(text("""
            SELECT s3_path
            FROM project_llm_results
            WHERE project_id = :project_id
        """), {"project_id": project_id}).fetchone()

        if not result:
            raise HTTPException(status_code=404, detail="LLM result not found")

        s3_key = result[0]

        url = s3.generate_presigned_url(
            "get_object",
            Params={
                "Bucket": BUCKET,
                "Key": s3_key
            },
            ExpiresIn=300
        )

        return {"url": url}

    finally:
        db.close()

# =========================================================
# 🔥 PROJECT SCORE
# =========================================================
@app.get("/project/{project_id}/score")
def get_project_score(project_id: str):

    db = SessionLocal()

    try:
        result = get_score_from_db(db, project_id)

        if not result:
            raise HTTPException(status_code=404, detail="Score not found")

        return result

    finally:
        db.close()

# =========================================================
# 🔥 LIST VERRA PROJECTS
# =========================================================
@app.get("/projects/verra")
def list_verra_projects():

    db = SessionLocal()

    try:
        result = db.execute(text("""
            SELECT 
                vm.project_id,
                vm.project_name,
                vm.project_status,
                vm.project_category,
                vm.annual_emission_reduction,

                ps.sector,
                ps.final_score

            FROM verra_metadata vm

            LEFT JOIN project_scores ps
                ON vm.project_id = ps.project_id

            ORDER BY vm.created_at DESC
        """))

        rows = result.mappings().all()

        return [
            {
                "id": r["project_id"],
                "name": r["project_name"],
                "status": r["project_status"],
                "category": r["project_category"],
                "credits": r["annual_emission_reduction"],
                "sector": r["sector"],
                "score": r["final_score"]
            }
            for r in rows
        ]

    finally:
        db.close()

# =========================================================
# 🔥 LIST GS PROJECTS
# =========================================================
@app.get("/projects/gs")
def list_gs_projects():

    db = SessionLocal()

    try:
        result = db.execute(text("""
            SELECT 
                gm.project_id,
                gm.project_name,
                gm.project_status,
                gm.project_type,
                gm.annual_credits,

                ps.sector,
                ps.final_score

            FROM gs_metadata gm

            LEFT JOIN project_scores ps
                ON gm.project_id = ps.project_id

            ORDER BY gm.created_at DESC
        """))

        rows = result.mappings().all()

        return [
            {
                "id": r["project_id"],
                "name": r["project_name"],
                "status": r["project_status"],
                "category": r["project_type"],
                "credits": r["annual_credits"],
                "sector": r["sector"],
                "score": r["final_score"]
            }
            for r in rows
        ]

    finally:
        db.close()

# =========================================================
# 🔥 WEBSOCKET CONNECTIONS
# =========================================================
connections = {}

# =========================================================
# 🔥 WEBSOCKET EVENT SENDER
# =========================================================
async def send_update(project_id: str, payload: dict):

    if project_id not in connections:
        return

    dead = []

    for ws in connections[project_id]:

        try:
            await ws.send_json(payload)

        except:
            dead.append(ws)

    for ws in dead:
        connections[project_id].remove(ws)

# =========================================================
# 🔥 WEBSOCKET
# =========================================================
@app.websocket("/ws/{project_id}")
async def websocket_endpoint(websocket: WebSocket, project_id: str):

    await websocket.accept()

    connections.setdefault(project_id, []).append(websocket)

    try:
        while True:
            await websocket.receive_text()

    except WebSocketDisconnect:

        if project_id in connections:
            connections[project_id].remove(websocket)

# =========================================================
# 🔥 START PIPELINE
# =========================================================
@app.post("/project/{project_id}/start")
async def start_ingestion(project_id: str, background_tasks: BackgroundTasks):

    async def run_pipeline():

        try:
            from scripts.ingest_project import process_project_with_progress
            from embeddings.embedding_factory import EmbeddingFactory
            from vectordb.vector_store import VectorStore
            from scripts.utils import setup_logger

            logger = setup_logger("API-Ingest")

            # =================================================
            # INITIALIZING
            # =================================================
            await send_update(project_id, {
                "type": "pipeline_step",
                "stage": "initialization",
                "message": "Initializing AI evaluation pipeline",
                "status": "running",
                "progress": 5
            })

            # =================================================
            # EMBEDDINGS
            # =================================================
            await send_update(project_id, {
                "type": "pipeline_step",
                "stage": "embedding_model",
                "message": "Loading embedding model",
                "status": "running",
                "progress": 10
            })

            embedding_model = EmbeddingFactory.create(
                "nomic",
                batch_size=32
            )

            # =================================================
            # VECTOR DB
            # =================================================
            await send_update(project_id, {
                "type": "pipeline_step",
                "stage": "vector_database",
                "message": "Connecting to vector database",
                "status": "running",
                "progress": 15
            })

            store = VectorStore(embedding_model)

            store.initialize(
                False,
                model="nomic",
                collection="nomic"
            )

            # =================================================
            # INGESTION
            # =================================================
            await send_update(project_id, {
                "type": "pipeline_step",
                "stage": "ingestion",
                "message": "Starting document ingestion pipeline",
                "status": "running",
                "progress": 20
            })

            await process_project_with_progress(
                base_path=Path("temp"),
                proj=project_id,
                workers=4,
                logger=logger,
                store=store,
                send_update=send_update
            )

            # =================================================
            # SDG ANALYSIS
            # =================================================
            from scripts.run_agent import run_agent_with_progress

            await send_update(project_id, {
                "type": "pipeline_step",
                "stage": "sdg_analysis",
                "message": "Starting SDG intelligence analysis",
                "status": "running",
                "progress": 70
            })

            await run_agent_with_progress(
                project_id=project_id,
                embedding="nomic",
                send_update=send_update
            )

            # =================================================
            # COMPLETE
            # =================================================
            await send_update(project_id, {
                "type": "pipeline_complete",
                "stage": "completed",
                "message": "Full AI sustainability analysis completed",
                "status": "done",
                "progress": 100
            })

        except Exception as e:

            await send_update(project_id, {
                "type": "pipeline_error",
                "stage": "failed",
                "message": f"Pipeline failed: {str(e)}",
                "status": "failed"
            })

    asyncio.create_task(run_pipeline())

    return {
        "message": f"Pipeline started for {project_id}"
    }