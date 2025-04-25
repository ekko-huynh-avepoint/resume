from __future__ import annotations

import json
import hashlib

import fitz
from PIL import Image, ImageDraw

from src.models.pdf2text_entity import Document, Page, Word, Line


class PDFProcessor:
    """Extract text and coordinates from a PDF file."""

    def __init__(self):
        """Initialize the PDFProcessor object."""

    def extract_text_and_coordinates(self, pdf_path: str) -> Document:
        """Extract text and coordinates from the PDF file."""
        doc = fitz.open(pdf_path)

        document = Document(
            id=hashlib.sha256(pdf_path.encode()).hexdigest(), pdf_path=pdf_path, pages=[]
        )
        for page_num in range(len(doc)):
            page = doc[page_num]
            page_id = hashlib.sha256(
                pdf_path.encode() + str(page_num).encode()
            ).hexdigest()
            page_data = Page(id=page_id, lines=[], line_count=0)

            # Extract text and coordinates
            words = page.get_text("words")  # [(x0, y0, x1, y1, text), ...]

            # Sort the words by the y0 coordinate (top of the word)
            words.sort(key=lambda x: x[1])  # Sort by the y0 coordinate (top of the word)

            line_id = 0
            current_line_words = []
            try:
                current_line_y = words[0][1]
            except IndexError:
                continue
            for word_data in words:
                word_id = hashlib.sha256(
                    page_id.encode() + word_data[4].encode()
                ).hexdigest()
                word = Word(id=word_id, text=word_data[4], bbox=word_data[:4])

                # Check if the word is on the same line
                if abs(word_data[1] - current_line_y) < 5:
                    current_line_words.append(word)
                else:
                    # Create a new line
                    line_text = " ".join([w.text for w in current_line_words])
                    line_bbox = self.get_line_bbox(current_line_words)
                    line = Line(
                        id=hashlib.sha256(str(line_id).encode()).hexdigest(),
                        text=line_text,
                        bbox=line_bbox,
                        words=current_line_words,
                    )
                    page_data.lines.append(line)
                    page_data.line_count += 1
                    line_id += 1

                    # Start a new line
                    current_line_words = [word]
                    current_line_y = word_data[1]
            # Add the last line
            if current_line_words:
                line_text = " ".join([w.text for w in current_line_words])
                line_bbox = self.get_line_bbox(current_line_words)
                line = Line(
                    id=hashlib.sha256(str(line_id).encode()).hexdigest(),
                    text=line_text,
                    bbox=line_bbox,
                    words=current_line_words,
                )
                page_data.lines.append(line)
                page_data.line_count += 1
            document.pages.append(page_data)

        doc.close()

        return document

    def get_line_bbox(self, words: list[Word]) -> list[float]:
        """Get the bounding box of a line."""
        x0 = min(word.bbox[0] for word in words)
        y0 = min(word.bbox[1] for word in words)
        x1 = max(word.bbox[2] for word in words)
        y1 = max(word.bbox[3] for word in words)
        return [x0, y0, x1, y1]

    def save_to_json(self, document: Document, output_folder: str = "output") -> None:
        """Save the text and coordinates to a JSON file."""
        file_name = document.pdf_path.split("/")[-1].replace(".pdf", ".json")
        file_path = f"{output_folder}/{file_name}"
        with open(file_path, "w", encoding="utf-8") as json_file:
            json.dump(document.dict(), json_file, ensure_ascii=False, indent=4)

        print(f"Text and coordinates saved to: {output_folder}/{file_path}")

    def draw_bounding_boxes(
        self, document: Document, output_folder: str = "output"
    ) -> None:
        """Draw bounding boxes around the text in the PDF file."""
        doc = fitz.open(document.pdf_path)
        for page_num, page_data in enumerate(document.pages):
            page = doc[page_num]
            text_data = page_data.lines

            # Create an image from the page
            pix = page.get_pixmap()
            img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
            draw = ImageDraw.Draw(img)

            # Draw bounding boxes
            for line in text_data:
                for word in line.words:
                    bbox = word.bbox
                    draw.rectangle(bbox, outline="red", width=2)

            # Save the image
            file_name = f"{document.pdf_path.split('/')[-1].replace('.pdf', '')}_page_{page_num + 1}.png"
            output_path = f"{output_folder}/{file_name}"
            img.save(output_path)
            print(f"Saved: {output_path}")

        doc.close()

    def parse_json_file_to_document(self, file_path: str) -> Document:
        """Parse the JSON file to a Document object."""
        with open(file_path, encoding="utf-8") as json_file:
            data = json.load(json_file)

        return Document.parse_obj(data)


# Main function
def main() -> None:
    # Process the PDF file

    # 1. Extract text and coordinates then save to a JSON file and draw bounding boxes
    pdf_path = "path_to_pdf_file"
    output_folder = "data_output"
    pdf_processor = PDFProcessor()
    doc = pdf_processor.extract_text_and_coordinates(pdf_path)
    pdf_processor.save_to_json(doc, output_folder)
    pdf_processor.draw_bounding_boxes(doc, output_folder)

    # # 2. Parse the JSON file to a Document object
    # output_folder = "data_output_test"
    # pdf_processor = PDFProcessor()
    # doc = pdf_processor.parse_json_file_to_document("data_output/https___www_cake_me_0reno_locale=en.json")
    # pdf_processor.save_to_json(doc, output_folder)


if __name__ == "__main__":
    main()
