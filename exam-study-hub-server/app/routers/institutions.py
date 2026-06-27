# 招生院校接口。
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.crud import institution as crud_inst
from app.crud.institution import KELEI_TO_CATEGORY, DEFAULT_DURATION
from app.schemas.institution import InstitutionRead, ScoreRead, SourceRead

router = APIRouter(prefix="/api/institutions", tags=["institutions"])

# 各省投档线数据的来源机构。
PROVIDER_BY_PROVINCE = {
    "jiangsu": "江苏省教育考试院",
    "henan": "河南省教育考试院",
}


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
                tuition=crud_inst.tuition_for(inst.name, KELEI_TO_CATEGORY.get(s.category_name)),
            )
            for s in inst.scores
        ]
        # 来源与可信度：由投档线数据派生（年度、官方链接、线型）。
        province_code = province_map.get(inst.province_id, "")
        if inst.scores:
            years = [s.year for s in inst.scores]
            source_url = next((s.source for s in inst.scores if s.source), None)
            source = SourceRead(
                provider=PROVIDER_BY_PROVINCE.get(province_code),
                year=max(years),
                line_type=inst.scores[0].line_type,
                url=source_url,
                confidence="verified",
            )
        else:
            source = SourceRead(confidence="none")
        results.append(InstitutionRead(
            code=inst.code,
            name=inst.name,
            province=province_code,
            city=inst.city,
            duration=inst.duration or DEFAULT_DURATION,
            tuition=inst.tuition,
            teaching_site=inst.teaching_site,
            degree=inst.degree,
            majors=offered,
            scores=scores,
            source=source,
        ))

    # 若指定了专业，只返回开设该专业的院校
    if major:
        results = [r for r in results if major in r.majors]
    return results
