from sqlalchemy import Column, Integer, Text, Float, ForeignKey, TIMESTAMP
from sqlalchemy.orm import declarative_base
from sqlalchemy.sql import func

Base = declarative_base()


# =========================================================
# 🔥 PROJECT SCORES
# =========================================================
class ProjectScore(Base):
    __tablename__ = "project_scores"

    project_id = Column(Text, primary_key=True)
    sector = Column(Text)
    final_score = Column(Float)

    created_at = Column(TIMESTAMP, server_default=func.now())
    updated_at = Column(TIMESTAMP, server_default=func.now(), onupdate=func.now())


# =========================================================
# 🔥 SDG SCORES
# =========================================================
class ProjectSDGScore(Base):
    __tablename__ = "project_sdg_scores"

    id = Column(Integer, primary_key=True, autoincrement=True)

    project_id = Column(
        Text,
        ForeignKey("project_scores.project_id", ondelete="CASCADE")
    )

    sdg = Column(Integer)
    score = Column(Float)