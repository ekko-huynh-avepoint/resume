import os
import openai
import logging
from dotenv import load_dotenv
from src.models.resume_entity import ScoreFactor
import ast

load_dotenv()
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY")
logger = logging.getLogger(__name__)

def jd_generate(
    jobName: str,
    extra: str = "",
) -> ScoreFactor:
    client = openai.OpenAI(api_key=OPENAI_API_KEY)
    system_prompt = (
        "You are an expert HR assistant. "
        "Given a job title and some requirements, generate a Python dictionary with exactly 6 keys: "
        "'hardskill', 'softskill', 'education', 'experience', 'project', 'language'. "
        "Each value must be a concise, relevant list of strings for that category. "
        "Do NOT include any explanation, markdown, or extra text—return ONLY a valid Python dictionary. "
        "Example: "
        "{'hardskill': ['requirement gathering', 'UML'], 'softskill': ['communication'], "
        "'education': ['bachelor'], 'experience': ['3 years'], 'project': ['BA project'], 'language': ['Chinese']}"
    )
    user_prompt = (
        f"Job title: {jobName}\n"
        f"Additional requirements: {extra}\n"
        "Return only the Python dictionary."
    )

    completion = client.chat.completions.create(
        model="gpt-4.1-mini-2025-04-14",
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ],
        stream=False,
        temperature=0.2,
        top_p=0.95,
        max_tokens=1000
    )

    if completion.choices and completion.choices[0].message:
        content = completion.choices[0].message.content
        finish_reason = completion.choices[0].finish_reason
        if finish_reason == "length":
            logger.warning(
                f"OpenAI response was truncated due to max_tokens limit (1000). Parsing might fail.")
        content = content.strip() if content else ""
    else:
        logger.error("OpenAI API call returned no content or unexpected structure.")
        raise ValueError("No content returned from OpenAI API.")

    try:
        jd_dict = ast.literal_eval(content)
        return ScoreFactor(**jd_dict)
    except Exception as err:
        logger.error(f"Could not parse LLM response: {content}\nError: {err}")
        raise ValueError(f"Could not parse LLM response: {content}\nError: {err}")
#
# if __name__ == "__main__":
#     logging.basicConfig(level=logging.INFO)
#     job_name = "Business Analyst"
#     extra_requirements = "3-5 years experience, language is Chinese, familiar with UML and process modeling"
#     try:
#         jd = jd_generate(job_name, extra_requirements)
#         print("Generated Job Description (ScoreFactor):")
#         print(jd)
#         print("As dict:")
#         print(jd.model_dump())
#     except Exception as e:
#         print("Error:", e)