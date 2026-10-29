"""Atomic, repeatable import restricted to Shandong adult admission data."""
import json
from pathlib import Path

from app.db.session import SessionLocal
from app.models.catalog import AdmissionPlan, Institution, Province, ProvinceControlScore

DATA = Path(__file__).resolve().parent.parent / "scraped-data"
NOTE = "已收录2026及2025专升本目录、2025两次征集计划、2023—2025省控线；暂无院校实际录取线"
PLAN_FIELDS = ("major_name", "level", "category_code", "category_name", "plan_count", "study_form",
               "teaching_site", "tuition_amount", "tuition_unit", "tuition_raw", "enrollment_scope")
DETAIL_FIELDS = ("study_duration_raw", "minimum_study_duration_raw", "foreign_language", "remarks",
                 "national_major_code", "major_code_raw", "category_name_raw", "source_sheet", "source_row")


def import_shandong(db, data_dir=DATA):
    def records(filename):
        values = json.loads((data_dir / filename).read_text(encoding="utf-8"))
        if any(row["province"] != "shandong" for row in values): raise ValueError("山东资料混入其他省份")
        return values

    school_records = records("shandong-institutions.json")
    plans = records("shandong-adult-programs.json")
    controls = records("shandong-adult-control-scores.json")
    keys = [(r["institution_code"], r["year"], r["major_code"], r["line_type"], r["round"]) for r in plans]
    if len(keys) != len(set(keys)): raise ValueError("山东来源记录重复")
    province = db.query(Province).filter_by(code="shandong").one_or_none()
    if province is None:
        province = Province(code="shandong", name="山东")
        db.add(province)
        db.flush()
    province.note = NOTE
    counts = {"institutions_added": 0, "plans_added": 0, "controls_added": 0}
    schools, details = {}, {}
    for record in school_records:
        code = record["institution_code"]
        school = db.query(Institution).filter_by(province_id=province.id, code=code).one_or_none()
        if school is None:
            school = Institution(province_id=province.id, code=code)
            db.add(school)
            counts["institutions_added"] += 1
        school.name, school.city = record["institution_name"], record["city"]
        schools[code], details[code] = school, {}
    db.flush()
    active_year = max(r["year"] for r in plans if r["line_type"] == "招生专业目录")
    for record in plans:
        if record["level"] != "专升本" or record["line_type"] not in ("招生专业目录", "征集计划"):
            raise ValueError("山东招生资料口径错误")
        if record["line_type"] == "招生专业目录" and record["plan_count"] is not None:
            raise ValueError("不得为目录填入未公布的计划数")
        school = schools[record["institution_code"]]
        key = dict(institution_id=school.id, **{k: record[k] for k in ("year", "major_code", "line_type", "round")})
        plan = db.query(AdmissionPlan).filter_by(**key).one_or_none()
        if plan is None:
            plan = AdmissionPlan(**key)
            db.add(plan)
            counts["plans_added"] += 1
        for field in PLAN_FIELDS: setattr(plan, field, record.get(field))
        plan.source = record["source_url"]
        details[school.code][f"{plan.year}/{plan.round}/{plan.major_code}"] = {key: record.get(key) for key in DETAIL_FIELDS}
    for record in school_records:
        school = schools[record["institution_code"]]
        school.supplemental_data = {**(school.supplemental_data or {}), "active_catalog_year": active_year,
                                    "plan_details": details[school.code], "city_source_url": record["city_source_url"]}
    for record in controls:
        if record["level"] != "专升本" or record["line_type"] != "省控线" or record["review_status"] != "visually_verified":
            raise ValueError("省控线未核实或口径不符")
        key = dict(province_id=province.id, **{key: record[key] for key in ("year", "level", "category_name", "line_type", "round")})
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
        counts = import_shandong(db)
    print("山东数据导入完成：" + json.dumps(counts, ensure_ascii=False))


if __name__ == "__main__":
    run()
