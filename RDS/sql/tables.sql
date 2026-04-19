CREATE TABLE verra_metadata (
    project_id TEXT PRIMARY KEY,
    project_name TEXT,
    description TEXT,
    latitude DOUBLE PRECISION,
    longitude DOUBLE PRECISION,
    state_province TEXT,
    project_status TEXT,
    annual_emission_reduction INTEGER,
    buffer_pool_credits INTEGER,
    project_category TEXT,
    project_subcategory TEXT,
    registration_date TEXT,
    crediting_period TEXT,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);


CREATE TABLE project_scores (
    project_id TEXT PRIMARY KEY,
    sector TEXT,
    final_score DOUBLE PRECISION,

    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);


CREATE TABLE project_sdg_scores (
    id SERIAL PRIMARY KEY,

    project_id TEXT REFERENCES project_scores(project_id) ON DELETE CASCADE,
    sdg INTEGER,
    score DOUBLE PRECISION,

    UNIQUE(project_id, sdg)
);

CREATE TABLE project_documents (
    id SERIAL PRIMARY KEY,
    project_id TEXT,
    document_name TEXT,
    document_type TEXT,
    uri TEXT,
    upload_date TEXT
);

CREATE TABLE project_llm_results (
    project_id TEXT PRIMARY KEY,
    s3_path TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE gs_metadata (
    project_id TEXT PRIMARY KEY,              -- e.g. GS10924

    gs_project_numeric_id TEXT,               -- 2913
    sustaincert_id INTEGER,                   -- 10924
    sustaincert_url TEXT,

    project_name TEXT,
    description TEXT,

    project_status TEXT,
    standard TEXT,                            -- gsf_standards_version

    project_type TEXT,                        -- type
    project_size TEXT,                        -- size
    methodology TEXT,

    project_developer TEXT,
    country TEXT,
    country_code TEXT,
    state TEXT,

    latitude DOUBLE PRECISION,
    longitude DOUBLE PRECISION,

    annual_credits INTEGER,                   -- estimated_annual_credits
    carbon_stream TEXT,

    crediting_start_date DATE,
    crediting_end_date DATE,

    programme_of_activities TEXT,
    poa_project_id INTEGER,
    poa_project_sustaincert_id INTEGER,

    corsia_eligible BOOLEAN,

    sdgs JSONB,                               -- keep this (important)

    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);