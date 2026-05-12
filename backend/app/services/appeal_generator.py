from datetime import datetime, timezone

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.tables import Appeal
from app.models.appeals import AppealCreate, AppealResponse, Citation, RAGSourceItem, WebEvidenceItem
from app.services.llm import generate_text, is_api_key_configured
from app.services.prompts import APPEAL_LETTER_SYSTEM, build_appeal_prompt
from app.services.retrieval import retrieve_guideline_context
from app.services.web_evidence import search_web_evidence

logger = structlog.get_logger()


async def generate_appeal(req: AppealCreate, db: AsyncSession) -> AppealResponse:
    if not is_api_key_configured():
        raise RuntimeError("No API keys configured. Add ANTHROPIC_API_KEY to .env")

    # Step 1: Create appeal record
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

    try:
        # Step 2: RAG retrieval — prefer exact code matches over loose keyword matches.
        rag_results = retrieve_guideline_context(
            denied_service=req.denied_service,
            denial_reason=req.denial_reason,
            cpt_codes=req.cpt_codes,
            icd10_codes=req.icd10_codes,
        )

        rag_context = "\n\n---\n\n".join(
            f"[Reference {i + 1}] {r.title}\nSource: {r.source}\nRelevance Score: {r.score * 100:.1f}%\n\n{r.text}"
            for i, r in enumerate(rag_results)
        )

        # Step 2b: Web evidence (non-blocking)
        web_evidence_context = ""
        web_evidence_results: list[dict] = []
        try:
            web_evidence = await search_web_evidence(
                req.denied_service, req.denial_reason, req.cpt_codes, req.icd10_codes
            )
            web_evidence_context = web_evidence["formattedContext"]
            web_evidence_results = web_evidence["evidence"]
            if web_evidence_results:
                logger.info("pubmed_articles_found", count=len(web_evidence_results))
        except Exception as e:
            logger.warning("web_evidence_search_failed", error=str(e))

        # Step 3: Generate appeal letter
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
        )

        generated_letter = await generate_text(APPEAL_LETTER_SYSTEM, prompt, 0.15)

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
        appeal.status = "completed"
        appeal.parsed_clinical_data = req.clinical_notes
        appeal.generated_letter = generated_letter
        appeal.citations = citations_data
        appeal.rag_sources = rag_sources_data
        appeal.updated_at = datetime.now(timezone.utc)
        await db.commit()

        return AppealResponse(
            appealId=appeal_id,
            letter=generated_letter,
            citations=[Citation(**c) for c in citations_data],
            ragSources=[RAGSourceItem(**r) for r in rag_sources_data],
            webEvidence=[WebEvidenceItem(**e) for e in web_evidence_results],
            parsedClinicalData=req.clinical_notes,
        )

    except Exception:
        appeal.status = "failed"
        appeal.updated_at = datetime.now(timezone.utc)
        await db.commit()
        raise
