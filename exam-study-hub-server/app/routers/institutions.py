# 招生院校接口。
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.core.deps import get_current_user
from app.crud import institution as crud_inst
from app.crud.institution import KELEI_TO_CATEGORY, DEFAULT_DURATION
from app.schemas.institution import InstitutionRead, PlanRead, ScoreRead, SourceRead

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
    _user=Depends(get_current_user),
):
    """按省份(可选)、专业 code(可选)查询院校。
    有专业计划的省份按真实专业匹配；没有专业计划的省份按科类兜底。"""
    province_map = crud_inst.province_code_by_id(db)
    cat_to_codes = crud_inst.majors_by_category(db)
    code_by_major_name = crud_inst.major_code_by_name(db)

    results = []
    for inst in crud_inst.list_institutions(db, province_code=province):
        province_code = province_map.get(inst.province_id, "")
        if inst.plans:
            # 有公开专业计划：只认真实专业名称能匹配到本系统专业 code 的专业。
            offered = sorted({
                code_by_major_name[plan.major_name]
                for plan in inst.plans
                if plan.major_name in code_by_major_name
            })
            major_match = "exact"
        else:
            # 没有公开专业计划：退回原先的科类推导。
            categories = {KELEI_TO_CATEGORY.get(s.category_name) for s in inst.scores}
            categories.discard(None)
            offered = sorted({code for cat in categories for code in cat_to_codes.get(cat, [])})
            major_match = "category"

        scores = [
            ScoreRead(
                year=s.year,
                category_name=s.category_name,
                major_category=KELEI_TO_CATEGORY.get(s.category_name),
                score=s.score,
                tuition=crud_inst.tuition_for(inst.name, KELEI_TO_CATEGORY.get(s.category_name))
                if province_code == "jiangsu"
                else None,
                line_type=s.line_type,
                round=s.round,
            )
            for s in sorted(inst.scores, key=lambda item: (item.year, item.category_name))
        ]
        plans = [
            PlanRead(
                year=p.year,
                major_code=p.major_code,
                major_name=p.major_name,
                category_name=p.category_name,
                plan_count=p.plan_count,
                line_type=p.line_type,
                round=p.round,
            )
            for p in sorted(inst.plans, key=lambda item: (item.year, item.major_code))
        ]
        # 来源与可信度：由投档线数据派生（年度、官方链接、线型）。
        source_item = next(
            (s for s in sorted(inst.scores, key=lambda item: item.year, reverse=True) if s.source),
            None,
        )
        if source_item is None:
            source_item = next(
                (p for p in sorted(inst.plans, key=lambda item: item.year, reverse=True) if p.source),
                None,
            )
        if source_item is not None:
            source = SourceRead(
                provider=PROVIDER_BY_PROVINCE.get(province_code),
                year=source_item.year,
                line_type=source_item.line_type,
                url=source_item.source,
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
            major_match=major_match,
            plans=plans,
            scores=scores,
            source=source,
        ))

    # 若指定了专业，只返回开设该专业的院校
    if major:
        results = [r for r in results if major in r.majors]
    return results
