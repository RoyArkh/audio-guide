from datetime import datetime

from geoalchemy2 import Geography, WKBElement
from sqlalchemy import DateTime, String, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column

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
