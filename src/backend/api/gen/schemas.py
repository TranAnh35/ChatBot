from pydantic import BaseModel
from typing import List

class WebSearchItem(BaseModel):
    title: str
    link: str
    snippet: str

class WebResults(BaseModel):
    results: List[List[WebSearchItem]]