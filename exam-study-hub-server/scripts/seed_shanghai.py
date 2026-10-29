"""Transactional, repeatable Shanghai-only import. Run python -m scripts.seed_shanghai."""
import json
from pathlib import Path

from app.db.session import SessionLocal
from app.models.catalog import AdmissionPlan, Institution, Province, ProvinceControlScore

DATA = Path(__file__).resolve().parent.parent / "scraped-data"
NOTE = "已收录2026专升本专业目录、2025主批次及征求计划、2023—2025市控线；暂无院校实际录取线"
PLAN_FIELDS = ("major_name", "level", "category_code", "category_name", "plan_count", "study_form",
               "teaching_site", "tuition_amount", "tuition_unit", "tuition_raw", "enrollment_scope")
DETAIL_FIELDS = ("study_duration_raw", "minimum_study_duration_raw", "major_direction", "foreign_language",
                 "fee_basis", "remarks", "source_page", "teaching_site_codes")


def detail_key(year, round_name, major_code):
    return f"{year}/{round_name}/{major_code}"


def import_shanghai(db, data_dir=DATA):
    def records(name):
        data = json.loads((data_dir / name).read_text(encoding="utf-8"))
        if any(row["province"] != "shanghai" for row in data):
            raise ValueError("上海资料包含其他省份")
        return data

    school_records = records("shanghai-institutions.json")
    plans = records("shanghai-adult-programs.json")
    controls = records("shanghai-adult-control-scores.json")
    province = db.query(Province).filter_by(code="shanghai").one_or_none()
    if province is None:
        province = Province(code="shanghai", name="上海")
        db.add(province)
        db.flush()
    province.note = NOTE
    counts = {"institutions_added": 0, "plans_added": 0, "controls_added": 0}
    schools = {}
    for record in school_records:
        school = db.query(Institution).filter_by(province_id=province.id, code=record["institution_code"]).one_or_none()
        if school is None:
            school = Institution(province_id=province.id, code=record["institution_code"])
            db.add(school)
            counts["institutions_added"] += 1
        school.name, school.city = record["institution_name"], record["city"]
        schools[school.code] = school
    db.flush()
    details = {code: {} for code in schools}
    active_year = max(p["year"] for p in plans if p["line_type"] == "招生专业目录")
    for record in plans:
        if record["level"] != "专升本" or record["line_type"] not in ("招生计划", "征求计划", "招生专业目录"):
            raise ValueError("不支持的招生目录口径")
        if record["year"] == active_year and record["plan_count"] is not None:
            raise ValueError("当前目录不能填充未公布的计划数")
        school = schools[record["institution_code"]]
        key = dict(institution_id=school.id, year=record["year"], major_code=record["major_code"],
                   line_type=record["line_type"], round=record["round"])
        row = db.query(AdmissionPlan).filter_by(**key).one_or_none()
        if row is None:
            row = AdmissionPlan(**key)
            db.add(row)
            counts["plans_added"] += 1
        for field in PLAN_FIELDS:
            setattr(row, field, record.get(field))
        row.source = record["source_url"]
        details[school.code][detail_key(row.year, row.round, row.major_code)] = {field: record.get(field) for field in DETAIL_FIELDS}
    for code, school in schools.items():
        school.supplemental_data = {**(school.supplemental_data or {}), "active_catalog_year": active_year, "plan_details": details[code]}
    for record in controls:
        if record["line_type"] != "省控线" or record["level"] != "专升本":
            raise ValueError("控制线口径错误")
        key = dict(province_id=province.id, **{field: record[field] for field in ("year", "level", "category_name", "line_type", "round")})
        row = db.query(ProvinceControlScore).filter_by(**key).one_or_none()
        if row is None:
            row = ProvinceControlScore(**key)
            db.add(row)
            counts["controls_added"] += 1
        row.category_code, row.score, row.source = record["category_code"], record["score"], record["source_url"]
    db.flush()
    return counts


def run():
    with SessionLocal.begin() as db:
        counts = import_shanghai(db)
    print("上海数据导入完成：" + json.dumps(counts, ensure_ascii=False))


if __name__ == "__main__":
    run()
