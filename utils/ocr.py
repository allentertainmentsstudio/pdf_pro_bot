import pytesseract
from PIL import Image
from pdf2image import convert_from_path


def image_to_text(path):
    img = Image.open(path)
    return pytesseract.image_to_string(img)


def pdf_to_text(path):
    pages = convert_from_path(path)
    text = ""

    for p in pages:
        text += pytesseract.image_to_string(p) + "\n\n"

    return text
