from __future__ import annotations

from pydantic import BaseModel
from src.models.pdf2tags_entity import Document


class PdfMetadata(BaseModel):
    id: str = ""
    data: Document


class ScoreFactor(BaseModel):
    id: str = ""
    name: str = ""
    location: str = ""
    save_path: str = ""
    job_title: str = ""
    email: str = ""
    phone: str = ""
    hardskill: list[str] = []
    softskill: list[str] = []
    education: list[str] = []
    experience: list[str] = []
    language: list[str] = []
    project: list[str] = []
    # honor: List[str] = []
    # certificate: List[str] = []
    # publication: List[str] = []


class Score(BaseModel):
    id: str = ""
    name: str = ""
    location: str = ""
    save_path: str = ""
    job_title: str = ""
    email: str = ""
    phone: str = ""
    hardskill: float = 0.0
    softskill: float = 0.0
    education: float = 0.0
    experience: float = 0.0
    language: float = 0.0
    project: float = 0.0
    total: float = 0.0
    # honor: float = 0.0
    # certificate: float = 0.0
    # publication: float = 0.0