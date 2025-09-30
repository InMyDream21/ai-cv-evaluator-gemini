from typing import Tuple
from pypdf import PdfReader
from docx import Document
from io import BytesIO

def extract_text(filename: str, filedata: bytes) -> str:
    if filename.lower().endswith('.pdf'):
        reader = PdfReader(BytesIO(filedata))
        text = "\n".join(page.extract_text() or "" for page in reader.pages)
        return text
    elif filename.lower().endswith('.docx'):
        doc = Document(BytesIO(filedata))
        text = "\n".join(paragraph.text for paragraph in doc.paragraphs)
        return text
    else:
        return filedata.decode('utf-8', errors='ignore')
    
def normalize_pair(cv_file: Tuple[str, bytes], project_file: Tuple[str, bytes]) -> Tuple[str, str]:
    cv_filename, cv_data = cv_file
    project_filename, project_data = project_file
    cv_text = extract_text(cv_filename, cv_data)
    project_text = extract_text(project_filename, project_data)
    return cv_text.strip(), project_text.strip()

def extract_job_desc_from_pdf(path: str, pages: int = 2) -> str:
    reader = PdfReader(path)
    text = "\n".join(page.extract_text() or "" for page in reader.pages[:pages])
    return text.strip()