from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.models.catalog import Institution, Province, Major

# 专业类别(majors.category) → 考试院科类名(admission_scores.category_name)
CATEGORY_TO_KELEI = {
    "经济管理类": ["专升本经管类"],
    "法学类": ["专升本法学类"],
    "理工类": ["专升本理工类"],
    "教育学类": ["专升本教育学类", "专升本教育学类（体育）"],
    "文史中医类": ["专升本文史类", "专升本文史类（中医）"],
}
# 反向：科类名 → 专业类别
KELEI_TO_CATEGORY = {k: cat for cat, keleis in CATEGORY_TO_KELEI.items() for k in keleis}


def list_institutions(db: Session, province_code: str | None = None) -> list[Institution]:
    stmt = select(Institution).options(selectinload(Institution.scores)).order_by(Institution.id)
    if province_code:
        stmt = stmt.join(Province, Institution.province_id == Province.id).where(Province.code == province_code)
    return list(db.scalars(stmt).all())


def majors_by_category(db: Session) -> dict[str, list[str]]:
    """{专业类别: [专业code, ...]}，用于推导院校开设哪些专业。"""
    result: dict[str, list[str]] = {}
    for major in db.scalars(select(Major)).all():
        result.setdefault(major.category, []).append(major.code)
    return result


def province_code_by_id(db: Session) -> dict[int, str]:
    return {p.id: p.code for p in db.scalars(select(Province)).all()}
