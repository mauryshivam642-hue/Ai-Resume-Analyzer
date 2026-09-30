from pathlib import Path
from pdfminer.high_level import extract_text as pdf_extract_text
from docx import Document


def extract_from_pdf(filepath):
    return pdf_extract_text(filepath)


def extract_from_docx(filepath):
    document = Document(filepath)
    return "\n".join(
        paragraph.text
        for paragraph in document.paragraphs
        if paragraph.text.strip()
    )


def extract_text_from_file(filepath):
    extension = Path(filepath).suffix.lower()

    if extension == ".pdf":
        return extract_from_pdf(filepath)

    if extension == ".docx":
        return extract_from_docx(filepath)

    raise ValueError("Unsupported file type. Use PDF or DOCX.")
