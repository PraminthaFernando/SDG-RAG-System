from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect, BackgroundTasks
from pathlib import Path
from fastapi.middleware.cors import CORSMiddleware
import asyncio
from sqlalchemy import text

# 🔥 DB IMPORTS
from RDS.database import SessionLocal
from RDS.crud_metadata import get_metadata
from RDS.crud_score import get_project_score as get_score_from_db
from RDS.crud_llm import get_llm_result

app = FastAPI()

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
# 🔥 METADATA (AUTO DETECT)
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

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        db.close()


# =========================================================
# 🔥 LLM RESULTS
# =========================================================
@app.get("/project/{project_id}/llm")
def get_project_llm(project_id: str):
    db = SessionLocal()
    try:
        result = get_llm_result(db, project_id)

        if not result:
            raise HTTPException(status_code=404, detail="LLM results not found")

        return result

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        db.close()


# =========================================================
# 🔥 SCORE
# =========================================================
@app.get("/project/{project_id}/score")
def get_project_score(project_id: str):
    db = SessionLocal()
    try:
        result = get_score_from_db(db, project_id)

        if not result:
            raise HTTPException(status_code=404, detail="Score not found")

        return result

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
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
                project_id,
                project_name,
                project_status,
                project_category,
                annual_emission_reduction
            FROM verra_metadata
            ORDER BY created_at DESC
        """))

        rows = result.mappings().all()

        return [
            {
                "id": r["project_id"],
                "name": r["project_name"],
                "status": r["project_status"],
                "category": r["project_category"],
                "credits": r["annual_emission_reduction"]
            }
            for r in rows
        ]

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
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
                project_id,
                project_name,
                project_status,
                project_type,
                annual_credits
            FROM gs_metadata
            ORDER BY created_at DESC
        """))

        rows = result.mappings().all()

        return [
            {
                "id": r["project_id"],
                "name": r["project_name"],
                "status": r["project_status"],
                "category": r["project_type"],
                "credits": r["annual_credits"]
            }
            for r in rows
        ]

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        db.close()


# =========================================================
# 🔥 WEBSOCKET MANAGER
# =========================================================
connections = {}


async def send_update(project_id: str, step: str, status: str = "running"):
    if project_id not in connections:
        return

    dead = []

    for ws in connections[project_id]:
        try:
            await ws.send_json({
                "step": step,
                "status": status
            })
        except:
            dead.append(ws)

    for ws in dead:
        connections[project_id].remove(ws)


# =========================================================
# 🔥 WEBSOCKET ENDPOINT
# =========================================================
@app.websocket("/ws/{project_id}")
async def websocket_endpoint(websocket: WebSocket, project_id: str):
    await websocket.accept()

    connections.setdefault(project_id, []).append(websocket)

    print(f"✅ WS connected: {project_id}")

    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        print(f"❌ WS disconnected: {project_id}")
        connections[project_id].remove(websocket)


# =========================================================
# 🔥 START FULL PIPELINE
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

            await send_update(project_id, "🚀 Initializing system")

            # 🔥 EMBEDDING
            await send_update(project_id, "Loading embedding model")
            embedding_model = EmbeddingFactory.create("nomic", batch_size=32)

            # 🔥 VECTOR DB
            await send_update(project_id, "Connecting to vector database")
            store = VectorStore(embedding_model)
            store.initialize(False, model="nomic", collection="nomic")

            # 🔥 INGESTION
            await send_update(project_id, "Starting ingestion pipeline")

            await process_project_with_progress(
                base_path=Path("temp"),
                proj=project_id,
                workers=2,
                logger=logger,
                store=store,
                send_update=send_update
            )

            # 🔥 SDG ANALYSIS
            from scripts.run_agent import run_agent_with_progress

            await send_update(project_id, "🚀 Starting SDG analysis")

            await run_agent_with_progress(
                project_id=project_id,
                embedding="nomic",
                send_update=send_update
            )

            await send_update(project_id, "🎉 Full pipeline completed", "done")

        except Exception as e:
            await send_update(project_id, f"❌ Error: {str(e)}", "failed")

    asyncio.create_task(run_pipeline())

    return {"message": f"Pipeline started for {project_id}"}