from __future__ import annotations

from pathlib import Path

from src.services.pdf2text import PDFProcessor


# Define the PDF file path and output folder
pdf_path = "examples/https___www_cake_me_0reno_locale=en.pdf"
output_folder = "data_output"

if not Path(output_folder).exists():
    Path(output_folder).mkdir(parents=True)

# Initialize the processor
pdf_processor = PDFProcessor()

# Step 1: Extract text and coordinates
doc = pdf_processor.extract_text_and_coordinates(pdf_path)

# Step 2: Save the extracted data to a JSON file
pdf_processor.save_to_json(doc, output_folder=output_folder)

# Step 3: Draw bounding boxes on the PDF
pdf_processor.draw_bounding_boxes(doc, output_folder=output_folder)