import re
import copy
import json
import hashlib
import pathlib
from pathlib import Path

import cv2
import pytesseract

from src.models.pdf2text_entity import Line, Page, Word, Document
from rapidocr_onnxruntime import RapidOCR


class OCRProcessor:
    """OCRProcessor handles text extraction from images using RapidOCR.

    It processes images to extract text along with bounding box coordinates

    and provides functionality to save results in JSON and image formats.
    """

    def __init__(self) -> None:
        self.rapid_ocr = RapidOCR()

    @staticmethod
    def adjust_letter_width(word: str) -> float:
        """Adjust the width of the word based on its characters."""
        adjustment_map = {
            char: adjustment
            for group, adjustment in {
                "QYOASDGHVN$": 0.25,
                "wmM@%2": 0.5,
                "iIl!|:,;.·": -0.75,
                "fzc\\/?": -0.25,
                "rt1": -0.4375,
                "'-": -0.9,
                "T#X": 0.125,
                "sL": -0.125,
                "j()`[]": -0.5,
                " ": -0.8,
                "W": 0.875,
            }.items()
            for char in group
        }
        return sum(adjustment_map.get(char, 0) for char in word)

    def extract_text_and_coordinates(self, file_path: str, mode: str) -> Document:
        """Extract text and coordinates from the file using specified mode."""
        if mode == "rapid":
            return self.extract_text_and_coordinates_rapid(file_path)
        if mode == "tesseract":
            return self.extract_text_and_coordinates_tesseract(file_path)
        return None

    # RapidOCR
    def extract_text_and_coordinates_rapid(self, file_path: str) -> Document:
        """Extract text and coordinates using RapidOCR."""
        image = cv2.cvtColor(cv2.imread(file_path), cv2.COLOR_BGR2GRAY)
        results, _ = self.rapid_ocr(image)
        all_bbox, all_text = self._process_ocr_results(results)
        return self._create_document(file_path, all_bbox, all_text)

    # Tesseract
    def extract_text_and_coordinates_tesseract(self, file_path: str) -> Document:
        """Extract text and coordinates using Tesseract OCR."""
        image = cv2.cvtColor(cv2.imread(file_path), cv2.COLOR_BGR2GRAY)
        data = pytesseract.image_to_data(image, output_type=pytesseract.Output.DICT)

        all_bbox = []
        all_text = []

        n_boxes = len(data["level"])
        for i in range(n_boxes):
            text = data["text"][i].strip()
            if text:
                x = data["left"][i]
                y = data["top"][i]
                w = data["width"][i]
                h = data["height"][i]
                bbox = [[x, y], [x + w, y], [x + w, y + h], [x, y + h]]
                all_bbox.append(bbox)
                all_text.append(text)

        return self._create_document(file_path, all_bbox, all_text)

    def _process_ocr_results(self, results: list) -> tuple:
        """Process OCR results to extract bounding boxes and text."""
        all_bbox = []
        all_text = []
        for bbox, text, _ in results:
            words = self._split_and_merge_words(text)
            len_character = sum(len(word) for word in words) + sum(
                self.adjust_letter_width(word) for word in words
            )
            letter_width = (bbox[1][0] - bbox[0][0]) / len_character
            num_letter = 0
            for word in words:
                word_bbox = self._adjust_word_bbox(bbox, word, letter_width, num_letter)
                all_bbox.append(word_bbox)
                all_text.append(word.strip())
                num_letter += len(word) + self.adjust_letter_width(word)
        return all_bbox, all_text

    @staticmethod
    def _split_and_merge_words(text: str) -> list:
        """Split text and merge symbols/spaces with preceding words."""
        words = re.findall(r"[A-Z]?[a-z]+|[A-Z]+(?![a-z])|\d+|[^a-zA-Z0-9\s]+|\s+", text)
        merged_words = []
        for word in words:
            if merged_words and (re.match(r"^[^\w]", word) or word.isspace()):
                merged_words[-1] += word
            else:
                merged_words.append(word)
        return merged_words

    def _adjust_word_bbox(
        self, bbox: list, word: str, letter_width: float, num_letter: float
    ) -> list:
        """Adjust the bounding box for a word."""
        word_bbox = copy.deepcopy(bbox)
        adjusted_length = len(word) + self.adjust_letter_width(word)
        word_bbox[0][0] = bbox[0][0] + int(letter_width * num_letter)
        word_bbox[1][0] = word_bbox[0][0] + int(letter_width * adjusted_length)
        word_bbox[2][0] = word_bbox[1][0]
        word_bbox[3][0] = word_bbox[0][0]
        return word_bbox

    def _create_document(
        self, file_path: str, all_bbox: list, all_text: list, page: int = 1
    ) -> Document:
        """Create Document object from bounding boxes and text."""
        line_bbox, line_text = self.group_lines(all_bbox, all_text)
        whole_line_bbox = self.merge_line_bboxes(line_bbox)

        # Generate words for all lines in a flat structure
        words_per_line = [
            [
                Word(
                    id=self.generate_id(f"word_{file_path}_{line_idx}_{word_idx}"),
                    text=word_text,
                    bbox=[
                        word_bbox[0][0],
                        word_bbox[0][1],
                        word_bbox[2][0],
                        word_bbox[2][1],
                    ],
                )
                for word_idx, (word_text, word_bbox) in enumerate(
                    zip(line_text[line_idx], line_bbox[line_idx], strict=False)
                )
            ]
            for line_idx in range(len(line_bbox))
        ]

        # Generate lines using precomputed words
        lines = [
            Line(
                id=self.generate_id(f"line_{file_path}_{line_idx}"),
                text=" ".join(word.text for word in words),
                bbox=whole_line_bbox[line_idx],
                words=words,
            )
            for line_idx, words in enumerate(words_per_line)
        ]

        # Generate pages
        pages = [
            Page(
                id=self.generate_id(f"page_{file_path}_{page_idx}"),
                lines=lines,
                line_count=len(lines),
            )
            for page_idx in range(page)
        ]

        return Document(
            id=self.generate_id(file_path),
            pdf_path=file_path,
            pages=pages,
        )

    @staticmethod
    def group_lines(all_bbox: list, all_text: list, spacing: int = 30) -> tuple:
        """Group words into lines based on the y-coordinate."""
        line_positions = sorted({bbox[3][1] for bbox in all_bbox})

        lines_y = [line_positions[0]]
        for y in line_positions[1:]:
            if y > lines_y[-1] + spacing:
                lines_y.append(y)

        line_bbox = [[] for _ in lines_y]
        line_text = [[] for _ in lines_y]

        for bbox, text in zip(all_bbox, all_text, strict=False):
            for i, y in enumerate(lines_y):
                if bbox[3][1] <= y + spacing:
                    line_bbox[i].append(bbox)
                    line_text[i].append(text)
                    break

        return line_bbox, line_text

    @staticmethod
    def merge_line_bboxes(line_bbox: list) -> list:
        """Merge the bounding boxes of words in a line."""
        whole_line_bbox = []
        for boxes in line_bbox:
            merged_bbox = [999999, 999999, 0, 0]
            for box in boxes:
                merged_bbox[0] = min(merged_bbox[0], box[0][0])
                merged_bbox[1] = min(merged_bbox[1], box[0][1])
                merged_bbox[2] = max(merged_bbox[2], box[2][0])
                merged_bbox[3] = max(merged_bbox[3], box[2][1])
            whole_line_bbox.append(merged_bbox)
        return whole_line_bbox

    @staticmethod
    def generate_id(input_str: str) -> str:
        """Generate a unique ID using SHA-256 hash."""
        return hashlib.sha256(input_str.encode()).hexdigest()

    # JSON and Image Saving

    @staticmethod
    def save_to_json(document: Document, output_folder: str) -> None:
        """Save the text and coordinates to a JSON file."""
        ext_file = "." + document.pdf_path.split("/")[-1].split(".")[-1]
        file_name = document.pdf_path.split("/")[-1].replace(ext_file, ".json")
        file_path = Path(output_folder) / file_name

        with Path(file_path).open("w", encoding="utf-8") as json_file:
            json.dump(document.model_dump(), json_file, ensure_ascii=False, indent=4)

    @staticmethod
    def draw_bounding_boxes(document: Document, output_folder: str) -> None:
        """Draw bounding boxes around the text in the PDF file."""
        image = cv2.imread(document.pdf_path)

        # Flatten all bounding boxes and draw them
        bounding_boxes = [
            word.bbox
            for page in document.pages
            for line in page.lines
            for word in line.words
        ]

        for bbox in bounding_boxes:
            cv2.rectangle(
                image,
                (int(bbox[0]), int(bbox[1])),
                (int(bbox[2]), int(bbox[3])),
                (0, 255, 0),
                1,
            )
        output_path = Path(output_folder) / Path(document.pdf_path).name
        cv2.imwrite(output_path, image)

    @staticmethod
    def parse_json_file_to_document(file_path: str) -> Document:
        """Parse the JSON file to a Document object."""
        with Path(file_path).open(encoding="utf-8") as json_file:
            data = json.load(json_file)
        return Document.parse_obj(data)


def main() -> None:
    output_folder = (
        "/home/jean/1404-resume/resume-ranking/version_1/"
        "c_Resume-ranking-demo/packages/ocr_processor/examples/img_output"
    )
    img_path = (
        "/home/jean/1404-resume/resume-ranking/version_1/"
        "c_Resume-ranking-demo/packages/ocr_processor/examples/"
        "img_input/Image_34.png"
    )
    processor = OCRProcessor()
    doc = processor.extract_text_and_coordinates((img_path), mode="tesseract")
    processor.draw_bounding_boxes(doc, output_folder)
    processor.save_to_json(doc, output_folder)

    input_folder = "/home/jean/PROJECT/ocr_jean/ocr_processor/examples/img_input"
    for img_path in pathlib.Path.iterdir():
        doc = processor.extract_text_and_coordinates(
            Path(input_folder) / img_path, mode="tesseract"
        )
        processor.draw_bounding_boxes(doc, output_folder)


if __name__ == "__main__":
    main()
