import pytest

from app.services.medical_codes import search_cpt, search_icd10
from app.services.rag import cosine_similarity, search_rag_fallback


def test_search_cpt_finds_tka():
    results = search_cpt("27447")
    assert len(results) > 0
    assert results[0].code == "27447"


def test_search_cpt_by_description():
    results = search_cpt("knee arthroplasty")
    assert len(results) > 0


def test_search_icd10_finds_knee_oa():
    results = search_icd10("M17.11")
    assert len(results) > 0
    assert results[0].code == "M17.11"


def test_search_icd10_by_category():
    results = search_icd10("Cardiovascular")
    assert len(results) > 0
    assert all(r.category == "Cardiovascular" for r in results)


def test_cosine_similarity_identical():
    a = [1.0, 0.0, 0.0]
    b = [1.0, 0.0, 0.0]
    assert cosine_similarity(a, b) == pytest.approx(1.0)


def test_cosine_similarity_orthogonal():
    a = [1.0, 0.0]
    b = [0.0, 1.0]
    assert cosine_similarity(a, b) == pytest.approx(0.0)


def test_search_rag_fallback_finds_tka():
    results = search_rag_fallback("total knee arthroplasty osteoarthritis")
    assert len(results) > 0
    assert any("knee" in r.title.lower() or "tka" in r.title.lower() for r in results)


def test_search_rag_fallback_finds_pet():
    results = search_rag_fallback("PET CT lung cancer NSCLC staging")
    assert len(results) > 0


def test_search_rag_fallback_deduplicates():
    results = search_rag_fallback("osteoarthritis knee joint replacement surgery")
    guideline_ids = [r.guideline_id for r in results]
    assert len(guideline_ids) == len(set(guideline_ids))


def test_guidelines_search():
    from app.services.guidelines import search_guidelines
    results = search_guidelines("knee arthroplasty")
    assert len(results) > 0


def test_guidelines_by_code():
    from app.services.guidelines import get_guidelines_by_code
    results = get_guidelines_by_code("27447")
    assert len(results) > 0
    assert any("knee" in g.title.lower() for g in results)


def test_guideline_chunks():
    from app.services.guidelines import get_guideline_chunks
    chunks = get_guideline_chunks()
    assert len(chunks) > 10
    assert all(hasattr(c, "id") and hasattr(c, "text") and hasattr(c, "guideline_id") for c in chunks)


def test_retrieval_prefers_cardiac_code_match_without_padding_irrelevant_sources():
    from app.services.retrieval import retrieve_guideline_context

    results = retrieve_guideline_context(
        denied_service="Left Heart Catheterization with Coronary Angiography",
        denial_reason="Stress testing results do not meet criteria.",
        cpt_codes="93458",
        icd10_codes="I20.9, I25.10",
    )
    guideline_ids = [r.guideline_id for r in results]

    assert "cms-ncd-20.7" in guideline_ids
    assert "cms-ncd-220.6" not in guideline_ids
    assert "lcd-l35014" not in guideline_ids


def test_retrieval_splits_multiple_codes_before_matching():
    from app.services.retrieval import retrieve_guideline_context

    results = retrieve_guideline_context(
        denied_service="PET/CT for NSCLC staging",
        denial_reason="PET/CT considered investigational.",
        cpt_codes="78816, 71260",
        icd10_codes="C34.11, R91.1",
    )
    guideline_ids = {r.guideline_id for r in results}

    assert "cms-ncd-220.6" in guideline_ids
    assert "nccn-nsclc-2024" in guideline_ids


@pytest.mark.parametrize(
    ("denied_service", "cpt_codes", "icd10_codes", "expected_guideline"),
    [
        ("Mounjaro for type 2 diabetes", "", "E11.65", "ada-glp1-t2dm-2026"),
        ("Home oxygen concentrator", "E1390", "J96.11", "cms-ncd-240.2-home-oxygen"),
        ("Lumbar transforaminal epidural steroid injection", "64483", "M54.16", "lcd-l39054-esi"),
        ("Keytruda immunotherapy", "J9271", "C34.90", "cms-l33394-oncology-drugs"),
        ("Total hip arthroplasty", "27130", "M16.11", "lcd-l34163-tha"),
        ("Power wheelchair", "K0823", "R26.2", "cms-l33789-power-mobility"),
    ],
)
def test_retrieval_finds_expanded_guideline_corpus(
    denied_service,
    cpt_codes,
    icd10_codes,
    expected_guideline,
):
    from app.services.retrieval import retrieve_guideline_context

    results = retrieve_guideline_context(
        denied_service=denied_service,
        denial_reason="Medical necessity criteria not met.",
        cpt_codes=cpt_codes,
        icd10_codes=icd10_codes,
        max_results=5,
    )
    guideline_ids = {r.guideline_id for r in results}

    assert expected_guideline in guideline_ids


def test_eval_suite_contains_more_than_fifty_scenarios():
    from eval.scenarios import EVALUATION_CASES

    assert len(EVALUATION_CASES) >= 50
    assert all(case.get("expectedGuidelineIds") for case in EVALUATION_CASES)


@pytest.mark.asyncio
async def test_gemini_generation_falls_back_to_next_model_on_rate_limit(monkeypatch):
    from app.services import llm

    calls: list[str] = []

    class FakeResponse:
        text = "Generated with fallback model."

    class FakeModels:
        async def generate_content(self, *, model, contents, config):
            calls.append(model)
            if model == "model-a":
                raise Exception('429 RESOURCE_EXHAUSTED {"retryDelay":"60s"}')
            return FakeResponse()

    class FakeAio:
        models = FakeModels()

    class FakeClient:
        aio = FakeAio()

    monkeypatch.setattr(llm.settings, "google_generative_ai_api_key", "test-key")
    monkeypatch.setattr(llm.settings, "gemini_text_models", "model-a,model-b")
    monkeypatch.setattr(llm.settings, "anthropic_api_key", "")
    monkeypatch.setattr(llm.settings, "openrouter_api_key", "")
    monkeypatch.setattr(llm, "_get_gemini_client", lambda: FakeClient())

    result = await llm._generate_text_uncached("system", "user", 0.1)

    assert result == "Generated with fallback model."
    assert calls == ["model-a", "model-b"]


@pytest.mark.asyncio
async def test_gemini_generation_reports_project_rate_limit_after_all_models(monkeypatch):
    from app.services import llm

    class FakeModels:
        async def generate_content(self, *, model, contents, config):
            raise Exception("429 RESOURCE_EXHAUSTED quota exceeded")

    class FakeAio:
        models = FakeModels()

    class FakeClient:
        aio = FakeAio()

    monkeypatch.setattr(llm.settings, "google_generative_ai_api_key", "test-key")
    monkeypatch.setattr(llm.settings, "gemini_text_models", "model-a,model-b")
    monkeypatch.setattr(llm.settings, "anthropic_api_key", "")
    monkeypatch.setattr(llm.settings, "openrouter_api_key", "")
    monkeypatch.setattr(llm, "_get_gemini_client", lambda: FakeClient())

    with pytest.raises(RuntimeError, match="per-minute, per-token-minute, or daily quota"):
        await llm._generate_text_uncached("system", "user", 0.1)


def test_medical_safety_passes_grounded_letter():
    from app.services.medical_safety import SafetySource, run_medical_safety_checks

    letter = (
        'The note documents "Pain score 8/10" and failed physical therapy for 6 weeks. '
        "This satisfies the guideline criterion for failed conservative therapy [1]."
    )
    report = run_medical_safety_checks(
        letter=letter,
        clinical_notes="Pain score 8/10. The patient completed physical therapy for 6 weeks.",
        denial_reason="Conservative therapy not documented.",
        guideline_sources=[
            SafetySource(
                label="Reference 1",
                text="Failed conservative therapy including physical therapy for 6 weeks.",
            )
        ],
    )

    assert report["verdict"] == "PASS"
    assert report["checks"]["guidelineCitationsValid"] is True
    assert report["checks"]["quotedClaimsGrounded"] is True
    assert report["checks"]["numericClaimsGrounded"] is True


def test_medical_safety_allows_punctuation_and_unit_variants_for_quotes():
    from app.services.medical_safety import SafetySource, run_medical_safety_checks

    letter = (
        'The chart documents "No current glucose-lowering medication tolerated." '
        'It also documents "Class II obesity, BMI 37.2 kg/m²" [1].'
    )
    clinical_notes = (
        "Current Medications: No current glucose-lowering medication tolerated as of today; "
        "patient checks fingerstick glucose twice daily. "
        "Active Diagnoses: E66.01 Class II obesity due to excess calories, BMI 37.2 kg/m2."
    )
    report = run_medical_safety_checks(
        letter=letter,
        clinical_notes=clinical_notes,
        guideline_sources=[SafetySource(label="Reference 1", text="BMI and comorbidity documentation may support selection.")],
    )

    assert report["checks"]["quotedClaimsGrounded"] is True
    assert not any(issue["code"] == "UNGROUNDED_QUOTE" for issue in report["issues"])


def test_medical_safety_still_warns_on_unsupported_quote():
    from app.services.medical_safety import SafetySource, run_medical_safety_checks

    report = run_medical_safety_checks(
        letter='The chart documents "A1c 11.9% despite insulin therapy" [1].',
        clinical_notes="A1c 8.7% despite metformin intolerance.",
        guideline_sources=[SafetySource(label="Reference 1", text="A1c above goal may support therapy intensification.")],
    )

    assert report["checks"]["quotedClaimsGrounded"] is False
    assert any(issue["code"] == "UNGROUNDED_QUOTE" for issue in report["issues"])


def test_medical_safety_ignores_quoted_section_headings():
    from app.services.medical_safety import SafetySource, run_medical_safety_checks

    report = run_medical_safety_checks(
        letter='The note section titled "Active Diagnosis" supports the appeal [1].',
        clinical_notes="Active Diagnoses: E11.65 Type 2 diabetes mellitus with hyperglycemia.",
        guideline_sources=[SafetySource(label="Reference 1", text="Diagnosis documentation is required.")],
    )

    assert report["checks"]["quotedClaimsGrounded"] is True
    assert not any(issue["code"] == "UNGROUNDED_QUOTE" for issue in report["issues"])


def test_medical_safety_fails_invalid_citation_and_placeholder():
    from app.services.medical_safety import SafetySource, run_medical_safety_checks

    report = run_medical_safety_checks(
        letter="Please approve [Address]. Unsupported citation [2].",
        clinical_notes="Pain score 8/10.",
        guideline_sources=[SafetySource(label="Reference 1", text="Pain score 8/10.")],
    )

    assert report["verdict"] == "FAIL"
    assert any(issue["code"] == "UNRESOLVED_PLACEHOLDER" for issue in report["issues"])
    assert any(issue["code"] == "INVALID_GUIDELINE_CITATION" for issue in report["issues"])


def test_sanitize_generated_letter_removes_letterhead_placeholders():
    from app.services.medical_safety import SafetySource, sanitize_generated_letter, run_medical_safety_checks

    letter = """[PHYSICIAN LETTERHEAD]

May 19, 2026

Dear Medical Director,

Please approve the request based on the documented record [1].

Sincerely,
[PHYSICIAN SIGNATURE]"""

    cleaned = sanitize_generated_letter(letter)
    report = run_medical_safety_checks(
        letter=cleaned,
        clinical_notes="Documented record.",
        guideline_sources=[SafetySource(label="Reference 1", text="Documented record.")],
    )

    assert "[PHYSICIAN LETTERHEAD]" not in cleaned
    assert "[PHYSICIAN SIGNATURE]" not in cleaned
    assert not any(issue["code"] == "UNRESOLVED_PLACEHOLDER" for issue in report["issues"])


def test_sanitize_generated_letter_reframes_documentation_gap_language():
    from app.services.medical_safety import sanitize_generated_letter

    cleaned = sanitize_generated_letter(
        """**Documentation Gaps**

[DOCUMENTATION GAP]: Preferred GLP-1 trial is not documented."""
    )

    assert "Documentation Gaps" not in cleaned
    assert "[DOCUMENTATION GAP]" not in cleaned
    assert "Clinical Rationale for Exception" in cleaned
    assert "Additional supporting rationale:" in cleaned


def test_appeal_prompt_does_not_request_payer_facing_documentation_gap_section():
    from app.services.prompts import APPEAL_REPAIR_SYSTEM, build_appeal_prompt

    prompt = build_appeal_prompt(
        clinical_notes="Diagnosis: Type 2 diabetes mellitus with hyperglycemia.",
        denial_reason="Requires preferred GLP-1 trial.",
        denied_service="Mounjaro",
        cpt_code="",
        icd10_codes="E11.65",
        insurance_company="Apex",
        patient_name="Jordan Rivera",
        patient_dob="04/17/1978",
        member_id="AXH-99384721",
        claim_number="PA-26-5189047",
        denial_date="05/13/2026",
        physician_name="Amelia Chen, MD",
        physician_npi="",
        practice_name="Bayview Endocrinology Associates",
        rag_context="Criterion: diagnosis of type 2 diabetes.",
        structured_analysis_context='{"documentationGaps":["Preferred GLP-1 trial"]}',
    )

    assert "**Section 6 — Documentation Gaps**" not in prompt
    assert 'Do NOT title any payer-facing section "Documentation Gaps"' in prompt
    assert "convert the claim into a documentation gap" not in APPEAL_REPAIR_SYSTEM
    assert "Do NOT add a payer-facing" in APPEAL_REPAIR_SYSTEM


def test_medical_safety_warns_on_ungrounded_numeric_claim():
    from app.services.medical_safety import SafetySource, run_medical_safety_checks

    report = run_medical_safety_checks(
        letter="The patient has pain score 9/10 and this meets criteria [1].",
        clinical_notes="The patient reports knee pain.",
        guideline_sources=[SafetySource(label="Reference 1", text="Pain severity must be documented.")],
    )

    assert report["verdict"] == "NEEDS_REVIEW"
    assert any(issue["code"] == "UNGROUNDED_NUMERIC_CLAIM" for issue in report["issues"])


def test_structured_medical_analysis_extracts_evidence_and_gaps():
    from app.services.medical_analysis import build_structured_medical_analysis
    from app.services.retrieval import retrieve_guideline_context

    rag_results = retrieve_guideline_context(
        denied_service="Total Knee Arthroplasty",
        denial_reason="Conservative treatment not documented.",
        cpt_codes="27447",
        icd10_codes="M17.11",
    )
    analysis = build_structured_medical_analysis(
        clinical_notes=(
            "Diagnosis: severe right knee osteoarthritis. "
            "Pain score 8/10 with difficulty walking stairs. "
            "Completed physical therapy for 6 weeks and NSAIDs without adequate relief."
        ),
        rag_results=rag_results,
    )

    assert analysis["evidenceSpans"]
    assert analysis["criteria"]
    assert analysis["policyMetadata"]
    assert analysis["auditTrail"]["promptVersion"] == "appeal-v2-structured-criteria"
    assert any(c["evidenceSpanIds"] for c in analysis["criteria"])


def test_structured_medical_analysis_matches_prescriber_specialist_evidence():
    from app.services.medical_analysis import build_structured_medical_analysis
    from app.services.retrieval import retrieve_guideline_context

    rag_results = retrieve_guideline_context(
        denied_service="Mounjaro",
        denial_reason="Prescriber specialty not documented.",
        cpt_codes="",
        icd10_codes="E11.65",
    )
    analysis = build_structured_medical_analysis(
        clinical_notes=(
            "Ordering/Rendering Provider Amelia Chen, MD, FACE. "
            "Clinic Bayview Endocrinology Associates. "
            "Diagnosis: Type 2 diabetes mellitus with hyperglycemia, ICD-10 E11.65. "
            "A1c 8.7%."
        ),
        rag_results=rag_results,
    )
    specialist_criteria = [
        criterion for criterion in analysis["criteria"]
        if "prescriber" in criterion["criterion"].lower() or "specialist" in criterion["criterion"].lower()
    ]

    assert specialist_criteria
    assert any(criterion["evidenceSpanIds"] for criterion in specialist_criteria)
    assert not any(
        "specific chart evidence supporting this criterion" in missing
        for criterion in specialist_criteria
        for missing in criterion["missingElements"]
    )


def test_structured_medical_analysis_flags_stale_policy_metadata():
    from app.services.medical_analysis import build_structured_medical_analysis
    from app.services.retrieval import retrieve_guideline_context

    rag_results = retrieve_guideline_context(
        denied_service="MRI lumbar spine",
        denial_reason="Not medically necessary.",
        cpt_codes="72148",
        icd10_codes="M54.5",
    )
    analysis = build_structured_medical_analysis(
        clinical_notes="Low back pain. MRI requested.",
        rag_results=rag_results,
    )

    assert analysis["policyMetadata"]
    assert all("freshnessStatus" in item for item in analysis["policyMetadata"])


def test_clinical_note_sufficiency_blocks_very_thin_notes():
    from app.services.medical_analysis import assess_clinical_note_sufficiency

    report = assess_clinical_note_sufficiency(
        clinical_notes="Patient wants medication.",
        denied_service="Mounjaro",
        denial_reason="Requires type 2 diabetes diagnosis, A1c, and metformin failure.",
    )

    assert report["status"] == "block"
    assert report["blockingReasons"]
    assert any("metformin" in item.lower() for item in report["suggestions"])


def test_clinical_note_sufficiency_allows_well_supported_notes():
    from app.services.medical_analysis import assess_clinical_note_sufficiency

    report = assess_clinical_note_sufficiency(
        clinical_notes=(
            "Diagnosis: Type 2 diabetes mellitus with hyperglycemia, ICD-10 E11.65. "
            "A1c 8.7% on 05/01/2026 despite therapy. "
            "Metformin IR and ER failed due to severe GI intolerance over 3 months. "
            "Empagliflozin stopped due to recurrent genital mycotic infections. "
            "Plan: initiate Mounjaro for glycemic control, not solely weight loss."
        ),
        denied_service="Mounjaro",
        denial_reason="Requires diabetes diagnosis, A1c above goal, and metformin failure.",
    )

    assert report["status"] in ("pass", "needs_review")
    assert report["score"] >= 75
    assert not report["blockingReasons"]


def test_document_parser_extracts_docx_text():
    from io import BytesIO
    from zipfile import ZipFile

    from app.services.document_parser import extract_document_text

    buf = BytesIO()
    with ZipFile(buf, "w") as archive:
        archive.writestr(
            "word/document.xml",
            """<?xml version="1.0" encoding="UTF-8"?>
            <w:document xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main">
              <w:body>
                <w:p><w:r><w:t>Patient has severe knee pain.</w:t></w:r></w:p>
                <w:p><w:r><w:t>Physical therapy failed after 6 weeks.</w:t></w:r></w:p>
              </w:body>
            </w:document>""",
        )

    text = extract_document_text(
        buf.getvalue(),
        "clinical-note.docx",
        "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    )

    assert "severe knee pain" in text
    assert "Physical therapy failed" in text
