import json
from datetime import datetime, timezone
from typing import Awaitable, Callable

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.tables import Appeal
from app.models.appeals import AppealCreate, AppealResponse, Citation, RAGSourceItem, WebEvidenceItem
from app.services.llm import generate_text, is_api_key_configured
from app.services.medical_analysis import (
    assess_clinical_note_sufficiency,
    build_structured_medical_analysis,
    format_structured_analysis_for_prompt,
)
from app.services.medical_safety import (
    SafetySource,
    run_medical_safety_checks,
    sanitize_generated_letter,
    split_pubmed_sources,
)
from app.services.prompts import (
    APPEAL_LETTER_SYSTEM,
    APPEAL_REPAIR_SYSTEM,
    build_appeal_prompt,
    build_repair_prompt,
)
from app.services.retrieval import retrieve_guideline_context
from app.services.web_evidence import search_web_evidence

logger = structlog.get_logger()
ProgressCallback = Callable[[dict], Awaitable[None]]


class ClinicalNoteInsufficientError(RuntimeError):
    def __init__(self, report: dict):
        super().__init__(report["summary"])
        self.report = report


async def _emit_progress(
    progress: ProgressCallback | None,
    stage: str,
    message: str,
    data: dict | None = None,
) -> None:
    if progress:
        await progress({"stage": stage, "message": message, "data": data or {}})


async def generate_appeal(
    req: AppealCreate,
    db: AsyncSession,
    progress: ProgressCallback | None = None,
) -> AppealResponse:
    if not is_api_key_configured():
        raise RuntimeError("No API keys configured. Add GOOGLE_GENERATIVE_AI_API_KEY to .env (free)")

    # Step 1: RAG retrieval and deterministic sufficiency check before any LLM call.
    await _emit_progress(progress, "guidelines_started", "Retrieving medical necessity policies...")
    rag_results = retrieve_guideline_context(
        denied_service=req.denied_service,
        denial_reason=req.denial_reason,
        cpt_codes=req.cpt_codes,
        icd10_codes=req.icd10_codes,
    )
    await _emit_progress(
        progress,
        "guidelines_done",
        f"Found {len(rag_results)} relevant polic{'y' if len(rag_results) == 1 else 'ies'}.",
        {"count": len(rag_results)},
    )

    await _emit_progress(progress, "sufficiency_started", "Checking clinical-note sufficiency...")
    structured_analysis = build_structured_medical_analysis(
        clinical_notes=req.clinical_notes,
        rag_results=rag_results,
    )
    sufficiency_report = assess_clinical_note_sufficiency(
        clinical_notes=req.clinical_notes,
        denied_service=req.denied_service,
        denial_reason=req.denial_reason,
        structured_analysis=structured_analysis,
    )
    await _emit_progress(
        progress,
        "sufficiency_done",
        f"Clinical-note sufficiency score: {sufficiency_report['score']}/100.",
        sufficiency_report,
    )
    if sufficiency_report["status"] == "block":
        await _emit_progress(
            progress,
            "sufficiency_failed",
            sufficiency_report["summary"],
            {"sufficiencyReport": sufficiency_report},
        )
        raise ClinicalNoteInsufficientError(sufficiency_report)

    await _emit_progress(progress, "record_started", "Creating appeal record...")
    appeal = Appeal(
        patient_name=req.patient_name,
        patient_dob=req.patient_dob,
        member_id=req.member_id,
        insurance_company=req.insurance_company,
        claim_number=req.claim_number,
        denial_date=req.denial_date,
        denial_reason=req.denial_reason,
        denied_service=req.denied_service,
        cpt_codes=req.cpt_codes,
        icd10_codes=req.icd10_codes,
        physician_name=req.physician_name,
        physician_npi=req.physician_npi,
        practice_name=req.practice_name,
        clinical_notes=req.clinical_notes,
        status="generating",
    )
    db.add(appeal)
    await db.flush()
    appeal_id = str(appeal.id)
    await _emit_progress(progress, "record_done", "Appeal record created.", {"appealId": appeal_id})
    try:
        rag_context = "\n\n---\n\n".join(
            f"[Reference {i + 1}] {r.title}\nSource: {r.source}\nRelevance Score: {r.score * 100:.1f}%\n\n{r.text}"
            for i, r in enumerate(rag_results)
        )
        structured_analysis_context = format_structured_analysis_for_prompt(structured_analysis)

        # Step 2b: Web evidence (non-blocking)
        web_evidence_context = ""
        web_evidence_results: list[dict] = []
        await _emit_progress(progress, "pubmed_started", "Searching PubMed evidence...")
        try:
            web_evidence = await search_web_evidence(
                req.denied_service, req.denial_reason, req.cpt_codes, req.icd10_codes
            )
            web_evidence_context = web_evidence["formattedContext"]
            web_evidence_results = web_evidence["evidence"]
            if web_evidence_results:
                logger.info("pubmed_articles_found", count=len(web_evidence_results))
            await _emit_progress(
                progress,
                "pubmed_done",
                f"Found {len(web_evidence_results)} PubMed article{'s' if len(web_evidence_results) != 1 else ''}.",
                {"count": len(web_evidence_results)},
            )
        except Exception as e:
            logger.warning("web_evidence_search_failed", error=str(e))
            await _emit_progress(
                progress,
                "pubmed_done",
                "PubMed search was unavailable; continuing with guideline evidence.",
                {"count": 0, "warning": str(e)},
            )

        # Step 3: Generate appeal letter
        await _emit_progress(progress, "generation_started", "Generating appeal letter...")
        prompt = build_appeal_prompt(
            clinical_notes=req.clinical_notes,
            denial_reason=req.denial_reason,
            denied_service=req.denied_service,
            cpt_code=req.cpt_codes,
            icd10_codes=req.icd10_codes,
            insurance_company=req.insurance_company,
            patient_name=req.patient_name,
            patient_dob=req.patient_dob,
            member_id=req.member_id,
            claim_number=req.claim_number,
            denial_date=req.denial_date,
            physician_name=req.physician_name,
            physician_npi=req.physician_npi,
            practice_name=req.practice_name,
            rag_context=rag_context,
            web_evidence_context=web_evidence_context,
            structured_analysis_context=structured_analysis_context,
        )

        raw_letter = await generate_text(APPEAL_LETTER_SYSTEM, prompt, 0.15)
        generated_letter = sanitize_generated_letter(raw_letter)
        await _emit_progress(progress, "generation_done", "Draft generated.")

        await _emit_progress(progress, "safety_started", "Running medical safety checks...")
        safety_report = run_medical_safety_checks(
            letter=generated_letter,
            clinical_notes=req.clinical_notes,
            denial_reason=req.denial_reason,
            guideline_sources=[
                SafetySource(
                    label=f"Reference {i + 1}",
                    text=f"{r.title}\n{r.source}\n{r.text}",
                )
                for i, r in enumerate(rag_results)
            ],
            pubmed_sources=split_pubmed_sources(web_evidence_context),
        )
        await _emit_progress(
            progress,
            "safety_done",
            f"Safety checks returned {safety_report['verdict']}.",
            {"verdict": safety_report["verdict"], "issueCount": len(safety_report.get("issues", []))},
        )
        if safety_report["verdict"] == "FAIL":
            await _emit_progress(progress, "repair_started", "Repairing unsupported or unsafe draft content...")
            repaired_letter = await generate_text(
                APPEAL_REPAIR_SYSTEM,
                build_repair_prompt(
                    letter=generated_letter,
                    clinical_notes=req.clinical_notes,
                    rag_context=rag_context,
                    web_evidence_context=web_evidence_context,
                    safety_report=safety_report,
                ),
                0.05,
            )
            generated_letter = sanitize_generated_letter(repaired_letter)
            repaired_report = run_medical_safety_checks(
                letter=generated_letter,
                clinical_notes=req.clinical_notes,
                denial_reason=req.denial_reason,
                guideline_sources=[
                    SafetySource(
                        label=f"Reference {i + 1}",
                        text=f"{r.title}\n{r.source}\n{r.text}",
                    )
                    for i, r in enumerate(rag_results)
                ],
                pubmed_sources=split_pubmed_sources(web_evidence_context),
            )
            safety_report = {
                **repaired_report,
                "repairAttempted": True,
                "preRepairVerdict": "FAIL",
            }
            await _emit_progress(
                progress,
                "repair_done",
                f"Repair completed with final verdict {repaired_report['verdict']}.",
                {"verdict": repaired_report["verdict"]},
            )

        full_safety_report = {
            **safety_report,
            "structuredAnalysis": structured_analysis,
            "clinicalSufficiency": sufficiency_report,
        }

        # Step 4: Build citations
        citations_data = [
            {
                "index": i + 1,
                "guidelineId": r.guideline_id,
                "title": r.title,
                "source": r.source,
                "text": r.text[:300] + "...",
            }
            for i, r in enumerate(rag_results)
        ]

        rag_sources_data = [
            {
                "guidelineId": r.guideline_id,
                "title": r.title,
                "source": r.source,
                "relevanceScore": r.score,
            }
            for r in rag_results
        ]

        # Step 5: Update appeal
        await _emit_progress(progress, "save_started", "Saving appeal letter...")
        appeal.status = "failed" if full_safety_report["verdict"] == "FAIL" else "completed"
        appeal.parsed_clinical_data = req.clinical_notes
        appeal.generated_letter = generated_letter
        appeal.citations = citations_data
        appeal.rag_sources = rag_sources_data
        appeal.analysis_result = json.dumps({"safetyReport": full_safety_report})
        appeal.updated_at = datetime.now(timezone.utc)
        await db.commit()
        await _emit_progress(progress, "save_done", "Appeal saved.")

        return AppealResponse(
            appealId=appeal_id,
            letter=generated_letter,
            citations=[Citation(**c) for c in citations_data],
            ragSources=[RAGSourceItem(**r) for r in rag_sources_data],
            webEvidence=[WebEvidenceItem(**e) for e in web_evidence_results],
            parsedClinicalData=req.clinical_notes,
            safetyReport=full_safety_report,
            clinicalSufficiencyReport=sufficiency_report,
        )

    except Exception:
        appeal.status = "failed"
        appeal.updated_at = datetime.now(timezone.utc)
        await db.commit()
        raise
