from __future__ import annotations

import re
import unicodedata
from dataclasses import dataclass
from typing import Literal


SafetySeverity = Literal["error", "warning"]


@dataclass(frozen=True)
class SafetySource:
    label: str
    text: str


ALLOWED_BRACKET_CONTENT = re.compile(
    r"^(?:\d+|PubMed\s+\d+|Reference\s+\d+|DOCUMENTATION GAP(?::|\s|$).*)$",
    re.IGNORECASE,
)
PLACEHOLDER_HINTS = re.compile(
    r"\b(?:address|phone|fax|date|dob|birth|member|claim|insert|if known|not provided|"
    r"omitted|current|provider|physician|clinician|doctor|letterhead|practice|facility|"
    r"office|npi|name|signature|sincerely|to be|blank)\b",
    re.IGNORECASE,
)
CITATION_OR_SECTION_NUMBER = re.compile(r"^\d{1,2}$")
HEADING_ONLY_QUOTE = re.compile(
    r"^(?:active\s+)?(?:diagnosis|diagnoses|medications?|problems?|assessment|plan|"
    r"impression|history|clinical summary|review of systems|physical examination|"
    r"objective data|laboratory results|supporting documentation|documentation gaps?)$",
    re.IGNORECASE,
)


def _normalize_text(value: str) -> str:
    return (
        unicodedata.normalize("NFKC", value)
        .replace("“", '"')
        .replace("”", '"')
        .replace("‘", "'")
        .replace("’", "'")
        .replace("–", "-")
        .replace("—", "-")
        .replace("−", "-")
        .replace("²", "2")
        .replace("³", "3")
        .lower()
    )


def _normalize_for_grounding(value: str) -> str:
    text = _normalize_text(value).replace("&", " and ")
    text = re.sub(r"[^a-z0-9%/]+", " ", text)
    return re.sub(r"\s+", " ", text).strip()


def _grounding_tokens(value: str) -> list[str]:
    return [
        token
        for token in _normalize_for_grounding(value).split()
        if len(token) > 1 or re.search(r"\d", token)
    ]


def _has_ordered_token_window(quote: str, source: str) -> bool:
    quote_tokens = _grounding_tokens(quote)
    source_tokens = _grounding_tokens(source)
    if len(quote_tokens) < 4 or len(source_tokens) < len(quote_tokens):
        return False

    max_window = len(quote_tokens) + max(6, (3 * len(quote_tokens) + 3) // 4)
    for start, token in enumerate(source_tokens):
        if token != quote_tokens[0]:
            continue
        quote_index = 0
        for source_token in source_tokens[start : start + max_window]:
            if source_token == quote_tokens[quote_index]:
                quote_index += 1
                if quote_index == len(quote_tokens):
                    return True
    return False


def _source_contains(value: str, sources: list[SafetySource]) -> bool:
    normalized = _normalize_for_grounding(value)
    if not normalized:
        return True
    return any(
        normalized in _normalize_for_grounding(source.text)
        or _has_ordered_token_window(value, source.text)
        for source in sources
    )


def _unique(values: list[str]) -> list[str]:
    return list(dict.fromkeys(values))


def _find_bracket_issues(letter: str) -> list[dict]:
    issues: list[dict] = []
    for match in re.finditer(r"\[([^\]]+)\]", letter):
        content = match.group(1).strip()
        if ALLOWED_BRACKET_CONTENT.match(content):
            continue
        if PLACEHOLDER_HINTS.search(content) or not content.isdigit():
            issues.append(
                {
                    "code": "UNRESOLVED_PLACEHOLDER",
                    "severity": "error",
                    "message": f"Potential unresolved placeholder or unsupported bracketed text: [{content}]",
                    "evidence": f"[{content}]",
                }
            )
    return issues


def _is_placeholder_bracket(content: str) -> bool:
    if ALLOWED_BRACKET_CONTENT.match(content):
        return False
    return bool(PLACEHOLDER_HINTS.search(content) or re.match(r"^[A-Z0-9 _/-]{3,}$", content))


def sanitize_generated_letter(letter: str) -> str:
    text = re.sub(r"\s*\[SOURCE [A-Z]\]", "", letter)
    text = re.sub(
        r"^\s{0,3}(?:#{1,6}\s*)?(?:\*\*)?SECTION\s+\d+\s*[—\-:]\s*(?:HEADER\s*&\s*IDENTIFICATION|PURPOSE)(?:\*\*)?\s*$",
        "",
        text,
        flags=re.I | re.M,
    )
    text = re.sub(
        r"^\s{0,3}(?:#{1,6}\s*)?(?:\*\*)?SECTION\s+\d+\s*[—\-:]\s*",
        "",
        text,
        flags=re.I | re.M,
    )
    text = re.sub(
        r"^(\s{0,3}(?:#{1,6}\s*)?(?:\*\*)?)Documentation Gaps(?:\*\*)?\s*$",
        r"\1Clinical Rationale for Exception",
        text,
        flags=re.I | re.M,
    )
    text = re.sub(
        r"\[DOCUMENTATION GAP[.:]\s*(.*?)\]",
        r"Additional supporting rationale: \1",
        text,
        flags=re.S,
    )
    text = re.sub(r"\[DOCUMENTATION GAP\]\s*:\s*", "Additional supporting rationale: ", text)
    text = re.sub(r"\[DOCUMENTATION GAP[.:]\s*", "Additional supporting rationale: ", text)
    cleaned_lines: list[str] = []
    for line in text.splitlines():
        bracket_matches = list(re.finditer(r"\[([^\]]+)\]", line))
        if bracket_matches and all(_is_placeholder_bracket(m.group(1).strip()) for m in bracket_matches):
            cleaned_lines.append("")
            continue

        cleaned_lines.append(
            re.sub(
                r"\[([^\]]+)\]",
                lambda m: "" if _is_placeholder_bracket(m.group(1).strip()) else m.group(0),
                line,
            )
        )

    return re.sub(r"\n{3,}", "\n\n", "\n".join(cleaned_lines)).strip()


def _find_guideline_citation_issues(letter: str, guideline_count: int) -> list[dict]:
    issues: list[dict] = []
    numeric_refs = _unique(
        [
            match.group(1)
            for match in re.finditer(r"\[(\d+)\]", letter)
            if letter[max(0, match.start() - 10) : match.start()].lower().find("pubmed") == -1
        ]
    )

    for ref_text in numeric_refs:
        ref = int(ref_text)
        if ref < 1 or ref > guideline_count:
            issues.append(
                {
                    "code": "INVALID_GUIDELINE_CITATION",
                    "severity": "error",
                    "message": f"Guideline citation [{ref}] does not map to any retrieved guideline source.",
                    "evidence": f"[{ref}]",
                }
            )

    if guideline_count > 0 and not numeric_refs:
        issues.append(
            {
                "code": "MISSING_GUIDELINE_CITATIONS",
                "severity": "warning",
                "message": "Letter includes guideline context but does not cite any numbered guideline references.",
            }
        )

    return issues


def _find_pubmed_citation_issues(letter: str, pubmed_count: int) -> list[dict]:
    issues: list[dict] = []
    refs = _unique([match.group(1) for match in re.finditer(r"\[PubMed\s+(\d+)\]", letter, re.I)])
    for ref_text in refs:
        ref = int(ref_text)
        if ref < 1 or ref > pubmed_count:
            issues.append(
                {
                    "code": "INVALID_PUBMED_CITATION",
                    "severity": "error",
                    "message": f"PubMed citation [PubMed {ref}] does not map to any retrieved PubMed source.",
                    "evidence": f"[PubMed {ref}]",
                }
            )
    return issues


def _quoted_claim_needs_grounding(value: str) -> bool:
    if len(value) < 8:
        return False
    if re.match(r"^https?://", value, re.I):
        return False
    if HEADING_ONLY_QUOTE.match(value.strip()):
        return False
    return bool(
        re.search(
            r"\d|pain|mass|lesion|deficit|stenosis|fracture|cancer|tumor|malign|biopsy|"
            r"therapy|medication|exam|imaging|mri|ct|pet|x-ray|xray|lab|a1c|bmi|symptom|"
            r"diagnos|criterion|requires|denial|not medically necessary",
            value,
            re.I,
        )
    )


def _find_quoted_claim_issues(letter: str, sources: list[SafetySource]) -> list[dict]:
    issues: list[dict] = []
    quoted = _unique(
        [
            match.group(1).strip()
            for match in re.finditer(r'"([^"]{4,240})"', letter)
            if _quoted_claim_needs_grounding(match.group(1).strip())
        ]
    )
    for quote in quoted:
        if not _source_contains(quote, sources):
            issues.append(
                {
                    "code": "UNGROUNDED_QUOTE",
                    "severity": "warning",
                    "message": "Quoted clinical, denial, or guideline text was not found verbatim in the supplied sources.",
                    "evidence": quote,
                }
            )
    return issues


def _extract_numeric_facts(text: str) -> list[str]:
    facts = [
        match.group(0).strip()
        for match in re.finditer(
            r"\b(?:\d{1,2}[/-]\d{1,2}[/-]\d{2,4}|\d+(?:\.\d+)?\s?(?:%|mg/dL|mmHg|"
            r"cm|mm|kg/m2|kg/m²|weeks?|months?|years?|days?|hours?|/10|points?|"
            r"QALY|mL|L))\b",
            text,
            re.I,
        )
    ]
    return _unique([value for value in facts if not CITATION_OR_SECTION_NUMBER.match(value)])


def _find_numeric_claim_issues(letter: str, sources: list[SafetySource]) -> list[dict]:
    issues: list[dict] = []
    for value in _extract_numeric_facts(letter):
        if not _source_contains(value, sources):
            issues.append(
                {
                    "code": "UNGROUNDED_NUMERIC_CLAIM",
                    "severity": "warning",
                    "message": "Numeric value in the letter was not found in the clinical notes, guidelines, denial reason, or PubMed context.",
                    "evidence": value,
                }
            )
    return issues


def run_medical_safety_checks(
    *,
    letter: str,
    clinical_notes: str,
    denial_reason: str = "",
    guideline_sources: list[SafetySource] | None = None,
    pubmed_sources: list[SafetySource] | None = None,
) -> dict:
    guideline_sources = guideline_sources or []
    pubmed_sources = pubmed_sources or []
    all_sources = [
        SafetySource(label="clinicalNotes", text=clinical_notes),
        SafetySource(label="denialReason", text=denial_reason),
        *guideline_sources,
        *pubmed_sources,
    ]

    placeholder_issues = _find_bracket_issues(letter)
    guideline_citation_issues = _find_guideline_citation_issues(letter, len(guideline_sources))
    pubmed_citation_issues = _find_pubmed_citation_issues(letter, len(pubmed_sources))
    quoted_claim_issues = _find_quoted_claim_issues(letter, all_sources)
    numeric_claim_issues = _find_numeric_claim_issues(letter, all_sources)

    issues = [
        *placeholder_issues,
        *guideline_citation_issues,
        *pubmed_citation_issues,
        *quoted_claim_issues,
        *numeric_claim_issues,
    ]
    has_errors = any(issue["severity"] == "error" for issue in issues)
    has_warnings = any(issue["severity"] == "warning" for issue in issues)

    return {
        "verdict": "FAIL" if has_errors else "NEEDS_REVIEW" if has_warnings else "PASS",
        "issues": issues,
        "checks": {
            "placeholderFree": not placeholder_issues,
            "guidelineCitationsValid": not any(
                issue["severity"] == "error" for issue in guideline_citation_issues
            ),
            "pubMedCitationsValid": not pubmed_citation_issues,
            "quotedClaimsGrounded": not quoted_claim_issues,
            "numericClaimsGrounded": not numeric_claim_issues,
        },
    }


def safety_report_to_verification_checks(report: dict) -> list[dict]:
    checks = report["checks"]
    return [
        {
            "check": "Deterministic Placeholder Check",
            "status": "PASS" if checks["placeholderFree"] else "FAIL",
            "details": (
                "No unresolved bracket placeholders were detected."
                if checks["placeholderFree"]
                else " ".join(
                    issue["message"]
                    for issue in report["issues"]
                    if issue["code"] == "UNRESOLVED_PLACEHOLDER"
                )
            ),
        },
        {
            "check": "Deterministic Citation Check",
            "status": (
                "PASS"
                if checks["guidelineCitationsValid"] and checks["pubMedCitationsValid"]
                else "FAIL"
            ),
            "details": (
                "All numbered guideline and PubMed citations map to retrieved sources."
                if checks["guidelineCitationsValid"] and checks["pubMedCitationsValid"]
                else " ".join(
                    issue["message"] for issue in report["issues"] if "CITATION" in issue["code"]
                )
            ),
        },
        {
            "check": "Deterministic Grounding Check",
            "status": (
                "PASS"
                if checks["quotedClaimsGrounded"] and checks["numericClaimsGrounded"]
                else "WARNING"
            ),
            "details": (
                "Quoted and numeric claims were found in the supplied sources."
                if checks["quotedClaimsGrounded"] and checks["numericClaimsGrounded"]
                else " ".join(
                    f"{issue['message']} {issue.get('evidence', '')}"
                    for issue in report["issues"]
                    if "UNGROUNDED" in issue["code"]
                )
            ),
        },
    ]


def split_guideline_sources(rag_context: str) -> list[SafetySource]:
    if not rag_context.strip():
        return []
    matches = list(re.finditer(r"\[Reference\s+(\d+)\]", rag_context, re.I))
    if not matches:
        return [SafetySource(label="Guideline Context", text=rag_context)]
    sources: list[SafetySource] = []
    for index, match in enumerate(matches):
        end = matches[index + 1].start() if index + 1 < len(matches) else len(rag_context)
        sources.append(SafetySource(label=f"Reference {match.group(1)}", text=rag_context[match.start() : end]))
    return sources


def split_pubmed_sources(context: str) -> list[SafetySource]:
    matches = list(re.finditer(r"\[PubMed\s+(\d+)\]", context, re.I))
    sources: list[SafetySource] = []
    for index, match in enumerate(matches):
        end = matches[index + 1].start() if index + 1 < len(matches) else len(context)
        sources.append(SafetySource(label=f"PubMed {match.group(1)}", text=context[match.start() : end]))
    return sources
