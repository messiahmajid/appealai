from fastapi import APIRouter, Query

from app.models.codes import CodeSearchResponse, CodeResult
from app.services.medical_codes import search_cpt, search_icd10

router = APIRouter()


@router.get("/api/codes/cpt")
async def search_cpt_codes(q: str = Query(default="")) -> CodeSearchResponse:
    results = search_cpt(q)
    return CodeSearchResponse(
        results=[CodeResult(code=r.code, description=r.description, category=r.category) for r in results]
    )


@router.get("/api/codes/icd10")
async def search_icd10_codes(q: str = Query(default="")) -> CodeSearchResponse:
    results = search_icd10(q)
    return CodeSearchResponse(
        results=[CodeResult(code=r.code, description=r.description, category=r.category) for r in results]
    )
