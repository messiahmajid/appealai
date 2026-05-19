from contextlib import asynccontextmanager
from uuid import uuid4

import structlog
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import ValidationError

from app.config import settings
from app.logging_config import setup_logging
from app.routers import appeals, codes, documents, verification

setup_logging(settings.log_level)
logger = structlog.get_logger()


@asynccontextmanager
async def lifespan(app: FastAPI):
    import asyncio
    logger.info("app_startup")
    from app.services.rag import initialize_rag
    asyncio.create_task(initialize_rag())
    yield
    logger.info("app_shutdown")


app = FastAPI(title="AppealAI", version="0.1.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.middleware("http")
async def logging_middleware(request: Request, call_next):
    request_id = str(uuid4())
    structlog.contextvars.bind_contextvars(request_id=request_id, path=request.url.path)
    logger.info("request_started", method=request.method)
    response = await call_next(request)
    logger.info("request_completed", status_code=response.status_code)
    structlog.contextvars.unbind_contextvars("request_id", "path")
    return response


@app.exception_handler(ValidationError)
async def validation_error_handler(request: Request, exc: ValidationError):
    logger.warning("validation_error", errors=str(exc.errors()))
    return JSONResponse({"error": "Validation error", "details": exc.errors()}, status_code=422)


app.include_router(appeals.router)
app.include_router(codes.router)
app.include_router(documents.router)
app.include_router(verification.router)


@app.get("/health")
async def health():
    return {"status": "ok"}
