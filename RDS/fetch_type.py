from sqlalchemy import text
from sqlalchemy.orm import Session


# =========================================================
# 🔥 FETCH PROJECT CATEGORY (FOR SECTOR MAPPING)
# =========================================================
def get_project_category(db: Session, project_id: str):

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
# 🔥 MAP CATEGORY → SECTOR
# =========================================================
def map_category_to_sector(category: str):

    if not category:
        return "renewables"  # default fallback

    category = category.strip().lower()

    # 🔥 AFOLU → forestry
    if category == "agriculture forestry and other land use":
        return "forestry"

    # 🔥 everything else → renewables
    return "renewables"


# =========================================================
# 🔥 MAIN HELPER (ONE CALL)
# =========================================================
def get_project_sector(db: Session, project_id: str):

    category = get_project_category(db, project_id)
    sector = map_category_to_sector(category)

    return {
        "project_id": project_id,
        "project_category": category,
        "sector": sector
    }