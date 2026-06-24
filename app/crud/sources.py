from sqlalchemy.orm import Session
from app.db.models.source import Source
from app.schemas.source import SourceCreate


def get_sources(db: Session) -> list[Source]:
    return db.query(Source).order_by(Source.name).all()


def get_source(db: Session, source_id: int) -> Source | None:
    return db.query(Source).filter(Source.id == source_id).first()


def get_source_by_name(db: Session, name: str) -> Source | None:
    return db.query(Source).filter(Source.name == name).first()


def create_source(db: Session, source: SourceCreate) -> Source:
    db_source = Source(**source.model_dump())
    db.add(db_source)
    db.commit()
    db.refresh(db_source)
    return db_source


def get_or_create_source(db: Session, source: SourceCreate) -> Source:
    existing = get_source_by_name(db, source.name)
    if existing:
        return existing
    return create_source(db, source)
