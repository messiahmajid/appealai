from app.services.guidelines import get_guidelines_by_code
from app.services.rag import RAGResult, search_rag_fallback


def _split_codes(codes: str) -> list[str]:
    return [c.strip() for c in codes.replace(";", ",").split(",") if c.strip()]


def retrieve_guideline_context(
    *,
    denied_service: str,
    denial_reason: str,
    cpt_codes: str,
    icd10_codes: str,
    max_results: int = 3,
) -> list[RAGResult]:
    """Select guideline context for appeal generation.

    Code matches are treated as authoritative. Keyword fallback is only used when no
    CPT/ICD-10 guideline match exists, which prevents unrelated high-frequency
    keyword matches from being cited in otherwise well-coded requests.
    """
    seen_ids: set[str] = set()
    results: list[RAGResult] = []

    for code in [*_split_codes(cpt_codes), *_split_codes(icd10_codes)]:
        for guideline in get_guidelines_by_code(code):
            if guideline.id in seen_ids:
                continue
            seen_ids.add(guideline.id)
            results.append(
                RAGResult(
                    text=f"[{guideline.title}] [Source: {guideline.source}]\n{guideline.content}",
                    guideline_id=guideline.id,
                    title=guideline.title,
                    source=guideline.source,
                    score=1.0,
                )
            )

    if results:
        return results[:max_results]

    rag_query = f"{denied_service} {denial_reason} {cpt_codes} {icd10_codes}"
    return search_rag_fallback(rag_query, max_results)
