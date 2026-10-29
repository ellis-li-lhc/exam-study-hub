"""Import reviewed Guangdong supplements without changing other provinces or major data.

Run after ``alembic upgrade head``: ``python -m scripts.seed_guangdong_supplements``.
The complete import is transactional and can be repeated safely.
"""
import json
from pathlib import Path

from app.db.session import SessionLocal
from app.models.catalog import AdmissionPlan, AdmissionScore, Institution, Province, ProvinceControlScore

DATA_DIR = Path(__file__).resolve().parent.parent / "scraped-data"


def import_guangdong_supplements(db, data_dir=DATA_DIR):
    province = db.query(Province).filter_by(code="guangdong").one_or_none()
    if province is None:
        raise ValueError("请先通过 scripts.seed 导入广东基础院校和专业计划")
    institutions = {i.code: i for i in db.query(Institution).filter_by(province_id=province.id)}
    counts = {"scores_added": 0, "controls_added": 0, "plans_added": 0, "institutions_updated": 0}

    def records(filename):
        return json.loads((data_dir / filename).read_text(encoding="utf-8"))

    def institution(record):
        if record["province"] != "guangdong" or record["institution_code"] not in institutions:
            raise ValueError(f"补充资料不在已有广东院校范围：{record['institution_code']}")
        return institutions[record["institution_code"]]

    for record in records("guangdong-adult-scores-history.json"):
        school = institution(record)
        key = dict(institution_id=school.id, year=record["year"], category_code=record["category_code"],
                   line_type=record["line_type"], round=record["round"])
        row = db.query(AdmissionScore).filter_by(**key).one_or_none()
        if row is None:
            row = AdmissionScore(**key)
            db.add(row)
            counts["scores_added"] += 1
        row.category_name = record["category_name"]
        row.score = record["score"]
        row.source = record["source_url"]

    for record in records("guangdong-adult-control-scores-history.json"):
        if record["province"] != "guangdong":
            raise ValueError("省控线省份不一致")
        key = dict(province_id=province.id, year=record["year"], level=record["level"],
                   category_name=record["category_name"], line_type=record["line_type"], round=record["round"])
        row = db.query(ProvinceControlScore).filter_by(**key).one_or_none()
        if row is None:
            row = ProvinceControlScore(**key)
            db.add(row)
            counts["controls_added"] += 1
        row.category_code = record["category_code"]
        row.score = record["score"]
        row.source = record["source_url"]

    for record in records("guangdong-adult-collection-plan-2025.json"):
        school = institution(record)
        if record["round"] != "征集志愿" or record.get("applies_to_main_batch") is not False:
            raise ValueError("征集志愿资料缺少独立批次标识")
        if record.get("tuition_unit") not in (None, "total", "per_academic_year"):
            raise ValueError("未知学费计费口径")
        main_plan = db.query(AdmissionPlan).filter_by(
            institution_id=school.id, year=record["year"], major_name=record["major_name"],
            category_code=record["category_code"], round="第一批专科起点本科",
        ).one_or_none()
        if main_plan is None:
            raise ValueError(f"征集资料无法匹配已有主批次专业：{school.code}/{record['major_name']}")
        key = dict(institution_id=school.id, year=record["year"], major_code=record["major_code"],
                   line_type=record["line_type"], round=record["round"])
        row = db.query(AdmissionPlan).filter_by(**key).one_or_none()
        if row is None:
            row = AdmissionPlan(**key)
            db.add(row)
            counts["plans_added"] += 1
        for field in ("major_name", "level", "category_code", "category_name", "plan_count",
                      "study_form", "teaching_site", "tuition_amount", "tuition_unit", "tuition_raw", "enrollment_scope"):
            setattr(row, field, record.get(field))
        row.source = record["source_url"]

    for profile in records("guangdong-institution-supplements-2025.json"):
        school = institution(profile)
        data = {
            "documents": profile["documents"],
            "facts": [fact for fact in profile["facts"] if fact.get("review_status") == "verified_text"],
        }
        if school.supplemental_data != data:
            school.supplemental_data = data
            counts["institutions_updated"] += 1
    province.note = "已收录2023—2025投档线、省控线及2025专业计划、征集明细和院校补充资料"
    db.flush()
    return counts


def run():
    with SessionLocal.begin() as db:
        counts = import_guangdong_supplements(db)
    print("广东补充资料导入完成：" + json.dumps(counts, ensure_ascii=False))


if __name__ == "__main__":
    run()
