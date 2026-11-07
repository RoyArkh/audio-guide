from fastapi import APIRouter, Depends
from fastapi.responses import JSONResponse
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.db import get_session

router = APIRouter(tags=["health"])

EXTENSION_VERSIONS_SQL = text(
    "SELECT extname, extversion FROM pg_extension WHERE extname IN ('postgis', 'vector')"
)


@router.get("/health")
def health(session: Session = Depends(get_session)):
    try:
        versions = dict(session.execute(EXTENSION_VERSIONS_SQL).all())
    except SQLAlchemyError as exc:
        return JSONResponse(
            status_code=503,
            content={"status": "error", "database": "unreachable", "detail": type(exc).__name__},
        )

    return {
        "status": "ok",
        "database": "ok",
        "postgis": versions.get("postgis"),
        "pgvector": versions.get("vector"),
    }
