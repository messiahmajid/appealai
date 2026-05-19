import json
import re

import structlog
from fastapi import APIRouter
from fastapi.responses import JSONResponse

from app.models.verification import VerifyRequest
from app.services.llm import generate_text, is_api_key_configured
from app.services.medical_safety import (
    run_medical_safety_checks,
    safety_report_to_verification_checks,
    split_guideline_sources,
    split_pubmed_sources,
)
from app.services.prompts import VERIFICATION_SYSTEM, build_verification_prompt
from app.services.retrieval import retrieve_guideline_context

logger = structlog.get_logger()
router = APIRouter()


@router.post("/api/verify-appeal")
async def verify_appeal(body: VerifyRequest):
    try:
        rag_context = body.rag_context
        if body.denied_service or body.cpt_codes or body.icd10_codes:
            rag_results = retrieve_guideline_context(
                denied_service=body.denied_service,
                denial_reason=body.denial_reason,
                cpt_codes=body.cpt_codes,
                icd10_codes=body.icd10_codes,
            )
            if rag_results:
                rag_context = "\n\n---\n\n".join(
                    f"[Reference {i + 1}] {r.title}\nSource: {r.source}\n\n{r.text}"
                    for i, r in enumerate(rag_results)
                )

        deterministic_report = run_medical_safety_checks(
            letter=body.letter,
            clinical_notes=body.clinical_notes,
            denial_reason=body.denial_reason,
            guideline_sources=split_guideline_sources(rag_context),
            pubmed_sources=split_pubmed_sources(rag_context),
        )

        if not is_api_key_configured():
            return {
                "verification": {
                    "overallVerdict": deterministic_report["verdict"],
                    "confidenceScore": 0.8 if deterministic_report["verdict"] == "PASS" else 0.6,
                    "checks": safety_report_to_verification_checks(deterministic_report),
                    "flaggedIssues": [
                        f"{issue['code']}: {issue['message']}"
                        for issue in deterministic_report["issues"]
                    ],
                    "summary": (
                        "Deterministic verification completed. LLM verification was skipped because "
                        "the API key is not configured."
                    ),
                    "deterministicReport": deterministic_report,
                }
            }

        prompt = build_verification_prompt(
            letter=body.letter,
            clinical_notes=body.clinical_notes,
            rag_context=rag_context,
            denial_reason=body.denial_reason,
        )

        result = await generate_text(VERIFICATION_SYSTEM, prompt, 0.1)

        # Extract JSON from response
        json_match = re.search(r"\{[\s\S]*\}", result)
        if json_match:
            verification = json.loads(json_match.group())
            deterministic_checks = safety_report_to_verification_checks(deterministic_report)
            if deterministic_report["verdict"] == "FAIL":
                merged_verdict = "FAIL"
            elif (
                deterministic_report["verdict"] == "NEEDS_REVIEW"
                and verification.get("overallVerdict") == "PASS"
            ):
                merged_verdict = "NEEDS_REVIEW"
            else:
                merged_verdict = verification.get("overallVerdict", deterministic_report["verdict"])

            verification["overallVerdict"] = merged_verdict
            verification["checks"] = [*verification.get("checks", []), *deterministic_checks]
            verification["flaggedIssues"] = [
                *verification.get("flaggedIssues", []),
                *[
                    f"{issue['code']}: {issue['message']}"
                    for issue in deterministic_report["issues"]
                ],
            ]
            verification["deterministicReport"] = deterministic_report
            return {"verification": verification}

        logger.warning("verification_json_parse_failed")
        return JSONResponse(
            {"error": "Failed to parse verification result"},
            status_code=500,
        )

    except Exception as e:
        logger.error("verification_error", error=str(e))
        return JSONResponse({"error": str(e)}, status_code=500)
