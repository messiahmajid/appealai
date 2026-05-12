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


def test_eval_suite_contains_more_than_fifty_scenarios():
    from eval.scenarios import EVALUATION_CASES

    assert len(EVALUATION_CASES) >= 50
    assert all(case.get("expectedGuidelineIds") for case in EVALUATION_CASES)
