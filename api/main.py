from fastapi import FastAPI, HTTPException
from pathlib import Path
import json
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # or ["http://localhost:3000"]
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

BASE_OUTPUT_DIR = Path(__file__).resolve().parent.parent / "outputs"


@app.get("/")
def root():
    return {"message": "API is running 🚀"}


@app.get("/project/{project_id}")
def get_project_metadata(project_id: str):
    try:
        # Example: outputs/VCS_1071/metadata.json
        file_path = BASE_OUTPUT_DIR / project_id / "metadata.json"

        if not file_path.exists():
            raise HTTPException(status_code=404, detail="Project not found")

        with open(file_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        return data

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    
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
    

@app.get("/project/{project_id}/score")
def get_project_score(project_id: str):
    try:
        file_path = BASE_OUTPUT_DIR / project_id / "project_impact_score.json"

        if not file_path.exists():
            raise HTTPException(status_code=404, detail="score results not found")

        with open(file_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        return data

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))