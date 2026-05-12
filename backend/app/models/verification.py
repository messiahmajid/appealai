from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


class VerifyRequest(BaseModel):
    letter: str = Field(..., min_length=10)
    clinical_notes: str = Field(..., alias="clinicalNotes")
    rag_context: str = Field(default="", alias="ragContext")
    denial_reason: str = Field(..., alias="denialReason")

    model_config = ConfigDict(populate_by_name=True)


class VerificationCheck(BaseModel):
    check: str
    status: Literal["PASS", "FAIL", "WARNING"]
    details: str


class Verification(BaseModel):
    overall_verdict: str = Field(alias="overallVerdict")
    confidence_score: float = Field(alias="confidenceScore")
    checks: list[VerificationCheck]
    flagged_issues: list[str] = Field(alias="flaggedIssues")
    summary: str

    model_config = ConfigDict(populate_by_name=True, by_alias=True)


class VerifyResponse(BaseModel):
    verification: Verification
