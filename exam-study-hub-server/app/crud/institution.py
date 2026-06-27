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

# 江苏成人高考公办收费标准（苏价费〔2007〕271号），按专业类别，单位 元/年。
# 注：民办/独立学院实际收费偏高，此处为公办省定标准，民办待逐校核实。
TUITION_BY_CATEGORY = {
    "经济管理类": 2200,
    "法学类": 2200,
    "文史中医类": 2200,
    "教育学类": 2200,
    "理工类": 2400,
}
DEFAULT_DURATION = "2.5 年"

# 民办/独立学院：不套用公办省定标准，使用院校招生简章公布的学费。
PRIVATE_INSTITUTIONS = {"无锡太湖学院", "南通理工学院"}

# 民办院校学费标准（来自院校招生简章），按专业类别，单位 元/年。
# 表中：文史/经管/法学 2000、理工 2200、艺术 3200、医学 2500；教育学类按非理工类归入 2000。
PRIVATE_TUITION_BY_CATEGORY = {
    "经济管理类": 2000,
    "法学类": 2000,
    "文史中医类": 2000,
    "教育学类": 2000,
    "理工类": 2200,
}


def tuition_for(institution_name: str, category: str | None) -> int | None:
    """根据院校性质(公办/民办)和专业类别返回学费(元/年)。"""
    if category is None:
        return None
    if institution_name in PRIVATE_INSTITUTIONS:
        return PRIVATE_TUITION_BY_CATEGORY.get(category)
    return TUITION_BY_CATEGORY.get(category)


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
