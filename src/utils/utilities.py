import pdfplumber
from docx import Document
import io



def extract_pdf(page):
    with pdfplumber.open(page) as pdf:
        pages = pdf.pages
        text = ''
        for page in pages:
            text += page.extract_text()
        return text


def extract_docx(page):
    doc = Document(io.BytesIO(page.read()))
    return "\n".join([para.text for para in doc.paragraphs])

