from sqlalchemy import text
from sqlalchemy.orm import Session


# =========================================================
# 🔥 FETCH VERRA CATEGORY (UNCHANGED)
# =========================================================
def get_verra_category(db: Session, project_id: str):

    result = db.execute(
        text("""
            SELECT project_category
            FROM verra_metadata
            WHERE project_id = :pid
        """),
        {"pid": project_id}
    )

    row = result.fetchone()
    return row[0] if row else None


# =========================================================
# 🔥 FETCH GS PROJECT NAME (NEW)
# =========================================================
def get_gs_project_name(db: Session, project_id: str):

    result = db.execute(
        text("""
            SELECT project_name
            FROM gs_metadata
            WHERE project_id = :pid
        """),
        {"pid": project_id}
    )

    row = result.fetchone()
    return row[0] if row else None


# =========================================================
# 🔥 MAP VERRA CATEGORY → SECTOR (UNCHANGED)
# =========================================================
def map_verra_category(category: str):

    if not category:
        return "renewables"

    category = category.strip().lower()

    if "agriculture forestry and other land use" in category:
        return "forestry"

    if any(k in category for k in ["forestry", "afolu", "redd", "arr", "ifm"]):
        return "forestry"

    return "renewables"


# =========================================================
# 🔥 MAP GS NAME → SECTOR (NEW LOGIC)
# =========================================================
def map_gs_name(project_name: str):

    if not project_name:
        return "renewables"

    name = project_name.lower()

    # 🌳 Forestry keywords
    forestry_keywords = [
        "forest",
        "reforestation",
        "afforestation",
        "redd",
        "arr",
        "ifm",
        "natural regeneration",
        "plantation",
        "conservation",
        "arb",
    ]

    # ⚡ Renewable / energy keywords
    energy_keywords = [
        "solar",
        "wind",
        "hydro",
        "power",
        "energy",
        "biogas",
        "methane",
        "electric",
        "pv",
        "generation",
        "cookstove",
    ]

    # 🌳 PRIORITY → forestry
    if any(k in name for k in forestry_keywords):
        return "forestry"

    # ⚡ THEN → renewables
    if any(k in name for k in energy_keywords):
        return "renewables"

    return "renewables"


# =========================================================
# 🔥 MAIN UNIFIED FUNCTION
# =========================================================
def get_project_sector(db: Session, project_id: str):

    # =====================================================
    # 🔥 VERRA PROJECT (UNCHANGED)
    # =====================================================
    if project_id.startswith("VCS"):

        category = get_verra_category(db, project_id)
        sector = map_verra_category(category)

        return {
            "project_id": project_id,
            "source": "verra",
            "raw_type": category,
            "sector": sector
        }

    # =====================================================
    # 🔥 GOLD STANDARD PROJECT (UPDATED)
    # =====================================================
    elif project_id.startswith("GS"):

        project_name = get_gs_project_name(db, project_id)
        sector = map_gs_name(project_name)

        return {
            "project_id": project_id,
            "source": "gs",
            "raw_type": project_name,
            "sector": sector
        }

    # =====================================================
    # 🔥 FALLBACK
    # =====================================================
    return {
        "project_id": project_id,
        "source": "unknown",
        "raw_type": None,
        "sector": "renewables"
    }