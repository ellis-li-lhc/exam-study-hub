# 把前端 mvp.js 里的专业数据灌入数据库。可重复运行（已存在的跳过）。
# 运行：在 server 目录下 `./.venv/bin/python -m scripts.seed`
import json
from pathlib import Path

from app.db.session import SessionLocal
from app.models.catalog import Major, MajorSubject, Province, Institution, AdmissionScore

SCORES_FILE = Path(__file__).resolve().parent.parent / "scraped-data" / "jiangsu-adult-scores.json"

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

        # —— 院校 + 投档线（来自 scraped-data 的江苏数据）——
        inst_added = score_added = 0
        if SCORES_FILE.exists():
            jiangsu = db.query(Province).filter_by(code="jiangsu").first()
            records = json.loads(SCORES_FILE.read_text(encoding="utf-8"))
            inst_cache = {}  # code -> Institution
            for rec in records:
                code = rec["institution_code"]
                inst = inst_cache.get(code)
                if inst is None:
                    inst = db.query(Institution).filter_by(
                        province_id=jiangsu.id, code=code
                    ).first()
                    if inst is None:
                        inst = Institution(code=code, name=rec["institution_name"], province_id=jiangsu.id)
                        db.add(inst)
                        db.flush()  # 拿到 inst.id
                        inst_added += 1
                    inst_cache[code] = inst
                # 同院校同年同科类已存在则跳过，避免重复
                exists = db.query(AdmissionScore).filter_by(
                    institution_id=inst.id, year=rec["year"], category_name=rec["category_name"]
                ).first()
                if exists:
                    continue
                db.add(AdmissionScore(
                    institution_id=inst.id,
                    year=rec["year"],
                    category_code=rec.get("category_code"),
                    category_name=rec["category_name"],
                    score=int(rec["score"]) if rec.get("score") is not None else None,
                    line_type=rec.get("line_type", "院校投档线"),
                    source=rec.get("source_url"),
                ))
                score_added += 1
            db.commit()
            print(f"新增院校 {inst_added} 所（共 {db.query(Institution).count()}）；"
                  f"新增投档线 {score_added} 条（共 {db.query(AdmissionScore).count()}）")
        else:
            print(f"未找到 {SCORES_FILE}，跳过院校数据")
    finally:
        db.close()


if __name__ == "__main__":
    run()
