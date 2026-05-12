import json
import re

import structlog
from fastapi import APIRouter
from fastapi.responses import JSONResponse

from app.models.verification import VerifyRequest
from app.services.llm import generate_text, is_api_key_configured
from app.services.prompts import VERIFICATION_SYSTEM, build_verification_prompt

logger = structlog.get_logger()
router = APIRouter()


@router.post("/api/verify-appeal")
async def verify_appeal(body: VerifyRequest):
    try:
        if not is_api_key_configured():
            return JSONResponse({"error": "No API keys configured"}, status_code=500)

        prompt = build_verification_prompt(
            letter=body.letter,
            clinical_notes=body.clinical_notes,
            rag_context=body.rag_context,
            denial_reason=body.denial_reason,
        )

        result = await generate_text(VERIFICATION_SYSTEM, prompt, 0.1)

        # Extract JSON from response
        json_match = re.search(r"\{[\s\S]*\}", result)
        if json_match:
            verification = json.loads(json_match.group())
            return {"verification": verification}

        logger.warning("verification_json_parse_failed")
        return JSONResponse(
            {"error": "Failed to parse verification result"},
            status_code=500,
        )

    except Exception as e:
        logger.error("verification_error", error=str(e))
        return JSONResponse({"error": str(e)}, status_code=500)
