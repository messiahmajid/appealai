import uuid
from datetime import datetime, timezone

from sqlalchemy import Column, DateTime, Index, String, Text, text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    pass


class Appeal(Base):
    __tablename__ = "appeals"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    status = Column(String(20), nullable=False, default="draft")
    created_at = Column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    patient_name = Column(String(255), nullable=False, default="Unknown")
    patient_dob = Column(String(20), nullable=False, default="")
    member_id = Column(String(100), nullable=False, default="")

    insurance_company = Column(String(255), nullable=False, default="")
    claim_number = Column(String(100), nullable=False, default="")
    denial_date = Column(String(20), nullable=False, default="")
    denial_reason = Column(Text, nullable=False)
    denied_service = Column(Text, nullable=False)
    cpt_codes = Column(String(255), nullable=False, default="")
    icd10_codes = Column(String(255), nullable=False, default="")

    physician_name = Column(String(255), nullable=False, default="")
    physician_npi = Column(String(20), nullable=False, default="")
    practice_name = Column(String(255), nullable=False, default="")

    clinical_notes = Column(Text, nullable=False)
    parsed_clinical_data = Column(Text, nullable=True)

    generated_letter = Column(Text, nullable=True)
    citations = Column(JSONB, nullable=True)
    rag_sources = Column(JSONB, nullable=True)
    analysis_result = Column(Text, nullable=True)

    __table_args__ = (
        Index("idx_appeals_created_at", created_at.desc()),
        Index("idx_appeals_status", status),
    )
