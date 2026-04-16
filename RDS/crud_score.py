from sqlalchemy.orm import Session
from RDS.models import ProjectScore, ProjectSDGScore


# =========================================================
# 🔥 UPSERT PROJECT SCORE
# =========================================================
def upsert_project_score(db: Session, data: dict):
    project_id = data["project_id"]

    existing = db.query(ProjectScore).filter(
        ProjectScore.project_id == project_id
    ).first()

    if existing:
        existing.sector = data.get("sector")
        existing.final_score = data.get("final_score")
    else:
        existing = ProjectScore(
            project_id=project_id,
            sector=data.get("sector"),
            final_score=data.get("final_score"),
        )
        db.add(existing)

    db.commit()


# =========================================================
# 🔥 UPSERT SDG SCORES
# =========================================================
def upsert_sdg_scores(db: Session, project_id: str, sdgs: dict):
    # delete old SDG scores (simplest + clean)
    db.query(ProjectSDGScore).filter(
        ProjectSDGScore.project_id == project_id
    ).delete()

    for sdg, value in sdgs.items():
        score = value.get("score", 0)

        row = ProjectSDGScore(
            project_id=project_id,
            sdg=int(sdg),
            score=score
        )
        db.add(row)

    db.commit()


# =========================================================
# 🔥 FULL UPSERT (MAIN FUNCTION)
# =========================================================
def upsert_full_score(db: Session, project_id: str, payload: dict):
    upsert_project_score(db, {
        "project_id": project_id,
        "sector": payload.get("sector"),
        "final_score": payload.get("final_score")
    })

    upsert_sdg_scores(db, project_id, payload.get("sdgs", {}))


# =========================================================
# 🔥 FETCH SCORE
# =========================================================
def get_project_score(db: Session, project_id: str):
    project = db.query(ProjectScore).filter(
        ProjectScore.project_id == project_id
    ).first()

    if not project:
        return None

    sdgs = db.query(ProjectSDGScore).filter(
        ProjectSDGScore.project_id == project_id
    ).all()

    return {
        "project_id": project.project_id,
        "sector": project.sector,
        "final_score": project.final_score,
        "sdgs": {
            str(s.sdg): {"score": s.score} for s in sdgs
        }
    }