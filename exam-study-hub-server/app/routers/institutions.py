# 招生院校接口。
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.crud import institution as crud_inst
from app.crud.institution import KELEI_TO_CATEGORY
from app.schemas.institution import InstitutionRead, ScoreRead

router = APIRouter(prefix="/api/institutions", tags=["institutions"])


@router.get("", response_model=list[InstitutionRead])
def read_institutions(
    province: str | None = None,
    major: str | None = None,
    db: Session = Depends(get_db),
):
    """按省份(可选)、专业 code(可选)查询院校。
    院校开设哪些专业 = 它投档的科类对应的专业类别下的所有专业。"""
    province_map = crud_inst.province_code_by_id(db)
    cat_to_codes = crud_inst.majors_by_category(db)

    results = []
    for inst in crud_inst.list_institutions(db, province_code=province):
        # 该院校投档的所有科类 → 对应的专业类别集合
        categories = {KELEI_TO_CATEGORY.get(s.category_name) for s in inst.scores}
        categories.discard(None)
        # 推导该院校开设的专业 code
        offered = sorted({code for cat in categories for code in cat_to_codes.get(cat, [])})

        scores = [
            ScoreRead(
                year=s.year,
                category_name=s.category_name,
                major_category=KELEI_TO_CATEGORY.get(s.category_name),
                score=s.score,
            )
            for s in inst.scores
        ]
        results.append(InstitutionRead(
            code=inst.code,
            name=inst.name,
            province=province_map.get(inst.province_id, ""),
            city=inst.city,
            duration=inst.duration,
            tuition=inst.tuition,
            teaching_site=inst.teaching_site,
            degree=inst.degree,
            majors=offered,
            scores=scores,
        ))

    # 若指定了专业，只返回开设该专业的院校
    if major:
        results = [r for r in results if major in r.majors]
    return results
