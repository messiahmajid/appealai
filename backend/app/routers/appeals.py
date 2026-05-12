import structlog
from fastapi import APIRouter, Depends
from fastapi.responses import JSONResponse
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.db.tables import Appeal
from app.models.appeals import AppealCreate, AppealListResponse, AppealListItem, AppealStats
from app.services.appeal_generator import generate_appeal

logger = structlog.get_logger()
router = APIRouter()


@router.post("/api/generate-appeal")
async def create_appeal(body: AppealCreate, db: AsyncSession = Depends(get_db)):
    try:
        result = await generate_appeal(body, db)
        return result.model_dump(by_alias=True)
    except RuntimeError as e:
        logger.error("appeal_generation_error", error=str(e))
        return JSONResponse({"error": str(e)}, status_code=500)
    except Exception as e:
        logger.error("appeal_generation_error", error=str(e))
        return JSONResponse({"error": "Failed to generate appeal letter"}, status_code=500)


@router.get("/api/appeals")
async def list_appeals(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Appeal).order_by(Appeal.created_at.desc()))
    appeals = result.scalars().all()

    appeal_items = [
        AppealListItem(
            id=str(a.id),
            patientName=a.patient_name,
            deniedService=a.denied_service,
            insuranceCompany=a.insurance_company,
            status=a.status,
            createdAt=a.created_at.isoformat() if a.created_at else "",
            cptCodes=a.cpt_codes,
            icd10Codes=a.icd10_codes,
        )
        for a in appeals
    ]

    # Compute stats
    stats_result = await db.execute(
        select(Appeal.status, func.count(Appeal.id)).group_by(Appeal.status)
    )
    status_counts = {row[0]: row[1] for row in stats_result.all()}

    stats = AppealStats(
        total=sum(status_counts.values()),
        completed=status_counts.get("completed", 0),
        submitted=status_counts.get("submitted", 0),
        approved=status_counts.get("approved", 0),
        denied=status_counts.get("denied", 0),
    )

    return AppealListResponse(appeals=appeal_items, stats=stats).model_dump(by_alias=True)
