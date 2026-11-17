# Copyright (c) 2026 Muhamad Rizal Hidayat. All Rights Reserved.
# Licensed strictly for technical evaluation purposes only.
# Commercial use, redistribution, or production deployment without written consent is prohibited.

from fastapi import Depends, FastAPI, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from app.config import Settings, get_settings
from app.schemas import PostRequest, PostResponse
from app.services.posting_service import PostingService

app = FastAPI(
    title="Automated Multi-Platform Posting System",
    description="REST API to validate and publish short CTA messages across multiple third-party platforms concurrently.",
    version="1.0.0",
)


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError) -> JSONResponse:
    errors = []
    for err in exc.errors():
        field = ".".join(str(loc) for loc in err.get("loc", []) if loc != "body")
        msg = err.get("msg", "Invalid value").replace("Value error, ", "")
        errors.append({"field": field or "body", "message": msg})

    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            "success": False,
            "error": "Validation failed",
            "details": errors,
        },
    )


def get_posting_service(settings: Settings = Depends(get_settings)) -> PostingService:
    return PostingService(settings=settings)


@app.get("/health", tags=["System"])
async def health_check() -> dict[str, str]:
    return {"status": "ok"}


@app.post(
    "/posting",
    response_model=PostResponse,
    status_code=status.HTTP_200_OK,
    tags=["Posting"],
    summary="Publish a short message with 1 CTA link to all integrated platforms",
)
async def create_post(
    payload: PostRequest,
    service: PostingService = Depends(get_posting_service),
) -> PostResponse:
    return await service.publish_all(payload)