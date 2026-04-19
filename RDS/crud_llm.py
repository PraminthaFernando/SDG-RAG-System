from sqlalchemy import text
from sqlalchemy.orm import Session

from RDS.s3_llm_storage import (
    upload_llm_result,
    get_llm_result_s3,
    delete_llm_result_s3
)


# =========================================================
# 🔥 UPSERT (SAVE TO S3 + STORE PATH)
# =========================================================
def upsert_llm_result(db: Session, project_id: str, llm_json: dict):

    # 1️⃣ Upload to S3
    s3_key = upload_llm_result(project_id, llm_json)

    # 2️⃣ Save path in DB
    query = text("""
        INSERT INTO project_llm_results (
            project_id,
            s3_path
        )
        VALUES (
            :project_id,
            :s3_path
        )
        ON CONFLICT (project_id) DO UPDATE SET
            s3_path = EXCLUDED.s3_path,
            updated_at = NOW()
    """)

    db.execute(query, {
        "project_id": project_id,
        "s3_path": s3_key
    })

    db.commit()


# =========================================================
# 🔥 GET (FETCH FROM S3)
# =========================================================
def get_llm_result(db: Session, project_id: str):

    query = text("""
        SELECT s3_path
        FROM project_llm_results
        WHERE project_id = :project_id
    """)

    result = db.execute(query, {"project_id": project_id}).fetchone()

    if not result:
        return None

    s3_path = result[0]

    # 🔥 Fetch actual JSON from S3
    return get_llm_result_s3(s3_path)


# =========================================================
# 🔥 DELETE
# =========================================================
def delete_llm_result(db: Session, project_id: str):

    query = text("""
        SELECT s3_path
        FROM project_llm_results
        WHERE project_id = :project_id
    """)

    result = db.execute(query, {"project_id": project_id}).fetchone()

    if result:
        s3_path = result[0]
        delete_llm_result_s3(s3_path)

    db.execute(
        text("DELETE FROM project_llm_results WHERE project_id = :project_id"),
        {"project_id": project_id}
    )

    db.commit()