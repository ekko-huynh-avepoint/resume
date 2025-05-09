import base64
from datetime import datetime
from dotenv import load_dotenv
from fastapi import APIRouter, HTTPException
import time
import asyncio
import sys
import os
from src.utils.file_utils import sanitize_filename, save_dict_data_to_txt, log_error
# from src.utils.save_to_db import es_client
from src.services.cake_service import crawl_links_person_cake_google, ProfileCake, html_to_pdf, crawl_job_listings, \
    JobDescriptionCake

sys.path.append(os.path.join(os.path.dirname(__file__), ".."))
load_dotenv("/.env")

PROFILE_PERSONS_FILE = os.getenv("PROFILE_PERSONS_FILE", "data/profile_persons.txt")
INDEX_FOR_JOB_CAKE = os.getenv("INDEX_FOR_JOB_CAKE")
INDEX_FOR_PROFILE_CAKE = os.getenv("INDEX_FOR_PROFILE_CAKE")
PREFIX_FOR_FILE_PDF_PROFILE_CAKE = os.getenv("PREFIX_FOR_FILE_PDF_PROFILE_CAKE")


async def scrape_jobs_cake_endpoint(
        keyword: str,
        location: str = "Vietnam",
        max_pages: int = 100,
        max_jobs: int = 25
):
    list_of_jobs = []
    try:
        start_time = time.time()
        links_job = crawl_job_listings(keyword, location, max_pages, max_jobs, None)
        if len(links_job) > 0:
            for link in links_job:
                job_data = JobDescriptionCake(link, keyword, None).crawl_job()
                # es_client.save_job_description(job_data, index_name=INDEX_FOR_JOB_CAKE)
                list_of_jobs.append(job_data)

        end_time = time.time() - start_time
        return {
            "message": f"{len(list_of_jobs)} Job: {keyword} scraping finished successfully with {end_time} seconds.",
            "total_jobs": list_of_jobs}

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"An error occurred: {e}")


async def scrape_persons_cake_endpoint(
        keyword: str = "ai engineer",
        location: str = "Malaysia",
        max_links_person: int = 3,
        cv_pdf_folder: str = "data",
        worker: int = 3
):
    cv_pdf_folder_new = os.path.join(cv_pdf_folder, "CV_cake")
    if not os.path.exists(cv_pdf_folder_new):
        os.makedirs(cv_pdf_folder_new)

    current_time = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    try:
        start_time = time.time()
        persons_dict = []
        links = crawl_links_person_cake_google(keyword, location, max_links_person, file_log_name=None)

        async def process_link(link):
            """
            Process a single link to scrape person data and convert it to PDF.
            """
            async with asyncio.Semaphore(worker):
                person_dict, link_resume = ProfileCake(link, None).crawl_profile()
                persons_dict.append(person_dict)
                # save_dict_data_to_txt(person_dict, PROFILE_PERSONS_FILE)
                # es_client.save_profile(person_dict, index_name=INDEX_FOR_PROFILE_CAKE)
                await html_to_pdf(link, link_resume, cv_pdf_folder_new)

        # Run multiple workers concurrently
        await asyncio.gather(*(process_link(link) for link in links))

        end_time = time.time() - start_time
        return {
            "message": f"Persons scraping finished successfully => {len(persons_dict)} persons with {end_time:.2f} seconds.",
            "persons_dict": persons_dict}

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"An error occurred: {e}")


async def scrape_one_person_cake_endpoint(
        profile_url: str,
        cv_pdf_folder: str = "data"
):
    cv_pdf_folder = os.path.join(cv_pdf_folder, "CV_cake")
    if not os.path.exists(cv_pdf_folder):
        os.makedirs(cv_pdf_folder)

    try:
        start_time = time.time()

        semaphore = asyncio.Semaphore(1)
        result = []

        async def process_link(profile_url):
            async with semaphore:
                try:
                    person_dict, link_resume = ProfileCake(profile_url, None).crawl_profile()
                    result.append(person_dict)
                    save_dict_data_to_txt(person_dict, PROFILE_PERSONS_FILE)
                    await html_to_pdf(profile_url, link_resume, cv_pdf_folder)
                except Exception:
                    pass

        await asyncio.gather(process_link(profile_url))

        pdf_file_path = os.path.join(cv_pdf_folder, sanitize_filename(profile_url))

        i = 0
        while True:
            if os.path.exists(pdf_file_path) or i == 10:
                break
            time.sleep(1)
            i += 1

        try:
            with open(pdf_file_path, "rb") as pdf_file:
                pdf_binary = pdf_file.read()
                pdf_base64 = base64.b64encode(pdf_binary).decode("utf-8")
        except Exception:
            pdf_base64 = ""

        end_time = time.time() - start_time
        return {
            "message": f"Person scraping finished successfully with {end_time:.2f} seconds.",
            "person_dict": result,
            "pdf_base64": pdf_base64
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"An error occurred: {e}")
