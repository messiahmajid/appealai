import json

from pydantic import BaseModel, ConfigDict, Field


class AppealCreate(BaseModel):
    clinical_notes: str = Field(..., min_length=10, alias="clinicalNotes")
    denial_reason: str = Field(..., min_length=5, alias="denialReason")
    denied_service: str = Field(..., min_length=2, alias="deniedService")
    cpt_codes: str = Field(default="", alias="cptCodes")
    icd10_codes: str = Field(default="", alias="icd10Codes")
    insurance_company: str = Field(default="", alias="insuranceCompany")
    patient_name: str = Field(default="Unknown", alias="patientName")
    patient_dob: str = Field(default="", alias="patientDOB")
    member_id: str = Field(default="", alias="memberId")
    claim_number: str = Field(default="", alias="claimNumber")
    denial_date: str = Field(default="", alias="denialDate")
    physician_name: str = Field(default="", alias="physicianName")
    physician_npi: str = Field(default="", alias="physicianNPI")
    practice_name: str = Field(default="", alias="practiceName")

    model_config = ConfigDict(populate_by_name=True)


class Citation(BaseModel):
    index: int
    guideline_id: str = Field(alias="guidelineId")
    title: str
    source: str
    text: str

    model_config = ConfigDict(populate_by_name=True, by_alias=True)


class RAGSourceItem(BaseModel):
    guideline_id: str = Field(alias="guidelineId")
    title: str
    source: str
    relevance_score: float = Field(alias="relevanceScore")

    model_config = ConfigDict(populate_by_name=True, by_alias=True)


class WebEvidenceItem(BaseModel):
    source: str
    title: str
    citation: str
    url: str
    evidence_level: str = Field(default="", alias="evidenceLevel")

    model_config = ConfigDict(populate_by_name=True, by_alias=True)


class AppealResponse(BaseModel):
    appeal_id: str = Field(alias="appealId")
    letter: str
    citations: list[Citation]
    rag_sources: list[RAGSourceItem] = Field(alias="ragSources")
    web_evidence: list[WebEvidenceItem] = Field(alias="webEvidence")
    parsed_clinical_data: str = Field(default="", alias="parsedClinicalData")
    safety_report: dict | None = Field(default=None, alias="safetyReport")
    clinical_sufficiency_report: dict | None = Field(default=None, alias="clinicalSufficiencyReport")

    model_config = ConfigDict(populate_by_name=True, by_alias=True)


class AppealListItem(BaseModel):
    id: str
    patient_name: str = Field(alias="patientName")
    denied_service: str = Field(alias="deniedService")
    insurance_company: str = Field(alias="insuranceCompany")
    status: str
    created_at: str = Field(alias="createdAt")
    cpt_codes: str = Field(alias="cptCodes")
    icd10_codes: str = Field(alias="icd10Codes")

    model_config = ConfigDict(populate_by_name=True, by_alias=True)


class AppealStats(BaseModel):
    total: int
    completed: int
    submitted: int
    approved: int
    denied: int


class AppealListResponse(BaseModel):
    appeals: list[AppealListItem]
    stats: AppealStats


class AppealDetail(BaseModel):
    id: str
    status: str
    patient_name: str = Field(alias="patientName")
    patient_dob: str = Field(alias="patientDOB")
    member_id: str = Field(alias="memberId")
    insurance_company: str = Field(alias="insuranceCompany")
    claim_number: str = Field(alias="claimNumber")
    denial_date: str = Field(alias="denialDate")
    denial_reason: str = Field(alias="denialReason")
    denied_service: str = Field(alias="deniedService")
    cpt_codes: str = Field(alias="cptCodes")
    icd10_codes: str = Field(alias="icd10Codes")
    physician_name: str = Field(alias="physicianName")
    physician_npi: str = Field(alias="physicianNPI")
    practice_name: str = Field(alias="practiceName")
    clinical_notes: str = Field(alias="clinicalNotes")
    generated_letter: str | None = Field(default=None, alias="generatedLetter")
    citations: list[dict] | None = None
    rag_sources: list[dict] | None = Field(default=None, alias="ragSources")
    safety_report: dict | None = Field(default=None, alias="safetyReport")
    created_at: str = Field(alias="createdAt")

    model_config = ConfigDict(populate_by_name=True, by_alias=True)

    @classmethod
    def from_orm_row(cls, row) -> "AppealDetail":
        safety_report = None
        if row.analysis_result:
            try:
                safety_report = json.loads(row.analysis_result).get("safetyReport")
            except (json.JSONDecodeError, TypeError, AttributeError):
                safety_report = None

        return cls(
            id=str(row.id),
            patientName=row.patient_name,
            patientDOB=row.patient_dob,
            memberId=row.member_id,
            insuranceCompany=row.insurance_company,
            claimNumber=row.claim_number,
            denialDate=row.denial_date,
            denialReason=row.denial_reason,
            deniedService=row.denied_service,
            cptCodes=row.cpt_codes,
            icd10Codes=row.icd10_codes,
            physicianName=row.physician_name,
            physicianNPI=row.physician_npi,
            practiceName=row.practice_name,
            clinicalNotes=row.clinical_notes,
            generatedLetter=row.generated_letter,
            citations=row.citations,
            ragSources=row.rag_sources,
            safetyReport=safety_report,
            createdAt=row.created_at.isoformat() if row.created_at else "",
            status=row.status,
        )
