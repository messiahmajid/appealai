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
    check_letter_structure,
    check_no_hallucinated_guidelines,
    check_patient_data_accuracy,
    check_response_schema,
    check_verification_passes,
)


SAMPLE_CASES = [
    {
        "id": "ortho-tka",
        "clinicalNotes": "PATIENT: Margaret Thompson\nDOB: 05/12/1957\nSevere bilateral knee OA, KL Grade 4, bone-on-bone. Failed 8 months conservative: PT 24 sessions, meloxicam, corticosteroid injections x4, HA injection, bracing. WOMAC 72/96, VAS 8/10. BMI 29.8, A1c 6.8%.",
        "denialReason": "Insufficient documentation of conservative management.",
        "deniedService": "Total Knee Arthroplasty, Right",
        "cptCodes": "27447",
        "icd10Codes": "M17.11",
        "insuranceCompany": "UnitedHealthcare",
        "patientName": "Margaret Thompson",
        "patientDOB": "05/12/1957",
        "memberId": "UHC-887234561",
        "claimNumber": "PA-2026-0115-89234",
        "denialDate": "01/28/2026",
        "physicianName": "Dr. Sarah Mitchell, MD",
        "physicianNPI": "1234567890",
        "practiceName": "Advanced Orthopedic Associates",
    },
    {
        "id": "cardio-cath",
        "clinicalNotes": "PATIENT: Robert Williams\nDOB: 08/23/1953\nNew-onset exertional angina. Stress echo: 2.5mm ST depression V2-V5, NEW hypokinesis anterior wall/septum/apex (LAD territory). High-risk: early ischemia Stage 2, large territory. A1c 7.2%, LDL 142.",
        "denialReason": "Stress testing results do not meet criteria for invasive cardiac catheterization.",
        "deniedService": "Left Heart Catheterization with Coronary Angiography",
        "cptCodes": "93458",
        "icd10Codes": "I20.9, I25.10",
        "insuranceCompany": "Anthem Blue Cross Blue Shield",
        "patientName": "Robert Williams",
        "patientDOB": "08/23/1953",
        "memberId": "ANT-443876210",
        "claimNumber": "PA-2026-0203-55612",
        "denialDate": "02/08/2026",
        "physicianName": "Dr. James Chen, MD, FACC",
        "physicianNPI": "9876543210",
        "practiceName": "Heart & Vascular Institute",
    },
    {
        "id": "onc-pet",
        "clinicalNotes": "PATIENT: David Kowalski\nDOB: 11/30/1964\nBiopsy-confirmed NSCLC adenocarcinoma RUL. CT: 4.5x3.8cm mass, mediastinal LN (station 4R 2.1cm, station 7 1.8cm). Stage cT2bN2M0 IIIA. PET/CT needed for staging.",
        "denialReason": "PET/CT is considered experimental/investigational. Standard CT sufficient for staging.",
        "deniedService": "PET/CT Whole Body for Tumor Staging",
        "cptCodes": "78816",
        "icd10Codes": "C34.11, R91.1",
        "insuranceCompany": "Aetna",
        "patientName": "David Kowalski",
        "patientDOB": "11/30/1964",
        "memberId": "AET-776543890",
        "claimNumber": "PA-2026-0212-33478",
        "denialDate": "02/15/2026",
        "physicianName": "Dr. Aisha Patel, MD",
        "physicianNPI": "5678901234",
        "practiceName": "Cancer Center of Greater Philadelphia",
    },
]

EXPECTED_APPEAL_KEYS = ["appealId", "letter", "citations", "ragSources", "webEvidence"]
EXPECTED_VERIFY_KEYS = ["overallVerdict", "confidenceScore", "checks", "flaggedIssues", "summary"]


def run_evaluation(base_url: str) -> dict:
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

    for case in SAMPLE_CASES:
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
    args = parser.parse_args()

    results = run_evaluation(args.base_url)

    if args.output:
        with open(args.output, "w") as f:
            json.dump(results, f, indent=2)
        print(f"\nResults saved to {args.output}")
