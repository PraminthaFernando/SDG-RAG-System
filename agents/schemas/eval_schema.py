from pydantic import BaseModel, Field

class JudgeResult(BaseModel):
    summary: str
    score: int = Field(ge=0, le=2)
    justification: str
    confidence: float | None = None


class DebateResult(BaseModel):
    summary: str
    score: int = Field(ge=0, le=2)
    justification: str
    agreement: bool

class Summary(BaseModel):
    summary: str