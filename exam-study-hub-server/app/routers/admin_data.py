from collections import Counter, defaultdict
from fastapi import APIRouter, Depends, Query
from sqlalchemy import func
from sqlalchemy.orm import Session, selectinload

from app.core.deps import get_current_admin
from app.db.session import get_db
from app.models.catalog import (
    AdmissionPlan,
    AdmissionScore,
    Institution,
    Major,
    Province,
    ProvinceControlScore,
    Question,
    QuestionTopic,
)
from app.models.user import User
from app.schemas.admin_data import (
    AdminDataSummary,
    AdminInstitutionItem,
    AdminStat,
    CatalogCategoryItem,
    CatalogMajorItem,
    CatalogProvinceItem,
    CatalogResponse,
    ImportBatchItem,
    InstitutionListResponse,
    QuestionQualityResponse,
    QuestionSubjectQuality,
    ValidationIssue,
    ValidationSummary,
)

router = APIRouter(prefix="/api/admin/data", tags=["admin-data"])

EXPECTED_COUNTS = {
    "major": 66,
    "henan_institution": 39,
    "henan_score": 90,
    "henan_plan": 199,
    "henan_control": 26,
    "jiangsu_score": 171,
    "jiangsu_plan": 89,
    "zhejiang_control": 24,
}
LEGACY_MAJOR_CODES = ["business", "accounting", "law", "education", "computer", "chinese"]


def province_maps(db: Session) -> tuple[dict[int, str], dict[int, str]]:
    provinces = db.query(Province).all()
    return (
        {item.id: item.code for item in provinces},
        {item.id: item.name for item in provinces},
    )


def add_count_issue(issues: list[ValidationIssue], area: str, label: str, actual: int, expected: int):
    if actual != expected:
        issues.append(ValidationIssue(
            severity="error",
            area=area,
            message=f"{label}应为 {expected}，实际 {actual}",
        ))


def build_validation_summary(db: Session) -> ValidationSummary:
    issues: list[ValidationIssue] = []

    henan = db.query(Province).filter_by(code="henan").first()
    jiangsu = db.query(Province).filter_by(code="jiangsu").first()
    zhejiang = db.query(Province).filter_by(code="zhejiang").first()
    if henan is None:
        issues.append(ValidationIssue(severity="error", area="省份", message="缺少河南省份记录"))
    if jiangsu is None:
        issues.append(ValidationIssue(severity="error", area="省份", message="缺少江苏省份记录"))
    if zhejiang is None:
        issues.append(ValidationIssue(severity="error", area="省份", message="缺少浙江省份记录"))

    major_count = db.query(Major).count()
    add_count_issue(issues, "专业主数据", "专业主数据", major_count, EXPECTED_COUNTS["major"])
    legacy_count = db.query(Major).filter(Major.code.in_(LEGACY_MAJOR_CODES)).count()
    if legacy_count:
        issues.append(ValidationIssue(
            severity="error",
            area="专业主数据",
            message=f"仍存在旧专业 code {legacy_count} 个",
        ))
    software = db.query(Major).filter_by(code="ruanjian", name="软件工程").first()
    if software is None:
        issues.append(ValidationIssue(severity="error", area="专业主数据", message="缺少 软件工程 / ruanjian"))

    score_control_count = db.query(AdmissionScore).filter_by(line_type="省控线").count()
    if score_control_count:
        issues.append(ValidationIssue(
            severity="error",
            area="院校分数线",
            message=f"admission_scores 中仍有省控线 {score_control_count} 条",
        ))
    roundless_scores = db.query(AdmissionScore).filter(AdmissionScore.round.is_(None)).count()
    if roundless_scores:
        issues.append(ValidationIssue(
            severity="error",
            area="院校分数线",
            message=f"admission_scores 中仍有无批次旧记录 {roundless_scores} 条",
        ))

    if henan is not None:
        old_control = db.query(Institution).filter_by(
            province_id=henan.id,
            code="henan-control-line",
        ).first()
        if old_control is not None:
            issues.append(ValidationIssue(severity="error", area="河南数据", message="河南省控线仍作为院校存在"))
        add_count_issue(
            issues,
            "河南数据",
            "河南院校数",
            db.query(Institution).filter_by(province_id=henan.id).count(),
            EXPECTED_COUNTS["henan_institution"],
        )
        add_count_issue(
            issues,
            "河南数据",
            "河南院校科类分数",
            db.query(AdmissionScore).join(Institution).filter(Institution.province_id == henan.id).count(),
            EXPECTED_COUNTS["henan_score"],
        )
        add_count_issue(
            issues,
            "河南数据",
            "河南专业计划",
            db.query(AdmissionPlan).join(Institution).filter(Institution.province_id == henan.id).count(),
            EXPECTED_COUNTS["henan_plan"],
        )
        add_count_issue(
            issues,
            "河南数据",
            "河南省控线",
            db.query(ProvinceControlScore).filter_by(province_id=henan.id).count(),
            EXPECTED_COUNTS["henan_control"],
        )

    if jiangsu is not None:
        add_count_issue(
            issues,
            "江苏数据",
            "江苏院校科类分数",
            db.query(AdmissionScore).join(Institution).filter(Institution.province_id == jiangsu.id).count(),
            EXPECTED_COUNTS["jiangsu_score"],
        )
        add_count_issue(
            issues,
            "江苏数据",
            "江苏本科征求计划",
            db.query(AdmissionPlan).join(Institution).filter(Institution.province_id == jiangsu.id).count(),
            EXPECTED_COUNTS["jiangsu_plan"],
        )

    if zhejiang is not None:
        add_count_issue(
            issues,
            "浙江数据",
            "浙江省控线",
            db.query(ProvinceControlScore).filter_by(province_id=zhejiang.id).count(),
            EXPECTED_COUNTS["zhejiang_control"],
        )

    missing_city_count = db.query(Institution).filter(
        (Institution.city.is_(None)) | (Institution.city == "") | (Institution.city == "—")
    ).count()
    if missing_city_count:
        issues.append(ValidationIssue(
            severity="warning",
            area="院校基础信息",
            message=f"有 {missing_city_count} 所院校缺少所在地城市",
        ))

    known_major_names = {item.name for item in db.query(Major).all()}
    unmapped_plan_count = db.query(AdmissionPlan).filter(~AdmissionPlan.major_name.in_(known_major_names)).count()
    if unmapped_plan_count:
        issues.append(ValidationIssue(
            severity="warning",
            area="专业计划",
            message=f"有 {unmapped_plan_count} 条专业计划无法映射到专业主数据",
        ))

    return ValidationSummary(passed=not any(item.severity == "error" for item in issues), issues=issues)


def question_quality(db: Session) -> QuestionQualityResponse:
    topics = db.query(QuestionTopic).options(selectinload(QuestionTopic.questions)).order_by(
        QuestionTopic.subject,
        QuestionTopic.sort_order,
    ).all()
    issues: list[ValidationIssue] = []
    subject_stats: dict[str, dict[str, int]] = defaultdict(lambda: {"topics": 0, "questions": 0, "issues": 0})
    stem_counter = Counter()

    for topic in topics:
        stat = subject_stats[topic.subject]
        stat["topics"] += 1
        if not topic.questions:
            issues.append(ValidationIssue(
                severity="warning",
                area=f"{topic.subject} / {topic.name}",
                message="知识点没有题目",
            ))
            stat["issues"] += 1
        for question in topic.questions:
            stat["questions"] += 1
            stem = (question.stem or "").strip()
            if stem:
                stem_counter[stem] += 1
            if not stem:
                issues.append(ValidationIssue(severity="error", area=f"{topic.subject} / {topic.name}", message="存在空题干"))
                stat["issues"] += 1
            if not isinstance(question.options, list) or len(question.options) < 2:
                issues.append(ValidationIssue(
                    severity="error",
                    area=f"{topic.subject} / {topic.name}",
                    message=f"题目 {question.id} 选项不足",
                ))
                stat["issues"] += 1
            answer = (question.answer or "").strip().upper()
            answer_index = ord(answer[:1]) - ord("A") if answer else -1
            if answer_index < 0 or answer_index >= len(question.options or []):
                issues.append(ValidationIssue(
                    severity="error",
                    area=f"{topic.subject} / {topic.name}",
                    message=f"题目 {question.id} 答案超出选项范围",
                ))
                stat["issues"] += 1

    duplicate_count = sum(count - 1 for count in stem_counter.values() if count > 1)
    if duplicate_count:
        issues.append(ValidationIssue(
            severity="warning",
            area="题库去重",
            message=f"发现 {duplicate_count} 条重复题干",
        ))

    subjects = [
        QuestionSubjectQuality(
            subject=subject,
            topics_count=data["topics"],
            questions_count=data["questions"],
            issue_count=data["issues"],
        )
        for subject, data in sorted(subject_stats.items())
    ]
    return QuestionQualityResponse(subjects=subjects, issues=issues)


@router.get("/summary", response_model=AdminDataSummary)
def data_summary(
    _admin: User = Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    stats = [
        AdminStat(key="provinces", label="已接入省份", value=db.query(Province).count(), tone="blue"),
        AdminStat(key="majors", label="专业主数据", value=db.query(Major).count(), description="专升本常见专业", tone="green"),
        AdminStat(key="institutions", label="招生院校", value=db.query(Institution).count(), tone="blue"),
        AdminStat(key="scores", label="院校参考线", value=db.query(AdmissionScore).count(), tone="green"),
        AdminStat(key="plans", label="专业计划", value=db.query(AdmissionPlan).count(), tone="amber"),
        AdminStat(key="questions", label="题库题目", value=db.query(Question).count(), tone="neutral"),
    ]
    return AdminDataSummary(stats=stats, validation=build_validation_summary(db))


@router.get("/institutions", response_model=InstitutionListResponse)
def institutions(
    province: str | None = None,
    keyword: str | None = None,
    issue_only: bool = False,
    page: int = Query(1, ge=1),
    page_size: int = Query(30, ge=1, le=200),
    _admin: User = Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    province_by_id, province_name_by_id = province_maps(db)
    query = db.query(Institution).options(selectinload(Institution.scores), selectinload(Institution.plans))
    if province:
        query = query.join(Province).filter(Province.code == province)
    if keyword:
        pattern = f"%{keyword.strip()}%"
        query = query.filter((Institution.name.ilike(pattern)) | (Institution.code.ilike(pattern)))
    institutions = query.order_by(Institution.province_id, Institution.name).all()
    items: list[AdminInstitutionItem] = []
    for inst in institutions:
        scores = sorted(
            [score for score in inst.scores if score.score is not None],
            key=lambda item: (item.year, item.category_name),
            reverse=True,
        )
        latest_score = scores[0] if scores else None
        major_names = {plan.major_name for plan in inst.plans}
        issues: list[str] = []
        if not inst.city or inst.city == "—":
            issues.append("缺少城市")
        if not inst.scores:
            issues.append("缺少参考线")
        if inst.plans and not major_names:
            issues.append("专业计划缺少专业名")
        if latest_score and not latest_score.source:
            issues.append("参考线缺少来源")
        if not inst.plans:
            issues.append("无公开专业计划")
        if issue_only and not issues:
            continue
        if not issues:
            quality = "完整"
        elif len(issues) <= 2 and inst.scores:
            quality = "可参考"
        else:
            quality = "待补充"
        items.append(AdminInstitutionItem(
            id=inst.id,
            code=inst.code,
            name=inst.name,
            province=province_by_id.get(inst.province_id, ""),
            province_name=province_name_by_id.get(inst.province_id, ""),
            city=inst.city,
            scores_count=len(inst.scores),
            plans_count=len(inst.plans),
            plan_major_count=len(major_names),
            latest_score=latest_score.score if latest_score else None,
            latest_score_year=latest_score.year if latest_score else None,
            latest_line_type=latest_score.line_type if latest_score else None,
            latest_source=latest_score.source if latest_score else None,
            quality=quality,
            issues=issues,
        ))
    start = (page - 1) * page_size
    return InstitutionListResponse(total=len(items), items=items[start:start + page_size])


@router.get("/batches", response_model=list[ImportBatchItem])
def import_batches(
    _admin: User = Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    province_by_id, province_name_by_id = province_maps(db)
    batches: list[ImportBatchItem] = []

    score_rows = db.query(
        Institution.province_id,
        AdmissionScore.year,
        AdmissionScore.line_type,
        AdmissionScore.round,
        AdmissionScore.source,
        func.count(AdmissionScore.id),
        func.count(func.distinct(AdmissionScore.institution_id)),
    ).join(Institution).group_by(
        Institution.province_id,
        AdmissionScore.year,
        AdmissionScore.line_type,
        AdmissionScore.round,
        AdmissionScore.source,
    ).all()
    for province_id, year, line_type, round_name, source, records, institutions_count in score_rows:
        province_code = province_by_id.get(province_id, "")
        batches.append(ImportBatchItem(
            id=f"score-{province_code}-{year}-{line_type}-{round_name or ''}",
            data_type="院校参考线",
            province=province_code,
            province_name=province_name_by_id.get(province_id, ""),
            year=year,
            line_type=line_type,
            round=round_name,
            source=source,
            records_count=records,
            institutions_count=institutions_count,
        ))

    plan_rows = db.query(
        Institution.province_id,
        AdmissionPlan.year,
        AdmissionPlan.line_type,
        AdmissionPlan.round,
        AdmissionPlan.source,
        func.count(AdmissionPlan.id),
        func.count(func.distinct(AdmissionPlan.institution_id)),
        func.count(func.distinct(AdmissionPlan.major_name)),
    ).join(Institution).group_by(
        Institution.province_id,
        AdmissionPlan.year,
        AdmissionPlan.line_type,
        AdmissionPlan.round,
        AdmissionPlan.source,
    ).all()
    for province_id, year, line_type, round_name, source, records, institutions_count, majors_count in plan_rows:
        province_code = province_by_id.get(province_id, "")
        batches.append(ImportBatchItem(
            id=f"plan-{province_code}-{year}-{line_type}-{round_name or ''}",
            data_type="专业计划",
            province=province_code,
            province_name=province_name_by_id.get(province_id, ""),
            year=year,
            line_type=line_type,
            round=round_name,
            source=source,
            records_count=records,
            institutions_count=institutions_count,
            majors_count=majors_count,
        ))

    control_rows = db.query(
        ProvinceControlScore.province_id,
        ProvinceControlScore.year,
        ProvinceControlScore.line_type,
        ProvinceControlScore.round,
        ProvinceControlScore.source,
        func.count(ProvinceControlScore.id),
    ).group_by(
        ProvinceControlScore.province_id,
        ProvinceControlScore.year,
        ProvinceControlScore.line_type,
        ProvinceControlScore.round,
        ProvinceControlScore.source,
    ).all()
    for province_id, year, line_type, round_name, source, records in control_rows:
        province_code = province_by_id.get(province_id, "")
        batches.append(ImportBatchItem(
            id=f"control-{province_code}-{year}-{line_type}-{round_name or ''}",
            data_type="省控线",
            province=province_code,
            province_name=province_name_by_id.get(province_id, ""),
            year=year,
            line_type=line_type,
            round=round_name,
            source=source,
            records_count=records,
            institutions_count=0,
        ))

    return sorted(batches, key=lambda item: (item.year, item.province, item.data_type), reverse=True)


@router.get("/question-quality", response_model=QuestionQualityResponse)
def question_quality_report(
    _admin: User = Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    return question_quality(db)


@router.get("/catalog", response_model=CatalogResponse)
def catalog(
    _admin: User = Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    provinces: list[CatalogProvinceItem] = []
    for province in db.query(Province).order_by(Province.id).all():
        provinces.append(CatalogProvinceItem(
            code=province.code,
            name=province.name,
            note=province.note,
            institutions_count=db.query(Institution).filter_by(province_id=province.id).count(),
            scores_count=db.query(AdmissionScore).join(Institution).filter(Institution.province_id == province.id).count(),
            plans_count=db.query(AdmissionPlan).join(Institution).filter(Institution.province_id == province.id).count(),
            control_scores_count=db.query(ProvinceControlScore).filter_by(province_id=province.id).count(),
        ))

    majors = db.query(Major).options(selectinload(Major.subjects)).order_by(Major.category, Major.name).all()
    category_map: dict[str, set[str]] = defaultdict(set)
    for major in majors:
        for subject in major.subjects:
            category_map[major.category].add(subject.subject)
    categories = [
        CatalogCategoryItem(
            category=category,
            majors_count=sum(1 for major in majors if major.category == category),
            subjects=sorted(subjects),
        )
        for category, subjects in sorted(category_map.items())
    ]
    return CatalogResponse(
        provinces=provinces,
        categories=categories,
        majors=[
            CatalogMajorItem(
                code=major.code,
                name=major.name,
                category=major.category,
                subjects=[subject.subject for subject in sorted(major.subjects, key=lambda item: item.id)],
            )
            for major in majors
        ],
    )
