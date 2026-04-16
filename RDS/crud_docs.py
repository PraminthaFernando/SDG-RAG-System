from sqlalchemy import text
from sqlalchemy.orm import Session


# =========================================================
# 🔥 UPSERT DOCUMENTS (REPLACE ALL FOR PROJECT)
# =========================================================
def replace_project_documents(db: Session, project_id: str, docs: list):

    # 🔥 delete old docs
    db.execute(
        text("DELETE FROM project_documents WHERE project_id = :pid"),
        {"pid": project_id}
    )

    # 🔥 insert new ones
    for d in docs:
        db.execute(
            text("""
                INSERT INTO project_documents (
                    project_id,
                    document_name,
                    document_type,
                    uri,
                    upload_date
                )
                VALUES (
                    :project_id,
                    :document_name,
                    :document_type,
                    :uri,
                    :upload_date
                )
            """),
            {
                "project_id": project_id,
                "document_name": d.get("documentName"),
                "document_type": d.get("documentType"),
                "uri": d.get("uri"),
                "upload_date": d.get("uploadDate"),
            }
        )

    db.commit()


# =========================================================
# 🔥 FETCH DOCUMENTS
# =========================================================
def get_project_documents(db: Session, project_id: str):

    result = db.execute(
        text("""
            SELECT 
                document_name,
                document_type,
                uri,
                upload_date
            FROM project_documents
            WHERE project_id = :pid
            ORDER BY upload_date DESC
        """),
        {"pid": project_id}
    )

    rows = result.mappings().all()

    return [
        {
            "document_name": r["document_name"],
            "document_type": r["document_type"],
            "uri": r["uri"],
            "upload_date": r["upload_date"],
        }
        for r in rows
    ]