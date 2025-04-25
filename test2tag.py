from __future__ import annotations

from src.services.pdf_parser import PdfParser

tokenizer_path = "Element/lilt-tokenizer"
model_path = "Element/ner_700i_500e_4_512.onnx"
pdf_path = "data/CV_cake/https___www_cake_me_me_afauzanaqil_locale=en.pdf"
classes_path = "Element/classes.yaml"

# Input the necessary path to the Parser
parser = PdfParser(
    tokenizer_path=tokenizer_path,
    model_path=model_path,
    classes_path=classes_path
)

# Parse the PDF to Document object
doc = parser.parse(pdf_path=pdf_path, max_length=512)
# Save the result to json format
parser.dump_to_json(document=doc, output_path="output.json")
# Visualize the result
parser.visualize(document=doc, pdf_path=pdf_path, visualize_path="output")
