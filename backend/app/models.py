import uuid
from datetime import datetime
from enum import StrEnum

from geoalchemy2 import Geography, WKBElement
from sqlalchemy import DateTime, ForeignKey, String, UniqueConstraint, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db import Base


class Place(Base):
    __tablename__ = "places"
    __table_args__ = (UniqueConstraint("wiki_lang", "wikipedia_page_id"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str]
    description: Mapped[str | None]
    wiki_lang: Mapped[str] = mapped_column(String(10))
    wikipedia_page_id: Mapped[int]
    wikidata_id: Mapped[str | None] = mapped_column(index=True)
    sitelinks: Mapped[int]
    geom: Mapped[WKBElement] = mapped_column(Geography(geometry_type="POINT", srid=4326))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class Episode(Base):
    """A finished story, kept so it can be served again later (caching, M7)."""

    __tablename__ = "episodes"

    id: Mapped[int] = mapped_column(primary_key=True)
    place_id: Mapped[int] = mapped_column(ForeignKey("places.id"), index=True)
    length: Mapped[str] = mapped_column(String(20))
    mood: Mapped[str] = mapped_column(String(30))
    language: Mapped[str] = mapped_column(String(10))
    script_text: Mapped[str]
    facts: Mapped[list[str]] = mapped_column(JSONB)
    sources: Mapped[list[dict]] = mapped_column(JSONB)
    audio_key: Mapped[str]
    duration_seconds: Mapped[float]
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    place: Mapped[Place] = relationship()


class JobStatus(StrEnum):
    PENDING = "pending"
    FINDING_PLACE = "finding_place"
    RESEARCHING = "researching"
    WRITING = "writing"
    GENERATING_AUDIO = "generating_audio"
    DONE = "done"
    FAILED = "failed"


class Job(Base):
    """One request for a story, and its progress."""

    __tablename__ = "jobs"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    lat: Mapped[float]
    lng: Mapped[float]
    length: Mapped[str] = mapped_column(String(20))
    mood: Mapped[str] = mapped_column(String(30))
    status: Mapped[str] = mapped_column(String(30), index=True)
    error: Mapped[str | None]
    place_id: Mapped[int | None] = mapped_column(ForeignKey("places.id"))
    distance_m: Mapped[float | None]
    episode_id: Mapped[int | None] = mapped_column(ForeignKey("episodes.id"))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(),
    )

    place: Mapped[Place | None] = relationship()
    episode: Mapped[Episode | None] = relationship()
