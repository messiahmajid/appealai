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


class AppealResponse(BaseModel):
    appeal_id: str = Field(alias="appealId")
    letter: str
    citations: list[Citation]
    rag_sources: list[RAGSourceItem] = Field(alias="ragSources")
    web_evidence: list[WebEvidenceItem] = Field(alias="webEvidence")
    parsed_clinical_data: str = Field(default="", alias="parsedClinicalData")

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
