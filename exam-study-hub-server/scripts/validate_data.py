"""校验招生数据口径，防止省控线/院校线/专业计划混用。

用法：在 server 目录下 `python -m scripts.validate_data`
"""
from sqlalchemy import select

from app.db.session import SessionLocal
from app.models.catalog import AdmissionPlan, AdmissionScore, Institution, Major, Province, ProvinceControlScore


def fail(message: str):
    raise SystemExit(f"数据校验失败：{message}")


def run():
    db = SessionLocal()
    try:
        henan = db.scalars(select(Province).where(Province.code == "henan")).first()
        if henan is None:
            fail("缺少河南省份记录")
        jiangsu = db.scalars(select(Province).where(Province.code == "jiangsu")).first()
        if jiangsu is None:
            fail("缺少江苏省份记录")
        zhejiang = db.scalars(select(Province).where(Province.code == "zhejiang")).first()
        if zhejiang is None:
            fail("缺少浙江省份记录")
        guangdong = db.scalars(select(Province).where(Province.code == "guangdong")).first()
        if guangdong is None:
            fail("缺少广东省份记录")
        shanghai = db.query(Province).filter_by(code="shanghai").one_or_none()
        if shanghai is None:
            fail("缺少上海省份记录")
        shandong = db.query(Province).filter_by(code="shandong").one_or_none()
        if shandong is None:
            fail("缺少山东省份记录")
        hebei = db.query(Province).filter_by(code="hebei").one_or_none()
        if hebei is None:
            fail("缺少河北省份记录")
        for label, actual, expected in (
            ("院校", db.query(Institution).filter_by(province_id=hebei.id).count(), 87),
            ("专升本计划", db.query(AdmissionPlan).join(Institution).filter(Institution.province_id == hebei.id).count(), 1709),
            ("院校实际录取线", db.query(AdmissionScore).join(Institution).filter(Institution.province_id == hebei.id).count(), 0),
            ("分人群省控线", db.query(ProvinceControlScore).filter_by(province_id=hebei.id).count(), 45),
        ):
            if actual != expected: fail(f"河北{label}应为 {expected}，实际 {actual}")
        for label, actual, expected in (
            ("院校", db.query(Institution).filter_by(province_id=shandong.id).count(), 89),
            ("目录及征集记录", db.query(AdmissionPlan).join(Institution).filter(Institution.province_id == shandong.id).count(), 2738),
            ("院校实际录取线", db.query(AdmissionScore).join(Institution).filter(Institution.province_id == shandong.id).count(), 0),
            ("省控线", db.query(ProvinceControlScore).filter_by(province_id=shandong.id).count(), 29),
        ):
            if actual != expected: fail(f"山东{label}应为 {expected}，实际 {actual}")
        shanghai_counts = {
            "院校": (db.query(Institution).filter_by(province_id=shanghai.id).count(), 40),
            "专业目录及计划": (db.query(AdmissionPlan).join(Institution).filter(Institution.province_id == shanghai.id).count(), 679),
            "院校实际录取线": (db.query(AdmissionScore).join(Institution).filter(Institution.province_id == shanghai.id).count(), 0),
            "市控线": (db.query(ProvinceControlScore).filter_by(province_id=shanghai.id).count(), 24),
        }
        for label, (actual, expected) in shanghai_counts.items():
            if actual != expected:
                fail(f"上海{label}应为 {expected}，实际 {actual}")

        major_count = db.query(Major).count()
        if major_count != 66:
            fail(f"专业主数据应为 66 个，实际 {major_count}")
        legacy_major_codes = ["business", "accounting", "law", "education", "computer", "chinese"]
        legacy_remaining = db.query(Major).filter(Major.code.in_(legacy_major_codes)).count()
        if legacy_remaining:
            fail(f"专业主数据仍有旧 code {legacy_remaining} 个")
        software = db.scalars(select(Major).where(Major.code == "ruanjian", Major.name == "软件工程")).first()
        if software is None:
            fail("专业主数据缺少软件工程/ruanjian")

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
        jiangsu_score_count = (
            db.query(AdmissionScore)
            .join(Institution)
            .filter(Institution.province_id == jiangsu.id)
            .count()
        )
        jiangsu_plan_count = (
            db.query(AdmissionPlan)
            .join(Institution)
            .filter(Institution.province_id == jiangsu.id)
            .count()
        )
        zhejiang_control_count = db.query(ProvinceControlScore).filter_by(province_id=zhejiang.id).count()
        zhejiang_plan_count = (
            db.query(AdmissionPlan)
            .join(Institution)
            .filter(Institution.province_id == zhejiang.id)
            .count()
        )
        guangdong_institution_count = db.query(Institution).filter_by(province_id=guangdong.id).count()
        guangdong_score_count = (
            db.query(AdmissionScore)
            .join(Institution)
            .filter(Institution.province_id == guangdong.id)
            .count()
        )
        guangdong_plan_count = (
            db.query(AdmissionPlan)
            .join(Institution)
            .filter(Institution.province_id == guangdong.id)
            .count()
        )
        guangdong_control_count = db.query(ProvinceControlScore).filter_by(province_id=guangdong.id).count()

        if henan_institution_count != 39:
            fail(f"河南院校数应为 39，实际 {henan_institution_count}")
        if henan_score_count != 90:
            fail(f"河南院校科类分数应为 90，实际 {henan_score_count}")
        if henan_plan_count != 199:
            fail(f"河南专业计划应为 199，实际 {henan_plan_count}")
        if henan_control_count != 26:
            fail(f"河南省控线应为 26，实际 {henan_control_count}")
        if jiangsu_score_count != 171:
            fail(f"江苏院校科类分数应为 171，实际 {jiangsu_score_count}")
        if jiangsu_plan_count != 89:
            fail(f"江苏本科征求计划应为 89，实际 {jiangsu_plan_count}")
        if zhejiang_control_count != 64:
            fail(f"浙江省控线应为 64，实际 {zhejiang_control_count}")
        if zhejiang_plan_count != 541:
            fail(f"浙江招生专业目录应为 541，实际 {zhejiang_plan_count}")
        if guangdong_institution_count != 79:
            fail(f"广东院校数应为 79，实际 {guangdong_institution_count}")
        if guangdong_score_count != 573:
            fail(f"广东院校科目组投档线应为 573，实际 {guangdong_score_count}")
        if guangdong_plan_count != 841:
            fail(f"广东招生计划应为 841（主批次746、征集95），实际 {guangdong_plan_count}")
        if guangdong_control_count != 27:
            fail(f"广东省控线应为 27，实际 {guangdong_control_count}")

        print("数据校验通过：专业 66 个；河南院校 39 所，院校科类分数 90 条，专业计划 199 条，省控线 26 条；"
              "江苏院校科类分数 171 条，本科征求计划 89 条；"
              "浙江省控线 64 条，招生专业目录 541 条；"
              "广东院校 79 所，院校科目组投档线 573 条，主批次计划 746 条、征集明细 95 条，省控线 27 条；"
              "上海院校 40 所，2026目录269条、2025主批次279条及征求131条，市控线24条，院校实际录取线0条；"
              "山东院校89所，2026目录952条、2025目录873条及两次征集465/448条，省控线29条，院校实际录取线0条；"
              "河北院校87所，2024/2025计划885/824条，分人群省控线45条，院校实际录取线0条。")
    finally:
        db.close()


if __name__ == "__main__":
    run()
