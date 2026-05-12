"""
Automated evaluation pipeline for AppealAI.

Tests output quality and API response consistency across sample cases.
Run: python -m eval.run_eval --base-url http://localhost:8000
"""

import argparse
import json
import sys
import time

import httpx

from eval.metrics import (
    check_citations_present,
    check_denial_reason_addressed,
    check_expected_guideline_sources,
    check_letter_structure,
    check_no_hallucinated_guidelines,
    check_patient_data_accuracy,
    check_response_schema,
    check_verification_passes,
)
from eval.scenarios import EVALUATION_CASES

EXPECTED_APPEAL_KEYS = ["appealId", "letter", "citations", "ragSources", "webEvidence"]
EXPECTED_VERIFY_KEYS = ["overallVerdict", "confidenceScore", "checks", "flaggedIssues", "summary"]


def run_evaluation(base_url: str, limit: int | None = None) -> dict:
    results = {"cases": [], "summary": {"total_checks": 0, "passed": 0, "failed": 0}}

    client = httpx.Client(base_url=base_url, timeout=120)

    # Health check
    try:
        resp = client.get("/health")
        if resp.status_code != 200:
            print(f"ERROR: Backend not reachable at {base_url}")
            sys.exit(1)
    except Exception as e:
        print(f"ERROR: Cannot connect to {base_url}: {e}")
        sys.exit(1)

    cases = EVALUATION_CASES[:limit] if limit else EVALUATION_CASES

    for case in cases:
        case_id = case["id"]
        print(f"\n{'='*60}")
        print(f"Evaluating case: {case_id}")
        print(f"{'='*60}")

        case_result = {"case_id": case_id, "checks": {}, "elapsed_seconds": 0}

        # Generate appeal
        start = time.time()
        try:
            resp = client.post("/api/generate-appeal", json=case)
            elapsed = time.time() - start
            case_result["elapsed_seconds"] = round(elapsed, 1)

            if resp.status_code != 200:
                case_result["error"] = f"HTTP {resp.status_code}: {resp.text[:200]}"
                results["cases"].append(case_result)
                continue

            data = resp.json()
        except Exception as e:
            case_result["error"] = str(e)
            results["cases"].append(case_result)
            continue

        # Check 1: Response schema
        schema_check = check_response_schema(data, EXPECTED_APPEAL_KEYS)
        case_result["checks"]["response_schema"] = schema_check
        _tally(results, schema_check)

        letter = data.get("letter", "")
        citations = data.get("citations", [])
        rag_sources = data.get("ragSources", [])

        # Check 1b: Expected guideline family retrieved
        expected_sources_check = check_expected_guideline_sources(
            rag_sources, case.get("expectedGuidelineIds", [])
        )
        case_result["checks"]["expected_guideline_sources"] = expected_sources_check
        _tally(results, expected_sources_check)

        # Check 2: Letter structure
        structure_check = check_letter_structure(letter)
        case_result["checks"]["letter_structure"] = structure_check
        _tally(results, structure_check)

        # Check 3: Citations present
        citation_check = check_citations_present(letter, citations)
        case_result["checks"]["citations_present"] = citation_check
        _tally(results, citation_check)

        # Check 4: No hallucinated guidelines
        hallucination_check = check_no_hallucinated_guidelines(letter, rag_sources)
        case_result["checks"]["no_hallucinated_guidelines"] = hallucination_check
        _tally(results, hallucination_check)

        # Check 5: Patient data accuracy
        patient_check = check_patient_data_accuracy(letter, case["clinicalNotes"])
        case_result["checks"]["patient_data_accuracy"] = patient_check
        _tally(results, patient_check)

        # Check 6: Denial reason addressed
        denial_check = check_denial_reason_addressed(letter, case["denialReason"])
        case_result["checks"]["denial_reason_addressed"] = denial_check
        _tally(results, denial_check)

        # Check 7: Response time
        time_check = {"passed": elapsed < 120, "elapsed": round(elapsed, 1)}
        case_result["checks"]["response_time"] = time_check
        _tally(results, time_check)

        # Check 8: Verification
        try:
            verify_resp = client.post(
                "/api/verify-appeal",
                json={
                    "letter": letter,
                    "clinicalNotes": case["clinicalNotes"],
                    "ragContext": "\n".join(s.get("title", "") for s in rag_sources),
                    "denialReason": case["denialReason"],
                },
            )
            if verify_resp.status_code == 200:
                verification = verify_resp.json().get("verification", {})
                verify_check = check_verification_passes(verification)
                case_result["checks"]["verification"] = verify_check
                _tally(results, verify_check)
        except Exception as e:
            case_result["checks"]["verification"] = {"passed": False, "error": str(e)}
            _tally(results, {"passed": False})

        # Print per-case summary
        for name, check in case_result["checks"].items():
            status = "PASS" if check.get("passed") else "FAIL"
            print(f"  [{status}] {name}")

        results["cases"].append(case_result)

    # Final summary
    s = results["summary"]
    print(f"\n{'='*60}")
    print(f"EVALUATION COMPLETE: {s['passed']}/{s['total_checks']} checks passed")
    print(f"{'='*60}")

    return results


def _tally(results: dict, check: dict):
    results["summary"]["total_checks"] += 1
    if check.get("passed"):
        results["summary"]["passed"] += 1
    else:
        results["summary"]["failed"] += 1


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Run AppealAI evaluation pipeline")
    parser.add_argument("--base-url", default="http://localhost:8000", help="Backend base URL")
    parser.add_argument("--output", default=None, help="Save results to JSON file")
    parser.add_argument("--limit", default=None, type=int, help="Limit number of cases")
    args = parser.parse_args()

    results = run_evaluation(args.base_url, args.limit)

    if args.output:
        with open(args.output, "w") as f:
            json.dump(results, f, indent=2)
        print(f"\nResults saved to {args.output}")
