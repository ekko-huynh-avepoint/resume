from __future__ import annotations

from pydantic import BaseModel


class Word(BaseModel):
    id: str
    text: str
    bbox: list[float]  # [x0, y0, x1, y1]


class Line(BaseModel):
    id: str
    text: str
    bbox: list[float]
    words: list[Word]


class Page(BaseModel):
    id: str
    lines: list[Line]
    line_count: int


class Document(BaseModel):
    id: str
    pdf_path: str
    pages: list[Page]

