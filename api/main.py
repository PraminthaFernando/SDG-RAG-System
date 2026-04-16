from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect
from pathlib import Path
import json
from fastapi.middleware.cors import CORSMiddleware
from fastapi import BackgroundTasks
import asyncio

# 🔥 DB IMPORTS
from RDS.database import SessionLocal
from RDS.crud_metadata import get_metadata   # ✅ FIXED
from RDS.crud_score import get_project_score as get_score_from_db

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

BASE_OUTPUT_DIR = Path(__file__).resolve().parent.parent / "outputs"

# =========================================================
# 🔥 ROOT
# =========================================================
@app.get("/")
def root():
    return {"message": "API is running 🚀"}


# =========================================================
# 🔥 METADATA FROM DB (FIXED)
# =========================================================
@app.get("/project/{project_id}")
def get_project_metadata(project_id: str):
    db = SessionLocal()
    try:
        result = get_metadata(db, project_id)  # ✅ FIXED

        if not result:
            raise HTTPException(status_code=404, detail="Project not found")

        return result  # ✅ already dict

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

    finally:
        db.close()


# =========================================================
# 🔥 LLM RESULTS (FILE BASED - UNCHANGED)
# =========================================================
@app.get("/project/{project_id}/llm")
def get_project_llm(project_id: str):
    try:
        file_path = BASE_OUTPUT_DIR / project_id / "nomic_sdg_prototype_llm_results.json"

        if not file_path.exists():
            raise HTTPException(status_code=404, detail="LLM results not found")

        with open(file_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        return data

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# =========================================================
# 🔥 SCORE FROM DB (UNCHANGED)
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
# 🔥 WEBSOCKET MANAGER
# =========================================================
connections = {}  # project_id -> list[WebSocket]


async def send_update(project_id: str, step: str, status: str = "running"):
    if project_id not in connections:
        return

    dead_connections = []

    for ws in connections[project_id]:
        try:
            await ws.send_json({
                "step": step,
                "status": status
            })
        except:
            dead_connections.append(ws)

    for ws in dead_connections:
        connections[project_id].remove(ws)


# =========================================================
# 🔥 WEBSOCKET ENDPOINT
# =========================================================
@app.websocket("/ws/{project_id}")
async def websocket_endpoint(websocket: WebSocket, project_id: str):
    await websocket.accept()

    if project_id not in connections:
        connections[project_id] = []

    connections[project_id].append(websocket)

    print(f"✅ WebSocket connected: {project_id}")

    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        print(f"❌ WebSocket disconnected: {project_id}")
        connections[project_id].remove(websocket)


# =========================================================
# 🔥 START FULL PIPELINE (UNCHANGED)
# =========================================================
@app.post("/project/{project_id}/start")
async def start_ingestion(project_id: str, background_tasks: BackgroundTasks):
    try:

        async def run_pipeline():
            try:
                from scripts.ingest_project import process_project_with_progress
                from embeddings.embedding_factory import EmbeddingFactory
                from vectordb.vector_store import VectorStore
                from scripts.utils import setup_logger

                logger = setup_logger("API-Ingest")

                await send_update(project_id, "🚀 Initializing system")
                await send_update(project_id, "Loading embedding model")

                embedding_model = EmbeddingFactory.create("nomic", batch_size=32)

                await send_update(project_id, "Connecting to vector database")

                store = VectorStore(embedding_model)
                store.initialize(False, model="nomic", collection="nomic")

                await send_update(project_id, "Starting ingestion pipeline")

                base_path = Path("pdfs")

                await process_project_with_progress(
                    base_path,
                    project_id,
                    2,
                    logger,
                    store,
                    send_update
                )

                from scripts.run_agent import run_agent_with_progress

                await send_update(project_id, "🚀 Starting SDG analysis")

                await run_agent_with_progress(
                    project_id=project_id,
                    output_path="outputs",
                    embedding="nomic",
                    send_update=send_update
                )

                await send_update(project_id, "🎉 Full pipeline completed", "done")

            except Exception as e:
                await send_update(project_id, f"❌ Error: {str(e)}", "failed")

        asyncio.create_task(run_pipeline())

        return {"message": f"Pipeline started for {project_id}"}

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    

    # =========================================================
# 🔥 LIST VERRA PROJECTS (NEW)
# =========================================================
from sqlalchemy import text

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

        rows = result.mappings().all()  # ✅ important

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