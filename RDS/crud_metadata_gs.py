from sqlalchemy import text
from sqlalchemy.orm import Session
from psycopg2.extras import Json


# =========================================================
# 🔥 UPSERT GS METADATA
# =========================================================
def upsert_metadata_gs(db: Session, metadata: dict):

    query = text("""
        INSERT INTO gs_metadata (
            project_id,
            gs_project_numeric_id,
            sustaincert_id,
            sustaincert_url,

            project_name,
            description,

            project_status,
            standard,

            project_type,
            project_size,
            methodology,

            project_developer,
            country,
            country_code,
            state,

            latitude,
            longitude,

            annual_credits,
            carbon_stream,

            crediting_start_date,
            crediting_end_date,

            programme_of_activities,
            poa_project_id,
            poa_project_sustaincert_id,

            corsia_eligible,

            sdgs,
            updated_at
        )
        VALUES (
            :project_id,
            :gs_project_numeric_id,
            :sustaincert_id,
            :sustaincert_url,

            :project_name,
            :description,

            :project_status,
            :standard,

            :project_type,
            :project_size,
            :methodology,

            :project_developer,
            :country,
            :country_code,
            :state,

            :latitude,
            :longitude,

            :annual_credits,
            :carbon_stream,

            :crediting_start_date,
            :crediting_end_date,

            :programme_of_activities,
            :poa_project_id,
            :poa_project_sustaincert_id,

            :corsia_eligible,

            :sdgs,
            NOW()
        )
        ON CONFLICT (project_id)
        DO UPDATE SET
            gs_project_numeric_id = EXCLUDED.gs_project_numeric_id,
            sustaincert_id = EXCLUDED.sustaincert_id,
            sustaincert_url = EXCLUDED.sustaincert_url,

            project_name = EXCLUDED.project_name,
            description = EXCLUDED.description,

            project_status = EXCLUDED.project_status,
            standard = EXCLUDED.standard,

            project_type = EXCLUDED.project_type,
            project_size = EXCLUDED.project_size,
            methodology = EXCLUDED.methodology,

            project_developer = EXCLUDED.project_developer,
            country = EXCLUDED.country,
            country_code = EXCLUDED.country_code,
            state = EXCLUDED.state,

            latitude = EXCLUDED.latitude,
            longitude = EXCLUDED.longitude,

            annual_credits = EXCLUDED.annual_credits,
            carbon_stream = EXCLUDED.carbon_stream,

            crediting_start_date = EXCLUDED.crediting_start_date,
            crediting_end_date = EXCLUDED.crediting_end_date,

            programme_of_activities = EXCLUDED.programme_of_activities,
            poa_project_id = EXCLUDED.poa_project_id,
            poa_project_sustaincert_id = EXCLUDED.poa_project_sustaincert_id,

            corsia_eligible = EXCLUDED.corsia_eligible,

            sdgs = EXCLUDED.sdgs,
            updated_at = NOW()
    """)

    db.execute(
        query,
        {
            **metadata,
            "sdgs": Json(metadata.get("sdgs"))
        }
    )

    db.commit()


# =========================================================
# 🔥 FETCH GS METADATA
# =========================================================
def get_gs_metadata(db: Session, project_id: str):

    result = db.execute(
        text("""
            SELECT *
            FROM gs_metadata
            WHERE project_id = :pid
        """),
        {"pid": project_id}
    )

    row = result.mappings().first()

    if not row:
        return None

    return dict(row)