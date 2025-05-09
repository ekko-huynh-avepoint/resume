import os
import requests
from dotenv import load_dotenv
load_dotenv()



BROWSERLESS_URL = os.environ.get("BROWSERLESS_URL")
BROWSERLESS_TOKEN = os.environ.get("BROWSERLESS_TOKEN")

def browserless_pdf(url, output_path, file_name="output.pdf"):
    """
    Save a PDF of the given URL using Browserless service.
    """
    endpoint = f"{BROWSERLESS_URL}/pdf?token={BROWSERLESS_TOKEN}"
    payload = {
        "url": url,
        "options": {
            "printBackground": True,
            "format": "A4",
            "margin": {
                "top": "10mm",
                "right": "10mm",
                "bottom": "10mm",
                "left": "10mm"
            }
        }
    }
    response = requests.post(endpoint, json=payload, timeout=120)
    response.raise_for_status()
    os.makedirs(output_path, exist_ok=True)  # <-- create folder if not exist
    pdf_output_path = os.path.join(output_path, file_name)
    with open(pdf_output_path, "wb") as f:
        f.write(response.content)
    return pdf_output_path