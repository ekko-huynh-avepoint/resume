from __future__ import annotations

from pydantic import BaseModel
from typing import List

class Word(BaseModel):
    id: str
    text: str
    bbox: list[float]
    ner_tag: str = ""


class Line(BaseModel):
    id: str
    text: str
    bbox: list[float]
    words: list[Word]
    ner_tag: str = ""


class Page(BaseModel):
    id: str
    lines: list[Line]
    line_count: int


class Document(BaseModel):
    id: str
    pdf_path: str
    pages: list[Page]


class TokenizedObject(BaseModel):
    input_ids: List[List[int]]
    bbox: List[List[List[float]]]
    attention_mask: List[List[int]]
