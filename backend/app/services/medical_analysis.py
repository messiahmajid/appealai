from __future__ import annotations

import re
from datetime import datetime, timezone
from typing import Literal

from app.services.guidelines import get_guideline_by_id
from app.services.rag import RAGResult

CriterionStatus = Literal["met", "unclear", "not_met"]

STOP_WORDS = {
    "the", "and", "for", "with", "that", "this", "from", "when", "then", "than",
    "have", "has", "had", "are", "was", "were", "been", "being", "patient",
    "documented", "documentation", "required", "requires", "including", "include",
    "criteria", "criterion", "covered",
}


def _tokenize(text: str) -> list[str]:
    return [
        t.strip()
        for t in re.split(r"[^a-z0-9.]+", text.lower())
        if len(t.strip()) >= 4 and t.strip() not in STOP_WORDS
    ]


def _category(text: str) -> str:
    if re.search(r"provider|prescriber|physician|clinician|endocrinolog|diabetes specialist|\bFACE\b|ordering/rendering|clinic|practice|facility", text, re.I):
        return "provider"
    if re.search(r"diagnos|icd|cancer|osteoarthritis|stenosis|spondylolisthesis|apnea|diabetes|obesity|malignan", text, re.I):
        return "diagnosis"
    if re.search(r"mri|ct|pet|x-?ray|radiograph|imaging|biopsy|patholog|lab|a1c|ahi", text, re.I):
        return "imaging"
    if re.search(r"therapy|pt\b|nsaid|injection|conservative|surgery|medication|trial|failed|treatment", text, re.I):
        return "treatment"
    if re.search(r"adl|walking|stairs|function|womac|koos|pain|vas|limitation|mobility", text, re.I):
        return "functional"
    if re.search(r"risk|bmi|smok|hypertension|contraindicat|infection|cardiac", text, re.I):
        return "risk"
    if re.search(r"mg|dose|methotrexate|biologic|cpap|drug|medication", text, re.I):
        return "medication"
    return "other"


def extract_evidence_spans(clinical_notes: str) -> list[dict]:
    spans: list[dict] = []
    pattern = re.compile(r"[^\n.!?;:]{8,260}(?:[.!?;:]|\n|$)")
    for match in pattern.finditer(clinical_notes):
        text = match.group(0).strip()
        if not text or not re.search(
            r"\d|diagnos|pain|failed|therapy|mri|ct|pet|x-?ray|biopsy|lab|symptom|"
            r"function|medication|risk|plan|recommend|conservative|provider|prescriber|"
            r"physician|clinician|endocrinolog|diabetes specialist|\bFACE\b|ordering/rendering|"
            r"clinic|practice|facility",
            text,
            re.I,
        ):
            continue
        spans.append(
            {
                "id": f"E{len(spans) + 1}",
                "text": text,
                "category": _category(text),
                "start": match.start(),
                "end": match.end(),
            }
        )
    return spans[:80]


def _overlap_score(criterion: str, span: dict) -> int:
    criterion_tokens = set(_tokenize(criterion))
    span_tokens = set(_tokenize(span["text"]))
    score = len(criterion_tokens & span_tokens)
    if re.search(r"\bfailed|failure|conservative|therapy|treatment\b", criterion, re.I) and re.search(r"\bfailed|failure|conservative|therapy|treatment\b", span["text"], re.I):
        score += 2
    if re.search(r"\bpain|functional|adl|walking|mobility\b", criterion, re.I) and re.search(r"\bpain|functional|adl|walking|mobility\b", span["text"], re.I):
        score += 2
    if re.search(r"\bimaging|radiograph|mri|ct|pet|biopsy|patholog\b", criterion, re.I) and re.search(r"\bimaging|radiograph|mri|ct|pet|biopsy|patholog\b", span["text"], re.I):
        score += 2
    if re.search(r"\bdiagnos|confirmed|malignan|osteoarthritis|cancer\b", criterion, re.I) and re.search(r"\bdiagnos|confirmed|malignan|osteoarthritis|cancer\b", span["text"], re.I):
        score += 2
    if re.search(r"\bprescriber|specialist|endocrinologist|clinician|provider|physician\b", criterion, re.I) and re.search(r"\bprovider|prescriber|physician|clinician|endocrinolog|diabetes specialist|FACE|clinic|practice|facility\b", span["text"], re.I):
        score += 3
    return score


def _missing_elements(criterion: str, matched: list[dict]) -> list[str]:
    if matched:
        return []
    lower = criterion.lower()
    missing: list[str] = []
    if re.search(r"diagnos|confirmed|malignan|patholog|biopsy", lower):
        missing.append("documented diagnosis/pathology confirmation")
    if re.search(r"imaging|radiograph|mri|ct|pet", lower):
        missing.append("supporting imaging or test result")
    if re.search(r"failed|conservative|therapy|treatment|months|weeks", lower):
        missing.append("duration and outcome of conservative treatment")
    if re.search(r"functional|adl|pain|vas|womac|mobility", lower):
        missing.append("functional limitation or pain severity documentation")
    if re.search(r"optimized|bmi|a1c|smoking|clearance", lower):
        missing.append("medical optimization or risk-factor documentation")
    if re.search(r"prescriber|specialist|endocrinologist|clinician|provider|physician", lower):
        missing.append("specialist or prescribing clinician documentation")
    return missing or ["specific chart evidence supporting this criterion"]


def _classify(criterion: str, matched: list[dict]) -> CriterionStatus:
    if re.search(r"non-covered|not covered|contraindicat", criterion, re.I):
        return "not_met"
    # Keyword overlap is a retrieval signal, not proof that all required clinical
    # elements are satisfied. Keep matches as clinician-reviewable unless a later
    # element-level validator can prove exact thresholds/durations.
    if matched:
        return "unclear"
    return "unclear"


def _policy_type(source: str) -> str:
    if re.search(r"National Coverage Determination|NCD", source, re.I):
        return "CMS_NCD"
    if re.search(r"Local Coverage Determination|LCD", source, re.I):
        return "CMS_LCD"
    if re.search(r"National Comprehensive Cancer Network|NCCN", source, re.I):
        return "NCCN"
    if re.search(r"Commercial", source, re.I):
        return "COMMERCIAL_POLICY"
    return "OTHER"


def _freshness_status(effective_date: str) -> str:
    try:
        effective = datetime.fromisoformat(effective_date)
    except ValueError:
        return "review_due"
    age_days = (datetime.now() - effective).days
    if age_days > 900:
        return "stale"
    if age_days > 365:
        return "review_due"
    return "current"


def _contraindication_warnings(rag_results: list[RAGResult], clinical_notes: str) -> list[str]:
    warnings: list[str] = []
    note = clinical_notes.lower()
    for result in rag_results:
        match = re.search(r"Non-Covered Indications:[\s\S]*?(?=\n\n[A-Z][A-Za-z ]+:|\n\n[A-Z][A-Za-z ]+\n|$)", result.text, re.I)
        if not match:
            continue
        for line in match.group(0).splitlines():
            clean = re.sub(r"^[-\d.\s]+", "", line).strip()
            if not clean:
                continue
            terms = _tokenize(clean)[:6]
            if len(terms) >= 2 and any(term in note for term in terms):
                warnings.append(f"{result.title}: possible non-covered indication overlap - {clean}")
    return warnings[:10]


def _payer_requirement_suggestions(denial_reason: str, clinical_notes: str) -> list[str]:
    denial = denial_reason.lower()
    notes = clinical_notes.lower()
    suggestions: list[str] = []

    if "metformin" in denial and "metformin" not in notes:
        suggestions.append(
            "Document metformin use, intolerance, contraindication, or the clinical reason it is inappropriate."
        )
    if re.search(r"\b(ozempic|trulicity|glp-?1|preferred formulary|step therapy)\b", denial) and not re.search(
        r"\b(ozempic|trulicity|semaglutide|dulaglutide|liraglutide|glp-?1)\b", notes
    ):
        suggestions.append(
            "Document preferred formulary or step-therapy trials, failures, intolerance, or contraindications."
        )
    if re.search(r"\bweight loss|solely for weight\b", denial) and not re.search(
        r"\b(type 2 diabetes|diabetes|a1c|hba1c|e11\.)\b", notes
    ):
        suggestions.append(
            "Document that the requested drug is for type 2 diabetes or another covered indication, not solely weight loss."
        )
    if re.search(r"\bconservative|physical therapy|nsaid|therapy\b", denial) and not re.search(
        r"\b(failed|tried|trial|completed|physical therapy|pt\b|nsaid|injection|conservative)\b", notes
    ):
        suggestions.append(
            "Document conservative treatment attempts with dates, duration, response, and reason for failure."
        )
    if re.search(r"\bimaging|x-?ray|mri|ct|radiograph\b", denial) and not re.search(
        r"\b(x-?ray|radiograph|mri|ct|ultrasound|imaging|report)\b", notes
    ):
        suggestions.append("Add relevant imaging or test results, including date and impression.")

    return suggestions


def assess_clinical_note_sufficiency(
    *,
    clinical_notes: str,
    denied_service: str,
    denial_reason: str,
    structured_analysis: dict | None = None,
) -> dict:
    notes = clinical_notes.strip()
    evidence_spans = (structured_analysis or {}).get("evidenceSpans") or extract_evidence_spans(notes)
    lower = notes.lower()

    elements = [
        {
            "key": "diagnosis",
            "label": "Diagnosis or covered indication",
            "weight": 20,
            "present": bool(
                re.search(
                    r"\b(diagnos|assessment|impression|icd-?10|dx\b|type 2 diabetes|diabetes|"
                    r"osteoarthritis|cancer|malignan|angina|stenosis|sleep apnea|e11\.)\b",
                    lower,
                    re.I,
                )
            )
            or any(span["category"] == "diagnosis" for span in evidence_spans),
            "suggestion": "Add the diagnosis/covered indication and ICD-10 code when available.",
        },
        {
            "key": "objective",
            "label": "Objective findings, labs, imaging, or measured severity",
            "weight": 20,
            "present": bool(
                re.search(
                    r"\b(a1c|hba1c|bmi|ldl|ef|ahi|kellgren|grade|stage|mm|cm|x-?ray|"
                    r"radiograph|mri|ct|pet|biopsy|pathology|stress test|echo|ultrasound|"
                    r"\d+\/10|%|\d+\.\d+)\b",
                    lower,
                    re.I,
                )
            )
            or any(span["category"] == "imaging" for span in evidence_spans),
            "suggestion": (
                "Add objective support such as labs, imaging/test reports, measured severity, "
                "or dated exam findings."
            ),
        },
        {
            "key": "treatment",
            "label": "Prior treatment history, failure, intolerance, or contraindication",
            "weight": 20,
            "present": bool(
                re.search(
                    r"\b(failed|failure|tried|trial|completed|intoler|contraindicat|therapy|"
                    r"physical therapy|pt\b|nsaid|injection|medication|metformin|insulin|"
                    r"ozempic|trulicity|empagliflozin|glipizide|statin)\b",
                    lower,
                    re.I,
                )
            )
            or any(span["category"] in ("treatment", "medication") for span in evidence_spans),
            "suggestion": (
                "Add prior therapies with dates/duration, outcome, intolerance, contraindication, "
                "or reason alternatives are inappropriate."
            ),
        },
        {
            "key": "timeline",
            "label": "Dates or treatment duration",
            "weight": 15,
            "present": bool(
                re.search(
                    r"\b\d{1,2}[/-]\d{1,2}[/-]\d{2,4}\b|\b\d+\s*(day|days|week|weeks|month|months|year|years)\b|\bsince\b|\bfrom\b",
                    lower,
                    re.I,
                )
            ),
            "suggestion": "Add dates and durations for symptoms, medication trials, procedures, and failed treatments.",
        },
        {
            "key": "symptoms",
            "label": "Symptoms, functional impact, or clinical risk",
            "weight": 15,
            "present": bool(
                re.search(
                    r"\b(pain|symptom|dyspnea|angina|hypoglycemia|infection|walking|stairs|"
                    r"adl|function|limitation|worsening|risk|comorbid|hypertension|obesity|cardiac)\b",
                    lower,
                    re.I,
                )
            )
            or any(span["category"] in ("functional", "risk") for span in evidence_spans),
            "suggestion": "Add symptom severity, functional limitations, clinical risk, or impact on daily activities.",
        },
        {
            "key": "plan",
            "label": "Clear request, plan, or medical rationale",
            "weight": 10,
            "present": bool(
                re.search(
                    r"\b(plan|recommend|request|requires|medical necessity|medically necessary|"
                    r"prescribed|initiate|proceed|refer)\b",
                    lower,
                    re.I,
                )
            )
            or denied_service.lower() in lower,
            "suggestion": "Add the requested service/drug and the clinician rationale for why it is medically necessary now.",
        },
    ]

    present_elements = [element["label"] for element in elements if element["present"]]
    missing_elements = [element["label"] for element in elements if not element["present"]]
    suggestions = [element["suggestion"] for element in elements if not element["present"]]
    suggestions.extend(_payer_requirement_suggestions(denial_reason, notes))
    score = min(100, sum(element["weight"] for element in elements if element["present"]) + min(10, len(evidence_spans)))

    blocking_reasons: list[str] = []
    if len(notes) < 120:
        blocking_reasons.append("Clinical notes are too short to support a medically grounded appeal.")
    if not elements[0]["present"] and not elements[1]["present"]:
        blocking_reasons.append(
            "Clinical notes do not clearly document a diagnosis/indication or objective clinical support."
        )
    if score < 45:
        blocking_reasons.append("Clinical notes are missing too many core medical-necessity elements.")

    unique_suggestions = list(dict.fromkeys(suggestions))[:8]
    warnings = list(
        dict.fromkeys(
            _payer_requirement_suggestions(denial_reason, notes)
            + (structured_analysis or {}).get("contraindicationWarnings", [])
        )
    )[:8]
    status = "block" if blocking_reasons else "needs_review" if score < 75 or unique_suggestions else "pass"

    return {
        "status": status,
        "score": score,
        "summary": (
            "The clinical notes are not sufficient to generate a medically grounded appeal yet."
            if status == "block"
            else "The clinical notes can be used, but adding the missing details would strengthen the appeal."
            if status == "needs_review"
            else "The clinical notes contain the core elements needed for a grounded appeal."
        ),
        "presentElements": present_elements,
        "missingElements": missing_elements,
        "blockingReasons": blocking_reasons,
        "suggestions": unique_suggestions,
        "warnings": warnings,
    }


def build_structured_medical_analysis(*, clinical_notes: str, rag_results: list[RAGResult]) -> dict:
    evidence_spans = extract_evidence_spans(clinical_notes)
    criteria: list[dict] = []
    policy_metadata: list[dict] = []

    for result in rag_results:
        guideline = get_guideline_by_id(result.guideline_id)
        if guideline:
            policy_metadata.append(
                {
                    "guidelineId": guideline.id,
                    "title": guideline.title,
                    "source": guideline.source,
                    "effectiveDate": guideline.effective_date,
                    "lastReviewed": datetime.now(timezone.utc).date().isoformat(),
                    "policyType": _policy_type(guideline.source),
                    "freshnessStatus": _freshness_status(guideline.effective_date),
                }
            )

        for criterion in (guideline.approval_criteria if guideline else []):
            ranked = sorted(
                [
                    {"span": span, "score": _overlap_score(criterion, span)}
                    for span in evidence_spans
                    if _overlap_score(criterion, span) >= 2
                ],
                key=lambda item: item["score"],
                reverse=True,
            )[:3]
            matched = [item["span"] for item in ranked]
            status = _classify(criterion, matched)
            missing = _missing_elements(criterion, matched)
            criteria.append(
                {
                    "guidelineId": result.guideline_id,
                    "guidelineTitle": result.title,
                    "criterion": criterion,
                    "status": status,
                    "evidenceSpanIds": [span["id"] for span in matched],
                    "missingElements": missing,
                    "rationale": (
                        f"Candidate chart evidence span(s): {', '.join(span['id'] for span in matched)}. "
                        "Clinician review required before treating the criterion as met."
                        if matched
                        else f"No direct chart evidence found for: {', '.join(missing)}."
                    ),
                }
            )

    gaps = []
    for criterion in criteria:
        if criterion["status"] != "met":
            gaps.extend(f"{criterion['guidelineTitle']}: {m}" for m in criterion["missingElements"])

    return {
        "evidenceSpans": evidence_spans,
        "criteria": criteria,
        "documentationGaps": list(dict.fromkeys(gaps))[:20],
        "contraindicationWarnings": _contraindication_warnings(rag_results, clinical_notes),
        "policyMetadata": policy_metadata,
        "auditTrail": {
            "generatedAt": datetime.now(timezone.utc).isoformat(),
            "promptVersion": "appeal-v2-structured-criteria",
            "safetyPolicyVersion": "medical-safety-v2",
            "modelRole": "drafting-support-with-deterministic-grounding-checks",
            "sourceGuidelineIds": [r.guideline_id for r in rag_results],
        },
    }


def format_structured_analysis_for_prompt(analysis: dict) -> str:
    import json

    return json.dumps(
        {
            "instructions": (
                "Use this as a planning aid. Do not cite this JSON as a source. Cite only Source A/B/C. "
                "If a criterion is unclear or not_met, state a documentation gap instead of claiming it is met."
            ),
            "evidenceSpans": [
                {"id": span["id"], "category": span["category"], "text": span["text"]}
                for span in analysis["evidenceSpans"]
            ],
            "criteria": analysis["criteria"],
            "documentationGaps": analysis["documentationGaps"],
            "contraindicationWarnings": analysis["contraindicationWarnings"],
            "policyMetadata": analysis["policyMetadata"],
        },
        indent=2,
    )
