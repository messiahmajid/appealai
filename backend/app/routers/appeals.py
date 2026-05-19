import asyncio
import json

import structlog
from fastapi import APIRouter, Depends
from fastapi.responses import JSONResponse, StreamingResponse
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.db.tables import Appeal
from app.models.appeals import (
    AppealCreate,
    AppealDetail,
    AppealListItem,
    AppealListResponse,
    AppealStats,
)
from app.services.appeal_generator import ClinicalNoteInsufficientError, generate_appeal
from app.services.docx_export import generate_docx

logger = structlog.get_logger()
router = APIRouter()


@router.post("/api/generate-appeal")
async def create_appeal(body: AppealCreate, db: AsyncSession = Depends(get_db)):
    try:
        result = await generate_appeal(body, db)
        return result.model_dump(by_alias=True)
    except ClinicalNoteInsufficientError as e:
        return JSONResponse(
            {
                "error": e.report["summary"],
                "sufficiencyReport": e.report,
            },
            status_code=422,
        )
    except RuntimeError as e:
        logger.error("appeal_generation_error", error=str(e))
        return JSONResponse({"error": str(e)}, status_code=500)
    except Exception as e:
        logger.error("appeal_generation_error", error=str(e))
        return JSONResponse({"error": "Failed to generate appeal letter"}, status_code=500)


@router.post("/api/generate-appeal/stream")
async def create_appeal_stream(body: AppealCreate, db: AsyncSession = Depends(get_db)):
    async def event_stream():
        queue: asyncio.Queue[dict | None] = asyncio.Queue()

        async def progress(event: dict):
            await queue.put(event)

        async def run_generation():
            try:
                result = await generate_appeal(body, db, progress=progress)
                await queue.put(
                    {
                        "stage": "complete",
                        "message": "Appeal letter ready.",
                        "data": result.model_dump(by_alias=True),
                    }
                )
            except ClinicalNoteInsufficientError as e:
                await queue.put(
                    {
                        "stage": "error",
                        "message": e.report["summary"],
                        "data": {"sufficiencyReport": e.report},
                    }
                )
            except RuntimeError as e:
                logger.error("appeal_stream_generation_error", error=str(e))
                await queue.put({"stage": "error", "message": str(e), "data": {}})
            except Exception as e:
                logger.error("appeal_stream_generation_error", error=str(e))
                await queue.put({"stage": "error", "message": "Failed to generate appeal letter", "data": {}})
            finally:
                await queue.put(None)

        task = asyncio.create_task(run_generation())
        try:
            while True:
                event = await queue.get()
                if event is None:
                    break
                yield f"event: {event['stage']}\ndata: {json.dumps(event)}\n\n"
        finally:
            if not task.done():
                task.cancel()

    return StreamingResponse(
        event_stream(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )


@router.get("/api/appeals/{appeal_id}")
async def get_appeal(appeal_id: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Appeal).where(Appeal.id == appeal_id))
    appeal = result.scalar_one_or_none()
    if not appeal:
        return JSONResponse({"error": "Appeal not found"}, status_code=404)

    return AppealDetail.from_orm_row(appeal).model_dump(by_alias=True)


@router.get("/api/appeals/{appeal_id}/download")
async def download_appeal(appeal_id: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Appeal).where(Appeal.id == appeal_id))
    appeal = result.scalar_one_or_none()
    if not appeal or not appeal.generated_letter:
        return JSONResponse({"error": "Appeal not found"}, status_code=404)

    buf = generate_docx(appeal.generated_letter, appeal.patient_name or "")
    filename = f"appeal-letter-{(appeal.patient_name or 'patient').replace(' ', '-').lower()}.docx"
    return StreamingResponse(
        buf,
        media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


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
