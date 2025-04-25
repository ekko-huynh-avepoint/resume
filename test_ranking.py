from __future__ import annotations

import json
from pathlib import Path

from src.models.resume_entity import ScoreFactor
from src.services.pdf_parser import PdfParser
from src.services.resume_scoring import ResumeScorer

resume_folder = "examples/pdf"
tokenizer_path = "Element/lilt-tokenizer"
model_path = "Element/ner_700i_500e_4_512.onnx"
# pdf_path = "data/CV_cake/https___www_cake_me_me_afauzanaqil_locale=en.pdf"
classes_path = "Element/classes.yaml"

# Input the necessary path to the Parser
parser = PdfParser(
    tokenizer_path=tokenizer_path,
    model_path=model_path,
    classes_path=classes_path
)

scorer = ResumeScorer(
    max_length=512,
    pdf_parser=parser
)

# with Path("examples/sample_jd.json").open(encoding="utf-8") as f:
#     jd_dict = json.load(f)
# sample_jd = ScoreFactor(**jd_dict)

job_description = ScoreFactor(
    hardskill=["business analysis", "requirement gathering", "UML", "process modeling"],
    softskill=["communication", "problem solving"],
    education=["bachelor", "university"],
    experience=["3 years", "4 years", "5 years"],
    project=["BA project"],
    language=["english"]
)

score = scorer.score_from_dir(resume_folder, job_description, parser)
print(f"Scores: {score}")
