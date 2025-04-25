import os
import json
from dotenv import load_dotenv  
import csv
import sys
import re

sys.path.append(os.path.join(os.path.dirname(__file__), ".."))
load_dotenv("/.env")

ERROR_LOG_FOLDER = os.getenv("ERROR_LOG_FOLDER", "logs/")
LINKS_PERSON_FILE = os.getenv("LINKS_PERSON_FILE", "data/links_person.csv")


def log_error(message: str, file_name: str):
    """
    Log an error message to a timestamped file.

    Args:
        message (str): The error message to be logged.

    Returns:
        None
    """
    path_log = os.path.join(ERROR_LOG_FOLDER, file_name)
    with open(path_log, "a", encoding='utf-8') as f:
        f.write(message + "\n")


def save_dict_data_to_txt(data, file_path):
    """
    Append dictionary data as a JSON string to a text file.

    Args:
        data (dict): The dictionary to be serialized and saved.
        file_path (str): Path to the text file where the data will be appended.

    Returns:
        None
    """
    with open(file_path, 'a', encoding='utf-8') as file:
        file.write(json.dumps(data, ensure_ascii=False) + "\n")

def save_link_to_csv(link, keyword=None, location=None, level=None, filename=LINKS_PERSON_FILE):
    """
    Save a link and related metadata to a CSV file.

    Args:
        link (str): The link to save.
        keyword (str, optional): The associated keyword. Defaults to None.
        location (str, optional): The associated location. Defaults to None.
        level (str, optional): The associated level. Defaults to None.
        filename (str): The name of the CSV file. Defaults to LINKS_PERSON_FILE.
    """
    print("Saving link to CSV file...", filename)

    # Create the file with headers if it doesn't exist
    if not os.path.exists(filename):
        print("Creating new CSV file...")
        with open(filename, mode="w", newline="", encoding="utf-8") as file:
            writer = csv.writer(file)
            writer.writerow(["Keyword", "Location", "Level", "Link"])
    else:
        print("CSV file already exists...")

    # Append data to the CSV file
    with open(filename, mode="a", newline="", encoding="utf-8") as file:
        writer = csv.writer(file)
        # Add a row with the data
        writer.writerow([
            keyword if keyword else "",
            location if location else "",
            level if level else "",
            link if link else "",
        ])

def get_data_from_col_from_csv(file_path: str, col: str = 'Link') -> list:
    """
    Extract data from a specific column in a CSV file.

    Args:
        file_path (str): Path to the CSV file.
        col (str): The column name to extract data from (default is 'Link').

    Returns:
        list: A list of values from the specified column.
    """
    data = []
    with open(file_path, mode='r', encoding='utf-8') as file:
        reader = csv.DictReader(file)
        for row in reader:
            if col in row:  # Ensure the column exists in the row
                data.append(row[col])
    return data

def sanitize_filename(url: str) -> str:
    """
    Sanitize a URL to create a valid filename.

    Args:
        url (str): The input URL or string to sanitize.

    Returns:
        str: A sanitized filename with a .pdf extension.
    """
    # Replace invalid characters for filenames with underscores
    sanitized_url = re.sub(r'[<>:"/\\|?*.-]', '_', url)
    # Append the .pdf extension
    return sanitized_url + ".pdf"