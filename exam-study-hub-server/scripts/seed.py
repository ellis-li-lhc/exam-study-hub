# 把前端 mvp.js 里的专业数据灌入数据库。可重复运行（已存在的跳过）。
# 运行：在 server 目录下 `./.venv/bin/python -m scripts.seed`
import json
from pathlib import Path

from app.db.session import SessionLocal
from app.models.catalog import (
    AdmissionPlan,
    AdmissionScore,
    Major,
    MajorSubject,
    Province,
    ProvinceControlScore,
    Institution,
)

SCORES_DIR = Path(__file__).resolve().parent.parent / "scraped-data"
SCORE_FILES = [
    SCORES_DIR / "jiangsu-adult-scores.json",
    SCORES_DIR / "henan-adult-scores.json",
]
CONTROL_SCORE_FILES = [
    SCORES_DIR / "henan-adult-control-scores.json",
]
PLAN_FILES = [
    SCORES_DIR / "henan-adult-collection-plan-2025.json",
]

# 院校所在市（校本部）。来自院校公开资料；外省校标其校本部所在市。
# 用于报考档案按市筛选院校（成考实际就读以教学点为准，教学点信息以招生简章为准）。
CITY_BY_NAME = {
    # 南京
    "中国药科大学": "南京", "南京中医药大学": "南京", "南京信息工程大学": "南京",
    "南京农业大学": "南京", "南京医科大学": "南京", "南京审计大学": "南京",
    "南京工业大学": "南京", "南京工程学院": "南京", "南京师范大学": "南京",
    "南京晓庄学院": "南京", "南京林业大学": "南京", "南京特殊教育师范学院": "南京",
    "南京理工大学": "南京", "南京航空航天大学": "南京", "南京财经大学": "南京",
    "南京邮电大学": "南京", "河海大学": "南京", "金陵科技学院": "南京",
    "江苏第二师范学院": "南京", "江苏警官学院": "南京",
    # 徐州
    "中国矿业大学": "徐州", "江苏师范大学": "徐州", "徐州医科大学": "徐州", "徐州工程学院": "徐州",
    # 苏州
    "苏州大学": "苏州", "苏州科技大学": "苏州", "苏州工学院": "苏州",
    # 无锡
    "江南大学": "无锡", "无锡太湖学院": "无锡", "无锡学院": "无锡",
    # 常州
    "常州大学": "常州", "常州工学院": "常州", "河海大学（常州校区）": "常州", "江苏理工学院": "常州",
    # 镇江
    "江苏大学": "镇江", "江苏科技大学": "镇江",
    # 扬州
    "扬州大学": "扬州",
    # 南通
    "南通大学": "南通", "南通理工学院": "南通",
    # 盐城
    "盐城工学院": "盐城", "盐城师范学院": "盐城",
    # 淮安
    "淮阴工学院": "淮安", "淮阴师范学院": "淮安",
    # 连云港
    "江苏海洋大学": "连云港",
    # 宿迁
    "宿迁学院": "宿迁",
    # 泰州
    "泰州学院": "泰州",
    # 省外（校本部所在市）
    "上海海事大学": "上海", "大连海事大学": "大连",
    "西安交通大学": "西安", "西安建筑科技大学": "西安", "长安大学": "西安",
    # 河南成人高招征集志愿计划（2025）院校/校本部所在市
    "中国石油大学(华东)": "青岛", "西安电子科技大学": "西安", "中央财经大学": "北京",
    "中国地质大学(武汉)": "武汉", "北京理工大学": "北京", "西北工业大学": "西安",
    "中国消防救援学院": "北京", "东北农业大学": "哈尔滨", "华东交通大学": "南昌",
    "涟源钢铁总厂职工大学": "娄底", "西北民族大学": "兰州",
    "河南财政金融学院": "郑州", "郑州航空工业管理学院": "郑州", "河南工业大学": "郑州",
    "中原工学院": "郑州", "郑州大学": "郑州", "河南农业大学": "郑州",
    "河南大学": "开封", "河南医药大学": "郑州", "河南工学院": "新乡",
    "河南工程学院": "郑州", "郑州工程技术学院": "郑州", "洛阳理工学院": "洛阳",
    "郑州师范学院": "郑州", "河南城建学院": "平顶山", "郑州西亚斯学院": "郑州",
    "安阳工学院": "安阳", "黄淮学院": "驻马店", "南阳理工学院": "南阳",
    "黄河交通学院": "焦作", "河南科技职业大学": "周口", "河南开封科技传媒学院": "开封",
    "鹤壁开放大学": "鹤壁", "驻马店开放大学": "驻马店", "信阳开放大学": "信阳",
    "郑州财经学院": "郑州",
}

# 与前端 exam-study-hub-client/src/data/mvp.js 的 provinceOptions 保持一致
PROVINCES = [
    {"code": "henan", "name": "河南", "note": "户籍地，可直接按当年公告准备材料"},
    {"code": "jiangsu", "name": "江苏", "note": "工作地，非户籍报名需核验居住证或连续社保"},
]

# 与前端 exam-study-hub-client/src/data/mvp.js 的 majorOptions 保持一致
MAJORS = [
    {"code": "business", "name": "工商管理", "category": "经济管理类",
     "subjects": ["政治", "英语", "高等数学（二）"]},
    {"code": "accounting", "name": "会计学", "category": "经济管理类",
     "subjects": ["政治", "英语", "高等数学（二）"]},
    {"code": "law", "name": "法学", "category": "法学类",
     "subjects": ["政治", "英语", "民法"]},
    {"code": "education", "name": "教育学", "category": "教育学类",
     "subjects": ["政治", "英语", "教育理论"]},
    {"code": "computer", "name": "计算机科学与技术", "category": "理工类",
     "subjects": ["政治", "英语", "高等数学（一）"]},
    {"code": "chinese", "name": "汉语言文学", "category": "文史中医类",
     "subjects": ["政治", "英语", "大学语文"]},
]


def run():
    db = SessionLocal()
    try:
        # —— 省份 ——
        province_added = 0
        for item in PROVINCES:
            if db.query(Province).filter_by(code=item["code"]).first():
                continue
            db.add(Province(**item))
            province_added += 1

        # —— 专业 ——
        added = 0
        for item in MAJORS:
            exists = db.query(Major).filter_by(code=item["code"]).first()
            if exists:
                continue
            major = Major(code=item["code"], name=item["name"], category=item["category"])
            major.subjects = [MajorSubject(subject=s) for s in item["subjects"]]
            db.add(major)
            added += 1
        db.commit()
        print(f"新增省份 {province_added} 个（共 {db.query(Province).count()}）；"
              f"新增专业 {added} 个（共 {db.query(Major).count()}）")

        # —— 清理旧版河南省控线伪院校（省控线现在入 province_control_scores）——
        henan = db.query(Province).filter_by(code="henan").first()
        if henan is not None:
            old_control = db.query(Institution).filter_by(
                province_id=henan.id, code="henan-control-line"
            ).first()
            if old_control is not None:
                db.delete(old_control)
                db.commit()
        old_roundless_scores = db.query(AdmissionScore).filter(AdmissionScore.round.is_(None)).all()
        if old_roundless_scores:
            for score in old_roundless_scores:
                db.delete(score)
            db.commit()

        # —— 院校 + 分数线（来自 scraped-data 的多省数据）——
        inst_added = score_added = 0
        loaded_files = 0
        for scores_file in SCORE_FILES:
            if not scores_file.exists():
                print(f"未找到 {scores_file}，跳过")
                continue
            records = json.loads(scores_file.read_text(encoding="utf-8"))
            if not records:
                continue
            province_code = records[0]["province"]
            province = db.query(Province).filter_by(code=province_code).first()
            if province is None:
                print(f"未找到省份 {province_code}，跳过 {scores_file}")
                continue
            loaded_files += 1
            inst_cache = {}  # (province_id, code) -> Institution
            for rec in records:
                if rec.get("line_type") == "省控线":
                    continue
                code = rec["institution_code"]
                inst_key = (province.id, code)
                inst = inst_cache.get(inst_key)
                if inst is None:
                    inst = db.query(Institution).filter_by(
                        province_id=province.id, code=code
                    ).first()
                    if inst is None:
                        inst = Institution(code=code, name=rec["institution_name"], province_id=province.id)
                        db.add(inst)
                        db.flush()  # 拿到 inst.id
                        inst_added += 1
                    inst_cache[inst_key] = inst
                # 同院校同年同科类已存在则跳过，避免重复
                exists = db.query(AdmissionScore).filter_by(
                    institution_id=inst.id,
                    year=rec["year"],
                    category_name=rec["category_name"],
                    line_type=rec.get("line_type", "院校投档线"),
                    round=rec.get("round"),
                ).first()
                if exists is not None:
                    exists.category_code = rec.get("category_code")
                    exists.score = int(rec["score"]) if rec.get("score") is not None else None
                    exists.source = rec.get("source_url")
                    continue
                db.add(AdmissionScore(
                    institution_id=inst.id,
                    year=rec["year"],
                    category_code=rec.get("category_code"),
                    category_name=rec["category_name"],
                    score=int(rec["score"]) if rec.get("score") is not None else None,
                    line_type=rec.get("line_type", "院校投档线"),
                    round=rec.get("round"),
                    source=rec.get("source_url"),
                ))
                score_added += 1
        if loaded_files:
            db.commit()
            print(f"新增院校 {inst_added} 所（共 {db.query(Institution).count()}）；"
                  f"新增投档线 {score_added} 条（共 {db.query(AdmissionScore).count()}）")
        else:
            print("未找到可用 scraped-data 分数线文件，跳过院校数据")

        # —— 省控线（独立于院校，不展示为院校卡片）——
        control_added = 0
        for control_file in CONTROL_SCORE_FILES:
            if not control_file.exists():
                print(f"未找到 {control_file}，跳过省控线")
                continue
            records = json.loads(control_file.read_text(encoding="utf-8"))
            for rec in records:
                province = db.query(Province).filter_by(code=rec["province"]).first()
                if province is None:
                    continue
                exists = db.query(ProvinceControlScore).filter_by(
                    province_id=province.id,
                    year=rec["year"],
                    level=rec.get("level", "专升本"),
                    category_name=rec["category_name"],
                    line_type=rec.get("line_type", "省控线"),
                    round=rec.get("round"),
                ).first()
                if exists is not None:
                    exists.category_code = rec.get("category_code")
                    exists.score = int(rec["score"]) if rec.get("score") is not None else None
                    exists.source = rec.get("source_url")
                    continue
                db.add(ProvinceControlScore(
                    province_id=province.id,
                    year=rec["year"],
                    level=rec.get("level", "专升本"),
                    category_code=rec.get("category_code"),
                    category_name=rec["category_name"],
                    score=int(rec["score"]) if rec.get("score") is not None else None,
                    line_type=rec.get("line_type", "省控线"),
                    round=rec.get("round"),
                    source=rec.get("source_url"),
                ))
                control_added += 1
        db.commit()
        print(f"新增省控线 {control_added} 条（共 {db.query(ProvinceControlScore).count()}）")

        # —— 招生专业计划（用于河南等有专业明细的数据做真实专业匹配）——
        plan_added = 0
        for plan_file in PLAN_FILES:
            if not plan_file.exists():
                print(f"未找到 {plan_file}，跳过专业计划")
                continue
            records = json.loads(plan_file.read_text(encoding="utf-8"))
            inst_cache = {}
            for rec in records:
                province = db.query(Province).filter_by(code=rec["province"]).first()
                if province is None:
                    continue
                code = rec["institution_code"]
                inst_key = (province.id, code)
                inst = inst_cache.get(inst_key)
                if inst is None:
                    inst = db.query(Institution).filter_by(province_id=province.id, code=code).first()
                    if inst is None:
                        inst = Institution(code=code, name=rec["institution_name"], province_id=province.id)
                        db.add(inst)
                        db.flush()
                    inst_cache[inst_key] = inst

                exists = db.query(AdmissionPlan).filter_by(
                    institution_id=inst.id,
                    year=rec["year"],
                    major_code=rec["major_code"],
                    line_type=rec.get("line_type", "招生计划"),
                    round=rec.get("round"),
                ).first()
                if exists is not None:
                    exists.major_name = rec["major_name"]
                    exists.level = rec.get("level", "专升本")
                    exists.category_code = rec.get("category_code")
                    exists.category_name = rec.get("category_name")
                    exists.plan_count = rec.get("plan_count")
                    exists.source = rec.get("source_url")
                    continue
                db.add(AdmissionPlan(
                    institution_id=inst.id,
                    year=rec["year"],
                    major_code=rec["major_code"],
                    major_name=rec["major_name"],
                    level=rec.get("level", "专升本"),
                    category_code=rec.get("category_code"),
                    category_name=rec.get("category_name"),
                    plan_count=rec.get("plan_count"),
                    line_type=rec.get("line_type", "招生计划"),
                    round=rec.get("round"),
                    source=rec.get("source_url"),
                ))
                plan_added += 1
        db.commit()
        print(f"新增专业计划 {plan_added} 条（共 {db.query(AdmissionPlan).count()}）")

        # —— 回填院校所在市（按名称映射，可重复运行）——
        city_updated = 0
        for inst in db.query(Institution).all():
            city = CITY_BY_NAME.get(inst.name)
            if city and inst.city != city:
                inst.city = city
                city_updated += 1
        db.commit()
        missing = [i.name for i in db.query(Institution).all() if not i.city]
        print(f"回填院校所在市 {city_updated} 所；仍缺城市 {len(missing)} 所" +
              (f"：{missing}" if missing else ""))
    finally:
        db.close()


if __name__ == "__main__":
    run()
