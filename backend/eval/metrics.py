"""Output quality metrics for appeal letter evaluation."""

import re


def check_letter_structure(letter: str) -> dict:
    """Verify letter has required sections."""
    sections = {
        "header": bool(re.search(r"(RE:|Re:|Subject:|Dear)", letter)),
        "denial_quoted": bool(re.search(r'(denial|denied|reason)', letter, re.IGNORECASE)),
        "clinical_summary": bool(re.search(r'(clinical|history|present illness)', letter, re.IGNORECASE)),
        "criterion_mapping": bool(re.search(r'(criterion|criteria|guideline|requirement)', letter, re.IGNORECASE)),
        "rebuttal": bool(re.search(r'(rebut|address|contrary|however|respectfully)', letter, re.IGNORECASE)),
        "closing": bool(re.search(r'(reconsider|sincerely|respectfully|request)', letter, re.IGNORECASE)),
    }
    return {
        "passed": all(sections.values()),
        "sections": sections,
        "score": sum(sections.values()) / len(sections),
    }


def check_citations_present(letter: str, citations: list[dict]) -> dict:
    """Verify citation markers appear in the letter."""
    expected = len(citations)
    found = len(set(re.findall(r'\[(\d+)\]', letter)))
    return {
        "passed": found > 0 and found >= expected * 0.5,
        "expected": expected,
        "found": found,
    }


def check_no_hallucinated_guidelines(letter: str, rag_sources: list[dict]) -> dict:
    """Check that cited guideline names appear in rag_sources."""
    known_titles = {s.get("title", "").lower() for s in rag_sources}
    guideline_refs = re.findall(r'(?:CMS |LCD |NCCN |NCD )\S+', letter)

    flagged = []
    for ref in guideline_refs:
        ref_lower = ref.lower().strip()
        if not any(ref_lower in t for t in known_titles):
            flagged.append(ref)

    return {
        "passed": len(flagged) == 0,
        "flagged_references": flagged,
    }


def check_patient_data_accuracy(letter: str, clinical_notes: str) -> dict:
    """Check patient name and key data points appear in letter."""
    # Extract patient name from notes
    name_match = re.search(r'PATIENT:\s*(.+)', clinical_notes)
    patient_name = name_match.group(1).strip() if name_match else ""

    checks = {}
    if patient_name:
        # Check first name or last name appears
        name_parts = patient_name.split()
        checks["patient_name"] = any(part in letter for part in name_parts if len(part) > 2)

    return {
        "passed": all(checks.values()) if checks else True,
        "checks": checks,
    }


def check_denial_reason_addressed(letter: str, denial_reason: str) -> dict:
    """Verify the denial reason is quoted or paraphrased in the letter."""
    # Check if key phrases from denial appear
    denial_words = [w.lower() for w in denial_reason.split() if len(w) > 4]
    found_words = sum(1 for w in denial_words if w in letter.lower())
    coverage = found_words / max(len(denial_words), 1)

    return {
        "passed": coverage >= 0.3,
        "coverage": round(coverage, 2),
    }


def check_response_schema(response: dict, expected_keys: list[str]) -> dict:
    """Validate API response has expected keys."""
    missing = [k for k in expected_keys if k not in response]
    return {
        "passed": len(missing) == 0,
        "missing_keys": missing,
    }


def check_expected_guideline_sources(rag_sources: list[dict], expected_guideline_ids: list[str]) -> dict:
    """Verify retrieval includes the expected policy/guideline family."""
    found_ids = {s.get("guidelineId", s.get("guideline_id", "")) for s in rag_sources}
    expected = set(expected_guideline_ids)
    matched = expected & found_ids
    return {
        "passed": bool(matched),
        "expected": sorted(expected),
        "found": sorted(found_ids),
        "matched": sorted(matched),
    }


def check_verification_passes(verification: dict) -> dict:
    """Check verification endpoint returns non-FAIL verdict."""
    verdict = verification.get("overallVerdict", "FAIL")
    return {
        "passed": verdict in ("PASS", "NEEDS_REVIEW"),
        "verdict": verdict,
        "confidence": verification.get("confidenceScore", 0),
    }
