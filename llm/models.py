from typing import Literal
from pydantic import BaseModel, Field

class SDG7Evidence(BaseModel):
    """Action items extracted from a meeting transcript."""
    evidences: list[str] = Field(description="Extracted supporting evidences as a list of supporting sentences")
    justification: str = Field(description="Short justification (1–3 sentences)")
    score: Literal[0, 1, 2, 3] = Field(
        description="""Assess whether the indicator is:
            0 = Not mentioned
            1 = Mentioned only qualitatively
            2 = Quantified
            3 = Quantified and verified (source, methodology, audit, official dataset)"""
        )

