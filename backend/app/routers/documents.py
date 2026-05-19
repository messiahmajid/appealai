from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse

from app.services.document_parser import DocumentParseError, extract_document_text

router = APIRouter()


@router.post("/api/clinical-notes/extract")
async def extract_clinical_notes(request: Request):
    data = await request.body()
    filename = request.headers.get("x-file-name", "")
    content_type = request.headers.get("content-type", "")

    if not data:
        return JSONResponse({"error": "No file data received."}, status_code=400)

    try:
        text = extract_document_text(data, filename, content_type)
    except DocumentParseError as exc:
        return JSONResponse({"error": str(exc)}, status_code=400)

    return {
        "text": text,
        "fileName": filename,
        "characterCount": len(text),
    }
