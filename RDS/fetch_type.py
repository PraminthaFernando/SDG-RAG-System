from sqlalchemy import text
from sqlalchemy.orm import Session


# =========================================================
# 🔥 FETCH VERRA CATEGORY
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
# 🔥 FETCH GS PROJECT TYPE
# =========================================================
def get_gs_project_type(db: Session, project_id: str):

    result = db.execute(
        text("""
            SELECT project_type
            FROM gs_metadata
            WHERE project_id = :pid
        """),
        {"pid": project_id}
    )

    row = result.fetchone()
    return row[0] if row else None


# =========================================================
# 🔥 MAP VERRA CATEGORY → SECTOR
# =========================================================
def map_verra_category(category: str):

    if not category:
        return "renewables"

    category = category.strip().lower()

    # 🌳 AFOLU → forestry
    if "agriculture forestry and other land use" in category:
        return "forestry"

    if any(k in category for k in ["forestry", "afolu", "redd", "arr", "ifm"]):
        return "forestry"

    return "renewables"


# =========================================================
# 🔥 MAP GS TYPE → SECTOR
# =========================================================
def map_gs_type(project_type: str):

    if not project_type:
        return "renewables"

    project_type = project_type.strip().lower()

    # 🌳 Forestry keywords
    forestry_keywords = [
        "forestry",
        "afforestation",
        "reforestation",
        "redd",
        "ifm",
        "arr",
        "a/r",
        "land use"
    ]

    if any(k in project_type for k in forestry_keywords):
        return "forestry"

    return "renewables"


# =========================================================
# 🔥 MAIN UNIFIED FUNCTION
# =========================================================
def get_project_sector(db: Session, project_id: str):

    # =====================================================
    # 🔥 VERRA PROJECT
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
    # 🔥 GOLD STANDARD PROJECT
    # =====================================================
    elif project_id.startswith("GS"):

        project_type = get_gs_project_type(db, project_id)
        sector = map_gs_type(project_type)

        return {
            "project_id": project_id,
            "source": "gs",
            "raw_type": project_type,
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