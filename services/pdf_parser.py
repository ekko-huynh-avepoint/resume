from __future__ import annotations

import io
import logging
import os
import json
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
import fitz
import onnx
import yaml
import re
import numpy as np
import onnxruntime as ort
from PIL import Image, ImageDraw
from transformers import AutoTokenizer

from src.services.ocr_processor import OCRProcessor
from src.services.pdf2text import PDFProcessor
from src.utils.processing import normalize_bbox, truncate_padding
from src.models.pdf2tags_entity import Document, TokenizedObject


class PdfParser:
    def __init__(
            self,
            model_path: str,
            tokenizer_path: str,
            classes_path: str,
            max_workers_infer: int = 6,
    ) -> None:
        self._check_health_onnx(model_path)
        self.max_workers_infer = max_workers_infer
        self.session = ort.InferenceSession(model_path)
        self.pdf_processor = PDFProcessor()
        self.ocr_processor = OCRProcessor()
        self.tokenizer = AutoTokenizer.from_pretrained(tokenizer_path)
        if classes_path is None:
            labels = [
                "B-Address", "B-Certificate", "B-Education", "B-Email", "B-Experience",
                "B-GPA", "B-Hardskill", "B-Honor", "B-Language", "B-Link", "B-Name",
                "B-Phone", "B-Project", "B-Publication", "B-Softskill", "O",
            ]
        else:
            labels = self._get_label(classes_path)
        self.id2label = {id: label for id, label in enumerate(labels)}

        def normalize_color(rgb):
            return tuple(c / 255 for c in rgb)

        self.label_colors = {
            "B-Hardskill": normalize_color((128, 0, 128)),
            "B-Softskill": normalize_color((255, 165, 0)),
            "B-Education": normalize_color((0, 255, 0)),
            "B-Experience": normalize_color((0, 0, 255)),
            "B-Language": normalize_color((139, 69, 19)),
            "B-Project": normalize_color((255, 255, 0)),
            "B-Email": normalize_color((255, 0, 255)),
            "B-Phone": normalize_color((255, 0, 0)),
            "B-Address": normalize_color((0, 255, 255)),
            "B-Name": normalize_color((255, 20, 147)),
        }

    def _get_label(self, classes_path: str):
        with open(classes_path) as file:
            data = yaml.safe_load(file)
        return [f"B-{name}" for name in data["names"].values()] + ["O"]

    def _check_health_onnx(self, model_path: str) -> None:
        onnx_model = onnx.load(model_path)
        onnx.checker.check_model(onnx_model)

    def preprocess_input(self, pdf_path: str, max_length: int) -> tuple:
        doc = (self.pdf_processor.extract_text_and_coordinates(pdf_path)
               if pdf_path.endswith(".pdf")
               else self.ocr_processor.extract_text_and_coordinates(pdf_path))
        max_height, max_width = 1, 1
        doc_dict = doc.dict()
        encoding_list, list_inputs = [], []
        for page in doc_dict["pages"]:
            original_words, original_bboxes = [], []
            for line in page["lines"]:
                for word in line["words"]:
                    original_words.append(word["text"])
                    original_bboxes.append(word["bbox"])
                    max_width = max(max_width, word["bbox"][2])
                    max_height = max(max_height, word["bbox"][3])
                    word["ner_tag"] = ""
                line["ner_tag"] = ""
            original_word_masks = [0] * len(original_words)
            cls_box = sep_box = [0, 0, 0, 0]
            tokenized_bboxes, tokenized_word_masks = [], []
            for word, box, mask in zip(original_words, original_bboxes, original_word_masks, strict=False):
                box = normalize_bbox(box, max_width, max_height)
                n_word_tokens = len(self.tokenizer.tokenize(word))
                tokenized_bboxes.extend([box] * n_word_tokens)
                tokenized_word_masks.extend([mask] + ([-100] * (n_word_tokens - 1)))
            tokenized_bboxes = [cls_box] + tokenized_bboxes + [sep_box]
            tokenized_word_masks = [-100] + tokenized_word_masks + [-100]
            list_inputs.append((original_words, tokenized_bboxes, tokenized_word_masks))
        for _words, _tokenized_bboxes, _tokenized_word_masks in list_inputs:
            inputs = self.tokenizer(
                " ".join(_words),
                padding="max_length",
                truncation=True,
                max_length=max_length,
                return_tensors="np",
            )
            _tokenized_bboxes = truncate_padding(_tokenized_bboxes, max_length, [0, 0, 0, 0])
            _tokenized_word_masks = truncate_padding(_tokenized_word_masks, max_length, -100)
            encoding = TokenizedObject(
                input_ids=inputs["input_ids"],
                bbox=np.array([_tokenized_bboxes]),
                attention_mask=inputs["attention_mask"],
            )
            encoding_list.append(encoding)
        return (
            encoding_list,
            [tokenized_word_masks for _, _, tokenized_word_masks in list_inputs],
            Document(**doc_dict),
        )

    def inference_model(self, encoding_list: list[TokenizedObject]) -> list[np.ndarray]:
        def run_inference(enc: TokenizedObject) -> np.ndarray:
            inputs = enc.dict()
            outputs = self.session.run(None, inputs)
            return np.argmax(outputs[0], axis=-1)

        with ThreadPoolExecutor(max_workers=self.max_workers_infer) as executor:
            return list(executor.map(run_inference, encoding_list))

    def get_labels(self, list_predictions: list[np.ndarray], list_masks: list[list]) -> list[list]:
        list_true_predictions = []
        for predictions, masks in zip(list_predictions, list_masks, strict=False):
            masks = [masks]
            list_true_predictions.append([
                                             [self.id2label[p] for (p, l) in zip(pred, gold_label, strict=False) if
                                              l != -100]
                                             for pred, gold_label in zip(predictions, masks, strict=False)
                                         ][0])
        return list_true_predictions

    def _fill_tags(self, doc: Document, list_ner_tags: list[list[str]], number_of_email_phone: int = 15) -> Document:
        found_phones, found_emails = set(), set()
        for idx, page in enumerate(doc.pages):
            ner_tags = list_ner_tags[idx]
            if idx == 0:
                for line in page.lines[:number_of_email_phone]:
                    try:
                        found_phones.update(self.extract_phone_number(line.text))
                        found_emails.update(self.extract_email(line.text))
                    except Exception as e:
                        logging.warning(f"Error extracting phone/email: {e}")
            for line in page.lines:
                line_tags = []
                for word in line.words:
                    word.ner_tag = ner_tags.pop(0) if ner_tags else "O"
                    if word.ner_tag != "O":
                        line_tags.append(word.ner_tag)
                    if word.text in found_phones:
                        word.ner_tag = "B-Phone"
                        line_tags.append("B-Phone")
                    if word.text in found_emails:
                        word.ner_tag = "B-Email"
                        line_tags.append("B-Email")
                if line_tags:
                    counts = np.unique(np.array(line_tags), return_counts=True)
                    line.ner_tag = counts[0][np.argmax(counts[1])]
                else:
                    line.ner_tag = "O"
        return doc

    def parse(self, pdf_path: str, max_length: int = 512) -> Document:
        try:
            list_encoding, list_tokenized_word_masks, doc = self.preprocess_input(pdf_path, max_length)
            list_predictions = self.inference_model(list_encoding)
            list_true_preds = self.get_labels(list_predictions, list_tokenized_word_masks)
            doc = self._fill_tags(doc, list_true_preds)
            return doc
        except Exception as e:
            logging.error(f"Error parsing {pdf_path}: {e}")
            raise

    def visualize_on_pdf(self, document: Document, pdf_path: str) -> bytes:
        pdf_document = fitz.open(pdf_path)
        extracted_page_number = 0
        for page_number, page in enumerate(pdf_document):
            text = page.get_text()
            if not text.strip():
                continue
            for line in document.pages[extracted_page_number].lines:
                for word in line.words:
                    x1, y1, x2, y2 = map(int, word.bbox)
                    color = self.label_colors.get(word.ner_tag)
                    if color:
                        page.draw_rect([x1, y1, x2, y2], color=color, width=1)
            extracted_page_number += 1
        pdf_bytes = io.BytesIO()
        pdf_document.save(pdf_bytes)
        pdf_document.close()
        return pdf_bytes.getvalue()

    def visualize_on_image(self, document: Document, image_path: str) -> bytes:
        image = Image.open(image_path).convert("RGB")
        draw = ImageDraw.Draw(image)
        for line in document.pages[0].lines:
            for word in line.words:
                color = self.label_colors.get(word.ner_tag)
                if not color:
                    continue
                x1, y1, x2, y2 = map(int, word.bbox)
                color = tuple(int(c * 255) for c in color)
                draw.rectangle([x1, y1, x2, y2], outline=color, width=2)
        img_bytes = io.BytesIO()
        ext_file = Path(image_path).suffix.lower().replace(".", "").upper()
        image_format = ext_file if ext_file in {"PNG", "JPEG", "JPG"} else "JPEG"
        image.save(img_bytes, format=image_format)
        return img_bytes.getvalue()

    def extract_phone_number(self, text: str) -> set[str]:
        phone_pattern = r'\+?\d{1,4}[- ]?\(?\d{2,4}\)?[- ]?\d{2,4}[- ]?\d{2,4}|\d{2,4}[-]?\d{2,4}[-]?\d{2,4}'
        return set(re.findall(phone_pattern, text))

    def extract_email(self, text: str) -> set[str]:
        email_pattern = r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}'
        return set(re.findall(email_pattern, text))

    def dump_to_json(self, document: Document, output_path: str = "output.json") -> None:
        with open(output_path, "w") as f:
            json.dump(document.dict(), f, indent=4)
