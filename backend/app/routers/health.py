from fastapi import APIRouter, Depends
from fastapi.responses import JSONResponse
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.db import get_session

router = APIRouter(tags=["health"])


@router.get("/health")
def health(session: Session = Depends(get_session)):
    """Liveness + database check. Returns 503 if Postgres can't be reached."""
    try:
        versions = dict(
            session.execute(
                text("SELECT extname, extversion FROM pg_extension WHERE extname IN ('postgis', 'vector')")
            ).all()
        )
    except SQLAlchemyError as exc:
        return JSONResponse(
            status_code=503,
            content={"status": "error", "database": "unreachable", "detail": type(exc).__name__},
        )

    return {
        "status": "ok",
        "database": "ok",
        # None here means the extension isn't enabled yet (run `alembic upgrade head`).
        "postgis": versions.get("postgis"),
        "pgvector": versions.get("vector"),
    }
