# CRUD = 增删改查。这一层只负责“怎么读写数据库”，不关心 HTTP。
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.catalog import Major, MajorSubject
from app.schemas.major import MajorCreate


def list_majors(db: Session) -> list[Major]:
    """查询所有专业。"""
    return list(db.scalars(select(Major).order_by(Major.id)).all())


def get_major_by_code(db: Session, code: str) -> Major | None:
    """按专业代码查单个专业。"""
    return db.scalars(select(Major).where(Major.code == code)).first()


def create_major(db: Session, data: MajorCreate) -> Major:
    """新建专业，并写入它的统考科目。"""
    major = Major(code=data.code, name=data.name, category=data.category)
    major.subjects = [MajorSubject(subject=s) for s in data.subjects]
    db.add(major)
    db.commit()
    db.refresh(major)
    return major
