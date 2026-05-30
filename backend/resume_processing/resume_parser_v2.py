from io import BytesIO
from pathlib import Path
from xml.etree import ElementTree as ET
from zipfile import BadZipFile, ZipFile

import pdfplumber


def clean_text(text: str) -> str:
    return " ".join(text.lower().split())


def _parse_txt(content: bytes) -> str:
    for encoding in ("utf-8", "utf-16", "latin-1"):
        try:
            return content.decode(encoding)
        except UnicodeDecodeError:
            continue
    raise ValueError("Unable to decode text file.")


def _parse_pdf(content: bytes) -> str:
    extracted_pages = []

    with pdfplumber.open(BytesIO(content)) as pdf:
        for page in pdf.pages:
            extracted_pages.append(page.extract_text() or "")

    return "\n".join(extracted_pages)


def _parse_docx(content: bytes) -> str:
    try:
        with ZipFile(BytesIO(content)) as docx_zip:
            xml_content = docx_zip.read("word/document.xml")
    except (KeyError, BadZipFile) as exc:
        raise ValueError("Invalid DOCX file.") from exc

    root = ET.fromstring(xml_content)
    namespace = {"w": "http://schemas.openxmlformats.org/wordprocessingml/2006/main"}
    paragraphs = []

    for paragraph in root.findall(".//w:p", namespace):
        texts = [node.text for node in paragraph.findall(".//w:t", namespace) if node.text]
        if texts:
            paragraphs.append("".join(texts))

    return "\n".join(paragraphs)


async def parse_resume(file) -> str:
    filename = file.filename or ""
    extension = Path(filename).suffix.lower()
    content = await file.read()

    if not content:
        raise ValueError(f"{filename or 'File'} is empty.")

    if extension == ".pdf":
        text = _parse_pdf(content)
    elif extension == ".docx":
        text = _parse_docx(content)
    elif extension in {".txt", ".md"}:
        text = _parse_txt(content)
    else:
        raise ValueError(
            f"Unsupported file format for {filename or 'file'}. "
            "Use PDF, DOCX, or TXT."
        )

    cleaned = clean_text(text)
    if not cleaned:
        raise ValueError(f"No readable text found in {filename or 'file'}.")

    return cleaned
