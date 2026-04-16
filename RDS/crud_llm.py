from sqlalchemy import text
from sqlalchemy.orm import Session
from psycopg2.extras import Json


# =========================================================
# 🔥 UPSERT LLM RESULT
# =========================================================
def upsert_llm_result(db: Session, project_id: str, llm_json: dict):

    query = text("""
        INSERT INTO project_llm_results (
            project_id,
            llm_result
        )
        VALUES (
            :project_id,
            :llm_result
        )
        ON CONFLICT (project_id) DO UPDATE SET
            llm_result = EXCLUDED.llm_result,
            updated_at = NOW()
    """)

    db.execute(query, {
        "project_id": project_id,
        "llm_result": Json(llm_json)  # ✅ FIX
    })

    db.commit()


# =========================================================
# 🔥 GET LLM RESULT
# =========================================================
def get_llm_result(db: Session, project_id: str):

    query = text("""
        SELECT llm_result
        FROM project_llm_results
        WHERE project_id = :project_id
    """)

    result = db.execute(query, {"project_id": project_id}).fetchone()

    if not result:
        return None

    return result[0]  # JSONB auto converted to dict


# =========================================================
# 🔥 DELETE (OPTIONAL)
# =========================================================
def delete_llm_result(db: Session, project_id: str):

    query = text("""
        DELETE FROM project_llm_results
        WHERE project_id = :project_id
    """)

    db.execute(query, {"project_id": project_id})
    db.commit()