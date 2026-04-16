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
    llm_result JSONB NOT NULL,

    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);