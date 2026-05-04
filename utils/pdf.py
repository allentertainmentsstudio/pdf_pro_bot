import os
import img2pdf
from PyPDF2 import PdfMerger


def images_to_pdf(folder, output):
    images = sorted([
        os.path.join(folder, f)
        for f in os.listdir(folder)
        if f.lower().endswith((".jpg", ".jpeg", ".png"))
    ])

    if not images:
        return None

    with open(output, "wb") as f:
        f.write(img2pdf.convert(images))

    return output
