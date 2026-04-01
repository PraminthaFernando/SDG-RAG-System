from dataclasses import dataclass
from typing import List, Dict, Optional


@dataclass
class PageContent:
    page: int
    text: str


@dataclass
class IngestedDocument:
    pid: Optional[str]
    name: str
    pages: List[PageContent]