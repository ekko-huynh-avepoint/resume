from __future__ import annotations

import io
import os
import logging

import numpy as np
from sklearn.metrics.pairwise import cosine_similarity
from sklearn.feature_extraction.text import TfidfVectorizer

from src.models.resume_entity import PdfMetadata, ScoreFactor, Score
from src.services.pdf_parser import PdfParser

def get_content_type(filename: str) -> str:
    ext = os.path.splitext(filename)[1].lower()
    return {
        ".pdf": "application/pdf",
        ".png": "image/png",
        ".jpg": "image/jpeg",
        ".jpeg": "image/jpeg",
    }.get(ext, "application/octet-stream")

def upload_pdf_binary(
    s3_client,
    s3_bucket_name: str,
    pdf_content: bytes,
    object_name: str,
    prefix: str = "CVs/",
) -> str | None:
    """Upload a PDF file as a binary stream to MinIO."""
    try:
        pdf_stream = io.BytesIO(pdf_content)
        content_type = get_content_type(object_name)
        s3_client.upload_fileobj(
            pdf_stream,
            s3_bucket_name,
            prefix + object_name,
            ExtraArgs={"ContentType": content_type},
        )
        return f"s3://{s3_bucket_name}/{prefix}{object_name}"
    except Exception as e:
        logging.error(f"Error uploading PDF: {e}")
        return None

class ResumeScorer:
    def __init__(
        self,
        pdf_parser: PdfParser,
        max_length: int = 512,
    ) -> None:
        self.vectorizer = TfidfVectorizer(stop_words="english", ngram_range=(1, 1))
        self.pdf_parser = pdf_parser
        self.info_to_score = {
            "B-Hardskill": "hardskill",
            "B-Softskill": "softskill",
            "B-Education": "education",
            "B-Experience": "experience",
            "B-Language": "language",
            "B-Project": "project",
        }
        self.max_length = max_length

    def fit(
        self, resumes_list: list[PdfMetadata], job_description: ScoreFactor
    ) -> list[ScoreFactor]:
        all_lines = []
        resumes_sections_list = []
        for resume_doc in resumes_list:
            resume_section_mapping = {key: [] for key in self.info_to_score.values()}
            resume_section_mapping.update({"id": resume_doc.id, "email": "", "phone": "", "name": "", "location": ""})
            for page in resume_doc.data.pages:
                for line in page.lines:
                    all_lines.append(line.text)
                    line_section_mapping = {}
                    for word in line.words:
                        if word.ner_tag == "B-Email":
                            resume_section_mapping["email"] += " " + word.text
                        elif word.ner_tag == "B-Phone":
                            resume_section_mapping["phone"] += " " + word.text
                        elif word.ner_tag == "B-Name":
                            resume_section_mapping["name"] += " " + word.text
                        elif word.ner_tag == "B-Address":
                            resume_section_mapping["location"] += " " + word.text
                        if word.ner_tag in self.info_to_score:
                            line_section_mapping.setdefault(word.ner_tag, []).append(word.text)
                    for key, value in line_section_mapping.items():
                        resume_section_mapping[self.info_to_score[key]].append(" ".join(value))
            resumes_sections_list.append(ScoreFactor(**resume_section_mapping))
        all_lines.extend(
            text for section in job_description.dict().values() if isinstance(section, list) for text in section
        )
        self.vectorizer.fit(all_lines)
        return resumes_sections_list

    def compare(
        self,
        resumes_list: list[ScoreFactor],
        job_description: ScoreFactor,
        threshold: float,
    ) -> tuple[list[Score], list[ScoreFactor]]:
        fields = job_description.__fields__.keys()
        jd_dict = job_description.dict()
        score_list: list[Score] = []
        for resume_idx, resume in enumerate(resumes_list):
            resume_score = Score(
                id=resume.id,
                save_path=resume.save_path,
                email=resume.email,
                phone=resume.phone,
                location=resume.location,
                name=resume.name,
                job_title=resume.job_title,
            )
            resume_dict = resume.dict()
            for field in fields:
                if field in {"id", "save_path", "email", "phone", "location", "name", "job_title"}:
                    continue
                jd_sentences = jd_dict[field]
                resume_sentences = resume_dict[field]
                if not resume_sentences or not jd_sentences:
                    continue
                all_sentences = resume_sentences + jd_sentences
                tfidf_matrix = self.vectorizer.transform(all_sentences)
                resume_tfidf = tfidf_matrix[: len(resume_sentences)]
                jd_tfidf = tfidf_matrix[len(resume_sentences):]
                similarity_matrix = cosine_similarity(resume_tfidf, jd_tfidf)
                sentence_scores = np.max(similarity_matrix, axis=1) if similarity_matrix.size else np.array([0])
                score = np.sum(sentence_scores) if sentence_scores.size else 0
                setattr(resume_score, field, score)
                resume_dict[field] = [
                    f"{sent}###{sentence_scores[idx]:.4f}" for idx, sent in enumerate(resume_sentences)
                ]
            resumes_list[resume_idx] = ScoreFactor(**resume_dict)
            score_list.append(resume_score)
        return score_list, resumes_list

    def score_from_dir(
        self,
        resume_dir: str,
        job_description: ScoreFactor,
        threshold: float = 0.4,
        save_to_s3: bool = False,
        s3_client=None,
        s3_bucket: str = None,
        s3_prefix: str = "CVs/",
    ) -> tuple:
        resume_paths = [
            os.path.join(resume_dir, file_name) for file_name in os.listdir(resume_dir)
        ]
        resume_list: list[PdfMetadata] = []
        for resume_path in resume_paths:
            data = self.pdf_parser.parse(resume_path, max_length=self.max_length)
            resume_list.append(PdfMetadata(id=resume_path, data=data))
            if save_to_s3:
                ext_file = os.path.splitext(data.pdf_path)[1].lower()
                if ext_file == ".pdf":
                    pdf_content = self.pdf_parser.visualize_on_pdf(data, resume_path)
                elif ext_file in {".png", ".jpg", ".jpeg"}:
                    pdf_content = self.pdf_parser.visualize_on_image(data, resume_path)
                else:
                    logging.warning(f"Unsupported file format: {data.pdf_path}")
                    continue
                upload_pdf_binary(
                    s3_client=s3_client,
                    s3_bucket_name=s3_bucket,
                    pdf_content=pdf_content,
                    object_name=os.path.basename(resume_path).replace(ext_file, "") + "_hightlight" + ext_file,
                    prefix=s3_prefix,
                )
        return self.score(resume_list, job_description, threshold)

    def score(
        self,
        resume_list: list[PdfMetadata],
        job_description: ScoreFactor,
        threshold: float = 0.4,
    ) -> tuple[list[Score], list[ScoreFactor], list[ScoreFactor]]:
        resume_section_list = self.fit(resume_list, job_description)
        score_list, resume_section_list_add_score = self.compare(
            resume_section_list, job_description, threshold
        )
        for score in score_list:
            score.total = (
                score.hardskill
                + score.softskill
                + score.education
                + score.experience
                + score.project
                + score.language
            )
        return score_list, resume_section_list, resume_section_list_add_score