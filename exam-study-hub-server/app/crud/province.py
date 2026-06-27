from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.catalog import Province


def list_provinces(db: Session) -> list[Province]:
    return list(db.scalars(select(Province).order_by(Province.id)).all())


def get_province_by_code(db: Session, code: str) -> Province | None:
    return db.scalars(select(Province).where(Province.code == code)).first()
