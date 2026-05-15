def get_forestry_score_distribution(db):
    from RDS.queries.insights_queries import GET_FORESTRY_SCORE_DISTRIBUTION

    result = db.execute(GET_FORESTRY_SCORE_DISTRIBUTION)
    rows = result.fetchall()

    distribution = []

    for r in rows:
        start = int(r[0])
        end = start + 10

        distribution.append({
            "range": f"{start}-{end}",
            "count": r[1]
        })

    return distribution

def get_forestry_sdg_distribution(db):
    from RDS.queries.insights_queries import GET_FORESTRY_SDG_DISTRIBUTION

    result = db.execute(GET_FORESTRY_SDG_DISTRIBUTION)
    rows = result.fetchall()

    # 🔥 Convert to total share (for pie chart)
    total = sum([r[1] for r in rows]) if rows else 0

    distribution = []

    for r in rows:
        sdg = r[0]
        avg_score = r[1]

        percentage = (avg_score / total * 100) if total > 0 else 0

        distribution.append({
            "sdg": sdg,
            "value": round(percentage, 2)
        })

    return distribution

# =========================================================
# 🔥 KPI SUMMARY
# =========================================================
def get_forestry_summary(db):
    from RDS.queries.insights_queries import GET_FORESTRY_SUMMARY

    row = db.execute(GET_FORESTRY_SUMMARY).fetchone()

    return {
        "avg_score": round(row[0] * 100, 2) if row[0] else 0,
        "total_projects": row[1]
    }


# =========================================================
# 🔥 SDG AVERAGE
# =========================================================
def get_forestry_sdg_avg(db):
    from RDS.queries.insights_queries import GET_FORESTRY_SDG_AVG

    rows = db.execute(GET_FORESTRY_SDG_AVG).fetchall()

    return [
        {
            "sdg": r[0],
            "score": round(r[1] * 100, 2)
        }
        for r in rows
    ]


# =========================================================
# 🔥 TOP PROJECTS
# =========================================================
def get_forestry_top_projects(db):
    from RDS.queries.insights_queries import GET_FORESTRY_TOP_PROJECTS

    rows = db.execute(GET_FORESTRY_TOP_PROJECTS).fetchall()

    return [
        {
            "project_id": r[0],
            "name": r[1],
            "score": round(r[2] * 100, 2)
        }
        for r in rows
    ]


# =========================================================
# 🔥 EMISSION VS SCORE
# =========================================================
def get_forestry_emission_vs_score(db):
    from RDS.queries.insights_queries import GET_FORESTRY_EMISSION_SCORE

    rows = db.execute(GET_FORESTRY_EMISSION_SCORE).fetchall()

    return [
        {
            "emission": r[0],
            "score": round(r[1] * 100, 2)
        }
        for r in rows
    ]


# =========================================================
# 🔥 CATEGORY PERFORMANCE
# =========================================================
def get_forestry_category_performance(db):
    from RDS.queries.insights_queries import GET_FORESTRY_CATEGORY_PERFORMANCE

    rows = db.execute(GET_FORESTRY_CATEGORY_PERFORMANCE).fetchall()

    return [
        {
            "category": r[0],
            "avg_score": round(r[1] * 100, 2),
            "count": r[2]
        }
        for r in rows
    ]

from sqlalchemy import text
from RDS.queries.insights_queries import GET_FORESTRY_MAP

def get_forestry_map_data(db):
    result = db.execute(text(GET_FORESTRY_MAP)).mappings().all()

    return [
        {
            "project_id": r["project_id"],
            "name": r["project_name"],
            "latitude": r["latitude"],
            "longitude": r["longitude"],
            "score": r["final_score"],
        }
        for r in result
    ]

# =========================================================
# 🔥 RENEWABLE SCORE DISTRIBUTION
# =========================================================
def get_renewable_score_distribution(db):
    from RDS.queries.insights_queries import GET_RENEWABLE_SCORE_DISTRIBUTION

    result = db.execute(GET_RENEWABLE_SCORE_DISTRIBUTION)
    rows = result.fetchall()

    distribution = []

    for r in rows:
        start = int(r[0])
        end = start + 10

        distribution.append({
            "range": f"{start}-{end}",
            "count": r[1]
        })

    return distribution


# =========================================================
# 🔥 RENEWABLE SDG DISTRIBUTION (PIE)
# =========================================================
def get_renewable_sdg_distribution(db):
    from RDS.queries.insights_queries import GET_RENEWABLE_SDG_DISTRIBUTION

    result = db.execute(GET_RENEWABLE_SDG_DISTRIBUTION)
    rows = result.fetchall()

    total = sum([r[1] for r in rows]) if rows else 0

    distribution = []

    for r in rows:
        sdg = r[0]
        avg_score = r[1]

        percentage = (avg_score / total * 100) if total > 0 else 0

        distribution.append({
            "sdg": sdg,
            "value": round(percentage, 2)
        })

    return distribution


# =========================================================
# 🔥 KPI SUMMARY
# =========================================================
def get_renewable_summary(db):
    from RDS.queries.insights_queries import GET_RENEWABLE_SUMMARY

    row = db.execute(GET_RENEWABLE_SUMMARY).fetchone()

    return {
        "avg_score": round(row[0] * 100, 2) if row[0] else 0,
        "total_projects": row[1]
    }


# =========================================================
# 🔥 SDG AVERAGE
# =========================================================
def get_renewable_sdg_avg(db):
    from RDS.queries.insights_queries import GET_RENEWABLE_SDG_AVG

    rows = db.execute(GET_RENEWABLE_SDG_AVG).fetchall()

    return [
        {
            "sdg": r[0],
            "score": round(r[1] * 100, 2)
        }
        for r in rows
    ]


# =========================================================
# 🔥 TOP PROJECTS
# =========================================================
def get_renewable_top_projects(db):
    from RDS.queries.insights_queries import GET_RENEWABLE_TOP_PROJECTS

    rows = db.execute(GET_RENEWABLE_TOP_PROJECTS).fetchall()

    return [
        {
            "project_id": r[0],
            "name": r[1],
            "score": round(r[2] * 100, 2)
        }
        for r in rows
    ]


# =========================================================
# 🔥 EMISSION VS SCORE
# =========================================================
def get_renewable_emission_vs_score(db):
    from RDS.queries.insights_queries import GET_RENEWABLE_EMISSION_SCORE

    rows = db.execute(GET_RENEWABLE_EMISSION_SCORE).fetchall()

    return [
        {
            "emission": r[0],
            "score": round(r[1] * 100, 2)
        }
        for r in rows
    ]


# =========================================================
# 🔥 CATEGORY PERFORMANCE
# =========================================================
def get_renewable_category_performance(db):
    from RDS.queries.insights_queries import GET_RENEWABLE_CATEGORY_PERFORMANCE

    rows = db.execute(GET_RENEWABLE_CATEGORY_PERFORMANCE).fetchall()

    return [
        {
            "category": r[0],
            "avg_score": round(r[1] * 100, 2),
            "count": r[2]
        }
        for r in rows
    ]


# =========================================================
# 🔥 MAP DATA
# =========================================================
def get_renewable_map_data(db):
    from RDS.queries.insights_queries import GET_RENEWABLE_MAP

    result = db.execute(GET_RENEWABLE_MAP).mappings().all()

    return [
        {
            "project_id": r["project_id"],
            "name": r["project_name"],
            "latitude": r["latitude"],
            "longitude": r["longitude"],
            "score": r["final_score"],  # keep raw
        }
        for r in result
    ]