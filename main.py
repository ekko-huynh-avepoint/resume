from mcp.server.fastmcp import FastMCP
import mcp.types as types
from typing import Optional

from src.models.resume_entity import ScoreFactor
from src.services.jd_service import jd_generate
from src.services.resume_scoring import ResumeScorer
from src.services.pdf_parser import PdfParser
from src.routes.cake import scrape_persons_cake_endpoint

pdf_parser = PdfParser("Element/ner_700i_500e_4_512.onnx", "Element/lilt-tokenizer", "Element/classes.yaml")
mcp = FastMCP(name="CakeScraperServer", host="0.0.0.0", port=1102)

# 1. Collect CVs
@mcp.tool()
async def collect_cvs(
    job_name: str,
    location: str,
    amount_people: int = 3,
) -> dict:
    pcv = await scrape_persons_cake_endpoint(
        keyword=job_name,
        location=location,
        max_links_person=amount_people
    )
    return pcv

# 3. Rank CVs
@mcp.tool()
async def rank_cvs(
    job_name: str,
    extra_information: Optional[str] = None,
    resume_dir: str = "data/CV_cake",
) -> list:
    jd = jd_generate(job_name, extra_information or "")
    jd_dict = jd.model_dump()

    scorer = ResumeScorer(pdf_parser, max_length=512)
    score_list, _, _ = scorer.score_from_dir(resume_dir, ScoreFactor(**jd_dict))
    ranked = sorted(score_list, key=lambda x: x.total, reverse=True)
    return [
        {
            "id": s.id,
            "name": s.name,
            "email": s.email,
            "phone": s.phone,
            "location": s.location,
            "total_score": s.total,
            "hardskill": s.hardskill,
            "softskill": s.softskill,
            "education": s.education,
            "experience": s.experience,
            "project": s.project,
            "language": s.language,
        }
        for s in ranked
    ]

    
if __name__ == "__main__":
    mcp.run(transport="sse")