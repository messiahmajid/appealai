from __future__ import annotations

import re
import zipfile
import zlib
from io import BytesIO
from xml.etree import ElementTree

MAX_UPLOAD_BYTES = 10 * 1024 * 1024
MAX_DECOMPRESSED_BYTES = 25 * 1024 * 1024
MAX_ZIP_ENTRIES = 200


class DocumentParseError(ValueError):
    pass


def _check_size(data: bytes) -> None:
    if len(data) > MAX_UPLOAD_BYTES:
        raise DocumentParseError("File is too large. Upload a file under 10 MB.")


def _normalize_text(text: str) -> str:
    text = text.replace("\x00", "")
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def extract_plain_text(data: bytes) -> str:
    _check_size(data)
    for encoding in ("utf-8-sig", "utf-8", "latin-1"):
        try:
            return _normalize_text(data.decode(encoding))
        except UnicodeDecodeError:
            continue
    raise DocumentParseError("Unable to decode text file.")


def extract_docx_text(data: bytes) -> str:
    _check_size(data)
    try:
        archive = zipfile.ZipFile(BytesIO(data))
    except zipfile.BadZipFile as exc:
        raise DocumentParseError("Invalid DOCX file.") from exc

    infos = archive.infolist()
    if len(infos) > MAX_ZIP_ENTRIES:
        raise DocumentParseError("DOCX contains too many internal files.")
    if sum(info.file_size for info in infos) > MAX_DECOMPRESSED_BYTES:
        raise DocumentParseError("DOCX expanded content is too large.")

    names = archive.namelist()
    xml_names = [
        "word/document.xml",
        *sorted(n for n in names if re.match(r"word/(?:header|footer)\d+\.xml$", n, re.I)),
    ]
    namespace = {"w": "http://schemas.openxmlformats.org/wordprocessingml/2006/main"}
    parts: list[str] = []

    for name in xml_names:
        if name not in names:
            continue
        try:
            root = ElementTree.fromstring(archive.read(name))
        except ElementTree.ParseError:
            continue

        for paragraph in root.findall(".//w:p", namespace):
            paragraph_text: list[str] = []
            for node in paragraph.iter():
                tag = node.tag.rsplit("}", 1)[-1]
                if tag == "t" and node.text:
                    paragraph_text.append(node.text)
                elif tag == "tab":
                    paragraph_text.append("\t")
                elif tag in {"br", "cr"}:
                    paragraph_text.append("\n")
            text = "".join(paragraph_text).strip()
            if text:
                parts.append(text)

    extracted = _normalize_text("\n".join(parts))
    if not extracted:
        raise DocumentParseError("No readable text found in DOCX file.")
    return extracted


def _decode_pdf_literal(value: str) -> str:
    value = value.replace(r"\(", "(").replace(r"\)", ")").replace(r"\\", "\\")
    value = re.sub(r"\\n|\\r", "\n", value)
    value = re.sub(r"\\t", "\t", value)
    value = re.sub(r"\\([0-7]{1,3})", lambda m: chr(int(m.group(1), 8)), value)
    return value


def _extract_pdf_text_from_stream(stream: bytes) -> str:
    text = stream.decode("latin-1", errors="ignore")
    chunks: list[str] = []
    for match in re.finditer(r"\((?:\\.|[^\\)])*\)\s*Tj", text):
        raw = match.group(0)
        chunks.append(_decode_pdf_literal(raw[1: raw.rfind(")")]))
    for match in re.finditer(r"\[([\s\S]*?)\]\s*TJ", text):
        chunks.extend(_decode_pdf_literal(item[1:-1]) for item in re.findall(r"\((?:\\.|[^\\)])*\)", match.group(1)))
    return " ".join(chunks)


def extract_pdf_text(data: bytes) -> str:
    _check_size(data)
    chunks: list[str] = []
    decompressed_total = 0
    for match in re.finditer(rb"stream\r?\n(.*?)\r?\nendstream", data, re.S):
        stream = match.group(1)
        candidates = [stream]
        try:
            decompressed = zlib.decompress(stream)
            decompressed_total += len(decompressed)
            if decompressed_total > MAX_DECOMPRESSED_BYTES:
                raise DocumentParseError("PDF expanded content is too large.")
            candidates.append(decompressed)
        except zlib.error:
            pass
        for candidate in candidates:
            extracted = _extract_pdf_text_from_stream(candidate)
            if extracted:
                chunks.append(extracted)

    extracted = _normalize_text("\n".join(chunks))
    if not extracted:
        raise DocumentParseError("No readable text found in PDF. Scanned PDFs require OCR before upload.")
    return extracted


def extract_document_text(data: bytes, filename: str, content_type: str = "") -> str:
    lower_name = filename.lower()
    lower_type = content_type.lower()

    if lower_name.endswith((".txt", ".md", ".csv")) or lower_type.startswith("text/"):
        return extract_plain_text(data)
    if lower_name.endswith(".docx") or "officedocument.wordprocessingml.document" in lower_type:
        return extract_docx_text(data)
    if lower_name.endswith(".pdf") or lower_type == "application/pdf":
        return extract_pdf_text(data)

    raise DocumentParseError("Unsupported file type. Upload TXT, MD, CSV, DOCX, or text-based PDF.")
