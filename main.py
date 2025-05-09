import os
import logging
from typing import Dict, Any, Optional

from dotenv import load_dotenv
from mcp.server.fastmcp import FastMCP
from src.services.jd_service import jd_generate
from src.services.resume_scoring import ResumeScorer
from src.services.pdf_parser import PdfParser
from src.routes.cake import scrape_persons_cake_endpoint

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

load_dotenv()
SERVER_NAME = "CakeScraperServer"
SERVER_HOST = os.environ.get("SERVER_HOST", "0.0.0.0")
SERVER_PORT = int(os.environ.get("SERVER_PORT", 1102))

mcp = FastMCP(name=SERVER_NAME, host=SERVER_HOST, port=SERVER_PORT)
pdf_parser = PdfParser("Element/ner_700i_500e_4_512.onnx", "Element/lilt-tokenizer", "Element/classes.yaml")

# Dummy implementations replacing Supabase
async def workflow_update_step(user_id: str, workflow_id: str, step: str, status: str, detail: Optional[str] = None):
    data = {
        "user_id": user_id,
        "workflow_id": workflow_id,
        "step": step,
        "status": status,
        "detail": detail or "",
    }
    logger.info(f"[Mock] Writing to workflow_steps: {data}")
    return {"mock": "ok", "data": data}

async def workflow_append_chat(user_id: str, workflow_id: str, message: str, sender: str = "system"):
    data = {
        "user_id": user_id,
        "workflow_id": workflow_id,
        "message": message,
        "sender": sender,
    }
    logger.info(f"[Mock] Writing to chat_history: {data}")
    return {"mock": "ok", "data": data}

@mcp.tool()
async def collect_cvs(
    job_name: str,
    location: str,
    amount_people: int = 3,
    user_id: Optional[str] = None,
    workflow_id: Optional[str] = None,
) -> Dict[str, Any]:
    step_name = "collect_cvs"
    if user_id and workflow_id:
        await workflow_update_step(user_id, workflow_id, step_name, "pending")
    try:
        pcv = await scrape_persons_cake_endpoint(
            keyword=job_name,
            location=location,
            max_links_person=amount_people
        )
        if user_id and workflow_id:
            await workflow_update_step(user_id, workflow_id, step_name, "finished")
            await workflow_append_chat(user_id, workflow_id, f"Collected {len(pcv.get('result', []))} CVs for {job_name} in {location}.", sender="system")
        return {
            "status": "success",
            "summary": f"Collected {len(pcv.get('result', []))} CVs for {job_name} in {location}.",
            "result": pcv.get("result", []),
        }
    except Exception as e:
        logger.error(f"Error collecting CVs: {e}", exc_info=True)
        if user_id and workflow_id:
            await workflow_update_step(user_id, workflow_id, step_name, "error", detail=str(e))
            await workflow_append_chat(user_id, workflow_id, f"Error collecting CVs: {str(e)}", sender="system")
        return {
            "status": "error",
            "summary": f"Error collecting CVs: {str(e)}",
            "result": []
        }

@mcp.tool()
async def rank_cvs(
    job_name: str,
    extra_information: Optional[str] = None,
    resume_dir: str = "data/CV_cake",
    user_id: Optional[str] = None,
    workflow_id: Optional[str] = None,
) -> Dict[str, Any]:
    from src.models.resume_entity import ScoreFactor
    step_name = "rank_cvs"
    if user_id and workflow_id:
        await workflow_update_step(user_id, workflow_id, step_name, "pending")
    try:
        jd = jd_generate(job_name, extra_information or "")
        jd_dict = jd.model_dump()
        scorer = ResumeScorer(pdf_parser, max_length=512)
        score_list, _, _ = scorer.score_from_dir(resume_dir, ScoreFactor(**jd_dict))
        ranked = sorted(score_list, key=lambda x: x.total, reverse=True)
        result = [
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
        if user_id and workflow_id:
            await workflow_update_step(user_id, workflow_id, step_name, "finished")
            await workflow_append_chat(user_id, workflow_id, f"Ranked {len(result)} CVs for {job_name}.", sender="system")
        return {
            "status": "success",
            "summary": f"Ranked {len(result)} CVs for {job_name}.",
            "ranked_cvs": result,
        }
    except Exception as e:
        logger.error(f"Error ranking CVs: {e}", exc_info=True)
        if user_id and workflow_id:
            await workflow_update_step(user_id, workflow_id, step_name, "error", detail=str(e))
            await workflow_append_chat(user_id, workflow_id, f"Error ranking CVs: {str(e)}", sender="system")
        return {
            "status": "error",
            "summary": f"Error ranking CVs: {str(e)}",
            "ranked_cvs": []
        }

if __name__ == "__main__":
    logger.info(f"Starting MCP server: {SERVER_NAME} on {SERVER_HOST}:{SERVER_PORT}")
    mcp.run(transport="sse")