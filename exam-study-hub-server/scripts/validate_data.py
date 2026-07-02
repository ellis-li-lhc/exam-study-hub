"""校验招生数据口径，防止省控线/院校线/专业计划混用。

用法：在 server 目录下 `python -m scripts.validate_data`
"""
from sqlalchemy import select

from app.db.session import SessionLocal
from app.models.catalog import AdmissionPlan, AdmissionScore, Institution, Province, ProvinceControlScore


def fail(message: str):
    raise SystemExit(f"数据校验失败：{message}")


def run():
    db = SessionLocal()
    try:
        henan = db.scalars(select(Province).where(Province.code == "henan")).first()
        if henan is None:
            fail("缺少河南省份记录")

        old_control = db.scalars(
            select(Institution).where(
                Institution.province_id == henan.id,
                Institution.code == "henan-control-line",
            )
        ).first()
        if old_control is not None:
            fail("河南省控线仍作为院校存在")

        score_control_count = db.query(AdmissionScore).filter_by(line_type="省控线").count()
        if score_control_count:
            fail(f"admission_scores 中仍有省控线 {score_control_count} 条")

        roundless_scores = db.query(AdmissionScore).filter(AdmissionScore.round.is_(None)).count()
        if roundless_scores:
            fail(f"admission_scores 中仍有无批次旧记录 {roundless_scores} 条")

        henan_institution_count = db.query(Institution).filter_by(province_id=henan.id).count()
        henan_score_count = (
            db.query(AdmissionScore)
            .join(Institution)
            .filter(Institution.province_id == henan.id)
            .count()
        )
        henan_plan_count = (
            db.query(AdmissionPlan)
            .join(Institution)
            .filter(Institution.province_id == henan.id)
            .count()
        )
        henan_control_count = db.query(ProvinceControlScore).filter_by(province_id=henan.id).count()

        if henan_institution_count != 39:
            fail(f"河南院校数应为 39，实际 {henan_institution_count}")
        if henan_score_count != 90:
            fail(f"河南院校科类分数应为 90，实际 {henan_score_count}")
        if henan_plan_count != 199:
            fail(f"河南专业计划应为 199，实际 {henan_plan_count}")
        if henan_control_count != 26:
            fail(f"河南省控线应为 26，实际 {henan_control_count}")

        print("数据校验通过：河南院校 39 所，院校科类分数 90 条，专业计划 199 条，省控线 26 条。")
    finally:
        db.close()


if __name__ == "__main__":
    run()
