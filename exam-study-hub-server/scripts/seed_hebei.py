"""Transactional import of verified Hebei records; no changes to other provinces or majors."""
import json
from pathlib import Path

from app.db.session import SessionLocal
from app.models.catalog import AdmissionPlan, Institution, Province, ProvinceControlScore

DATA = Path(__file__).resolve().parent.parent / "scraped-data"
NOTE = "已收录2024—2025专升本计划、2023—2025分人群省控线；仅历史参考，未取得2026完整目录及院校实际录取线"
PLAN_FIELDS = ("major_name", "level", "category_code", "category_name", "plan_count", "study_form",
               "teaching_site", "tuition_amount", "tuition_unit", "tuition_raw", "enrollment_scope")
DETAIL_FIELDS = ("study_duration_raw", "minimum_study_duration_raw", "remarks", "category_name_raw",
                 "institution_code_raw", "applicant_group", "source_page")


def import_hebei(db, data_dir=DATA):
    def records(filename):
        rows = json.loads((data_dir / filename).read_text(encoding="utf-8"))
        if any(row["province"] != "hebei" for row in rows): raise ValueError("河北资料包含其他省份")
        return rows

    school_rows = records("hebei-institutions.json")
    plans = records("hebei-adult-programs.json")
    controls = records("hebei-adult-control-scores.json")
    keys = [(r["institution_code"], r["year"], r["major_code"], r["line_type"], r["round"]) for r in plans]
    if len(keys) != len(set(keys)): raise ValueError("河北专业记录重复")
    province = db.query(Province).filter_by(code="hebei").one_or_none()
    if province is None:
        province = Province(code="hebei", name="河北")
        db.add(province)
        db.flush()
    province.note = NOTE
    counts = {"institutions_added": 0, "plans_added": 0, "controls_added": 0}
    schools, details = {}, {}
    for record in school_rows:
        code = record["institution_code"]
        school = db.query(Institution).filter_by(province_id=province.id, code=code).one_or_none()
        if school is None:
            school = Institution(province_id=province.id, code=code)
            db.add(school)
            counts["institutions_added"] += 1
        school.name, school.city = record["institution_name"], record["city"]
        schools[code], details[code] = school, {}
    db.flush()
    for record in plans:
        school = schools[record["institution_code"]]
        expected_raw = next(r for r in school_rows if r["institution_code"] == school.code)["source_codes_by_year"].get(str(record["year"]))
        if record["institution_name"] != school.name or record["institution_code_raw"] != expected_raw:
            raise ValueError("跨年份院校身份不符")
        if record["level"] != "专升本" or record["line_type"] != "招生计划" or record["plan_count"] is None:
            raise ValueError("河北资料层次/计划口径不符")
        key = dict(institution_id=school.id, **{key: record[key] for key in ("year", "major_code", "line_type", "round")})
        plan = db.query(AdmissionPlan).filter_by(**key).one_or_none()
        if plan is None:
            plan = AdmissionPlan(**key)
            db.add(plan)
            counts["plans_added"] += 1
        for field in PLAN_FIELDS: setattr(plan, field, record.get(field))
        plan.source = record["source_url"]
        details[school.code][f"{plan.year}/{plan.round}/{plan.major_code}"] = {field: record.get(field) for field in DETAIL_FIELDS}
    latest_year = max(p["year"] for p in plans)
    for record in school_rows:
        school = schools[record["institution_code"]]
        school.supplemental_data = {**(school.supplemental_data or {}), "active_catalog_year": latest_year,
                                    "plan_details": details[school.code], "city_source_url": record["city_source_url"],
                                    "source_codes_by_year": record["source_codes_by_year"], "coverage_note": NOTE}
    for record in controls:
        if record["level"] != "专升本" or record["line_type"] != "省控线" or record["round"] not in ("统考生", "农民工考生"):
            raise ValueError("河北控制线层次/人群口径不符")
        key = dict(province_id=province.id, **{field: record[field] for field in ("year", "level", "category_name", "line_type", "round")})
        line = db.query(ProvinceControlScore).filter_by(**key).one_or_none()
        if line is None:
            line = ProvinceControlScore(**key)
            db.add(line)
            counts["controls_added"] += 1
        line.category_code, line.score, line.source = record["category_code"], record["score"], record["source_url"]
    db.flush()
    return counts


def run():
    with SessionLocal.begin() as db:
        counts = import_hebei(db)
    print("河北数据导入完成：" + json.dumps(counts, ensure_ascii=False))


if __name__ == "__main__":
    run()
