from sqlalchemy import text

def upsert_metadata(db, metadata: dict):

    query = text("""
        INSERT INTO verra_metadata (
            project_id,
            project_name,
            description,
            latitude,
            longitude,
            state_province,
            project_status,
            annual_emission_reduction,
            buffer_pool_credits,
            project_category,
            project_subcategory,
            registration_date,
            crediting_period
        )
        VALUES (
            :project_id,
            :project_name,
            :description,
            :latitude,
            :longitude,
            :state_province,
            :project_status,
            :annual_emission_reduction,
            :buffer_pool_credits,
            :project_category,
            :project_subcategory,
            :registration_date,
            :crediting_period
        )
        ON CONFLICT (project_id) DO UPDATE SET
            project_name = EXCLUDED.project_name,
            description = EXCLUDED.description,
            latitude = EXCLUDED.latitude,
            longitude = EXCLUDED.longitude,
            state_province = EXCLUDED.state_province,
            project_status = EXCLUDED.project_status,
            annual_emission_reduction = EXCLUDED.annual_emission_reduction,
            buffer_pool_credits = EXCLUDED.buffer_pool_credits,
            project_category = EXCLUDED.project_category,
            project_subcategory = EXCLUDED.project_subcategory,
            registration_date = EXCLUDED.registration_date,
            crediting_period = EXCLUDED.crediting_period,
            updated_at = NOW()
    """)

    db.execute(query, metadata)
    db.commit()