from dataclasses import dataclass
from typing import List, Dict


@dataclass
class PageContent:
    page: int
    text: str


@dataclass
class IngestedDocument:
    pid: str
    name: str
    pages: List[PageContent]