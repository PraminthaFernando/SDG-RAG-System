from pydantic import BaseModel, Field
from typing import List, Literal


class Evidence(BaseModel):
    sentence: str = Field(
        description="Exact sentence from the retrieved context that supports the justification(don't change the sentence in the context, just copy it here.)"
    )
    document: str = Field(
        description="Document name containing the extracted sentence"
    )
    page: int = Field(
        description="Page number of the document containing the sentence as a intiger"
    )


class SDGEvaluationResult(BaseModel):
    """
    Evaluation result for a single SDG checklist item.
    """

    evidences: List[Evidence] | list = Field(
        default_factory=list,
        description="Extracted supporting evidence sentences(this a required filed. if score is 0, just return a empty array)"
    )

    justification: str = Field(
        description="Short justification (1–3 sentences explaining the score)"
    )

    score: Literal[0, 1, 2] = Field(
        description="""
        Indicator scoring:
        0 = Not mentioned
        1 = Mentioned qualitatively
        2 = Quantified
        """
    )