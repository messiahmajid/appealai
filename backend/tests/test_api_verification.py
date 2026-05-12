from unittest.mock import AsyncMock, patch
import json

import pytest


@pytest.mark.asyncio
async def test_verify_appeal_missing_fields(client):
    resp = await client.post("/api/verify-appeal", json={"letter": "test letter"})
    assert resp.status_code == 422


@pytest.mark.asyncio
async def test_verify_appeal_success(client):
    mock_verification = {
        "overallVerdict": "PASS",
        "confidenceScore": 0.92,
        "checks": [
            {"check": "Clinical Data Accuracy", "status": "PASS", "details": "All accurate"},
            {"check": "Guideline Citation Accuracy", "status": "PASS", "details": "All present"},
            {"check": "No Fabricated Claims", "status": "PASS", "details": "None found"},
            {"check": "Denial Reason Addressed", "status": "PASS", "details": "Addressed"},
            {"check": "Documentation Gaps Acknowledged", "status": "PASS", "details": "Acknowledged"},
        ],
        "flaggedIssues": [],
        "summary": "Letter is accurate.",
    }

    with patch(
        "app.routers.verification.generate_text",
        new_callable=AsyncMock,
        return_value=json.dumps(mock_verification),
    ), patch("app.routers.verification.is_api_key_configured", return_value=True):
        resp = await client.post(
            "/api/verify-appeal",
            json={
                "letter": "This is a test appeal letter with sufficient content.",
                "clinicalNotes": "Patient clinical notes here",
                "ragContext": "Some guideline context",
                "denialReason": "Not medically necessary",
            },
        )
        assert resp.status_code == 200
        data = resp.json()
        assert "verification" in data
        v = data["verification"]
        assert v["overallVerdict"] in ("PASS", "NEEDS_REVIEW", "FAIL")
        assert 0 <= v["confidenceScore"] <= 1
        assert isinstance(v["checks"], list)
        assert isinstance(v["flaggedIssues"], list)
