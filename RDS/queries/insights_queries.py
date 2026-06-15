from sqlalchemy import text

# =========================================================
# 🔥 FORESTRY SCORE DISTRIBUTION
# =========================================================
GET_FORESTRY_SCORE_DISTRIBUTION = text("""
    SELECT 
        FLOOR(final_score * 100 / 10) * 10 AS bin_start,
        COUNT(*) AS count
    FROM project_scores
    WHERE sector = 'forestry'
      AND final_score IS NOT NULL
      AND final_score > 0
    GROUP BY bin_start
    ORDER BY bin_start
""")

# =========================================================
# 🔥 FORESTRY SDG DISTRIBUTION (PIE CHART)
# =========================================================
GET_FORESTRY_SDG_DISTRIBUTION = text("""
    SELECT 
        s.sdg,
        AVG(s.score) AS avg_score
    FROM project_sdg_scores s
    JOIN project_scores ps
        ON s.project_id = ps.project_id
    WHERE ps.sector = 'forestry'
    GROUP BY s.sdg
    ORDER BY s.sdg
""")

# =========================================================
# 🔥 KPI SUMMARY
# =========================================================
GET_FORESTRY_SUMMARY = text("""
    SELECT 
        AVG(final_score) AS avg_score,
        COUNT(*) AS total_projects
    FROM project_scores
    WHERE sector = 'forestry'
      AND final_score IS NOT NULL
""")

# =========================================================
# 🔥 SDG AVERAGE (BAR CHART)
# =========================================================
GET_FORESTRY_SDG_AVG = text("""
    SELECT 
        s.sdg,
        AVG(s.score) AS avg_score
    FROM project_sdg_scores s
    JOIN project_scores ps
        ON s.project_id = ps.project_id
    WHERE ps.sector = 'forestry'
    GROUP BY s.sdg
    ORDER BY s.sdg
""")

# =========================================================
# 🔥 TOP PROJECTS
# =========================================================
GET_FORESTRY_TOP_PROJECTS = text("""
    SELECT 
        ps.project_id,
        vm.project_name,
        ps.final_score
    FROM project_scores ps
    JOIN verra_metadata vm
        ON ps.project_id = vm.project_id
    WHERE ps.sector = 'forestry'
      AND ps.final_score IS NOT NULL
    ORDER BY ps.final_score DESC
    LIMIT 10
""")

# =========================================================
# 🔥 EMISSION VS SCORE
# =========================================================
GET_FORESTRY_EMISSION_SCORE = text("""
    SELECT 
        vm.annual_emission_reduction,
        ps.final_score
    FROM project_scores ps
    JOIN verra_metadata vm
        ON ps.project_id = vm.project_id
    WHERE ps.sector = 'forestry'
      AND vm.annual_emission_reduction IS NOT NULL
      AND ps.final_score IS NOT NULL
""")

# =========================================================
# 🔥 CATEGORY PERFORMANCE
# =========================================================
GET_FORESTRY_CATEGORY_PERFORMANCE = text("""
    SELECT 
        vm.project_category,
        AVG(ps.final_score) AS avg_score,
        COUNT(*) AS count
    FROM project_scores ps
    JOIN verra_metadata vm
        ON ps.project_id = vm.project_id
    WHERE ps.sector = 'forestry'
      AND vm.project_category IS NOT NULL
    GROUP BY vm.project_category
    ORDER BY avg_score DESC
""")

GET_FORESTRY_MAP = """
SELECT 
    vm.project_id,
    vm.project_name,
    vm.latitude,
    vm.longitude,
    ps.final_score
FROM verra_metadata vm
JOIN project_scores ps 
    ON vm.project_id = ps.project_id
WHERE ps.sector = 'forestry'
AND vm.latitude IS NOT NULL
AND vm.longitude IS NOT NULL
"""

# =========================================================
# 🔥 RENEWABLE SCORE DISTRIBUTION
# =========================================================
GET_RENEWABLE_SCORE_DISTRIBUTION = text("""
    SELECT 
        FLOOR(final_score * 100 / 10) * 10 AS bin_start,
        COUNT(*) AS count
    FROM project_scores
    WHERE sector = 'renewables'
      AND final_score IS NOT NULL
      AND final_score > 0
    GROUP BY bin_start
    ORDER BY bin_start
""")

# =========================================================
# 🔥 RENEWABLE SDG DISTRIBUTION (PIE CHART)
# =========================================================
GET_RENEWABLE_SDG_DISTRIBUTION = text("""
    SELECT 
        s.sdg,
        AVG(s.score) AS avg_score
    FROM project_sdg_scores s
    JOIN project_scores ps
        ON s.project_id = ps.project_id
    WHERE ps.sector = 'renewables'
    GROUP BY s.sdg
    ORDER BY s.sdg
""")

# =========================================================
# 🔥 KPI SUMMARY
# =========================================================
GET_RENEWABLE_SUMMARY = text("""
    SELECT 
        AVG(final_score) AS avg_score,
        COUNT(*) AS total_projects
    FROM project_scores
    WHERE sector = 'renewables'
      AND final_score IS NOT NULL
""")

# =========================================================
# 🔥 SDG AVERAGE (BAR CHART)
# =========================================================
GET_RENEWABLE_SDG_AVG = text("""
    SELECT 
        s.sdg,
        AVG(s.score) AS avg_score
    FROM project_sdg_scores s
    JOIN project_scores ps
        ON s.project_id = ps.project_id
    WHERE ps.sector = 'renewables'
    GROUP BY s.sdg
    ORDER BY s.sdg
""")

# =========================================================
# 🔥 TOP PROJECTS
# =========================================================
GET_RENEWABLE_TOP_PROJECTS = text("""
    SELECT 
        ps.project_id,
        vm.project_name,
        ps.final_score
    FROM project_scores ps
    JOIN verra_metadata vm
        ON ps.project_id = vm.project_id
    WHERE ps.sector = 'renewables'
      AND ps.final_score IS NOT NULL
    ORDER BY ps.final_score DESC
    LIMIT 10
""")

# =========================================================
# 🔥 EMISSION VS SCORE
# =========================================================
GET_RENEWABLE_EMISSION_SCORE = text("""
    SELECT 
        vm.annual_emission_reduction,
        ps.final_score
    FROM project_scores ps
    JOIN verra_metadata vm
        ON ps.project_id = vm.project_id
    WHERE ps.sector = 'renewables'
      AND vm.annual_emission_reduction IS NOT NULL
      AND ps.final_score IS NOT NULL
""")

# =========================================================
# 🔥 CATEGORY PERFORMANCE
# =========================================================
GET_RENEWABLE_CATEGORY_PERFORMANCE = text("""
    SELECT 
        vm.project_category,
        AVG(ps.final_score) AS avg_score,
        COUNT(*) AS count
    FROM project_scores ps
    JOIN verra_metadata vm
        ON ps.project_id = vm.project_id
    WHERE ps.sector = 'renewables'
      AND vm.project_category IS NOT NULL
    GROUP BY vm.project_category
    ORDER BY avg_score DESC
""")

# =========================================================
# 🔥 MAP DATA
# =========================================================
GET_RENEWABLE_MAP = text("""
    SELECT 
        vm.project_id,
        vm.project_name,
        vm.latitude,
        vm.longitude,
        ps.final_score
    FROM verra_metadata vm
    JOIN project_scores ps 
        ON vm.project_id = ps.project_id
    WHERE ps.sector = 'renewables'
    AND vm.latitude IS NOT NULL
    AND vm.longitude IS NOT NULL
""")