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
    SCORES_DIR / "zhejiang-adult-control-scores.json",
]
PLAN_FILES = [
    SCORES_DIR / "henan-adult-collection-plan-2025.json",
    SCORES_DIR / "jiangsu-adult-collection-plan-2025.json",
    SCORES_DIR / "zhejiang-adult-program-catalog-2025.json",
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
    # 浙江 2025 成人高校招生章程（专升本院校）
    "衢州学院": "衢州", "中国美术学院": "杭州", "浙江工业大学之江学院": "绍兴",
    "浙江农林大学暨阳学院": "绍兴", "温州商学院": "温州", "中国计量大学": "杭州",
    "浙江音乐学院": "杭州", "杭州电子科技大学": "杭州", "湖州学院": "湖州",
    "嘉兴南湖学院": "嘉兴", "浙江药科职业大学": "宁波", "浙江海洋大学": "舟山",
    "宁波大学科学技术学院": "宁波", "宁波财经学院": "宁波",
    "浙江广厦建设职业技术大学": "金华", "浙江工商大学杭州商学院": "杭州",
    "嘉兴大学": "嘉兴", "浙江万里学院": "宁波", "浙江外国语学院": "杭州",
    "宁波大学": "宁波", "浙江工业大学": "杭州", "浙江财经大学": "杭州",
    "浙江中医药大学": "杭州", "浙江农林大学": "杭州", "浙江科技大学": "杭州",
    "温州医科大学": "温州", "浙江师范大学": "金华", "杭州师范大学": "杭州",
    "温州大学": "温州", "湖州师范学院": "湖州", "绍兴文理学院": "绍兴",
    "台州学院": "台州", "浙江水利水电学院": "杭州", "浙江树人学院": "杭州",
    "浙江理工大学": "杭州", "浙江工商大学": "杭州", "浙江财经大学东方学院": "嘉兴",
    "浙大城市学院": "杭州", "宁波工程学院": "宁波",
    "浙江理工大学科技与艺术学院": "绍兴", "温州理工学院": "温州",
    "浙江开放大学": "杭州", "浙大宁波理工学院": "宁波", "杭州医学院": "杭州",
    "浙江传媒学院": "杭州", "浙江越秀外国语学院": "绍兴", "丽水学院": "丽水",
}

# 与前端 exam-study-hub-client/src/data/mvp.js 的 provinceOptions 保持一致
PROVINCES = [
    {"code": "henan", "name": "河南", "note": "户籍地，可直接按当年公告准备材料"},
    {"code": "jiangsu", "name": "江苏", "note": "工作地，非户籍报名需核验居住证或连续社保"},
    {"code": "zhejiang", "name": "浙江", "note": "已收录2018—2025省控线及2025官方招生专业目录"},
]

# 与前端 exam-study-hub-client/src/data/majors.js 的 examMajors 保持一致。
LEGACY_MAJOR_CODE_MAP = {
    "business": "gongshang-guanli",
    "accounting": "kuaiji",
    "law": "faxue",
    "education": "jiaoyuxue",
    "computer": "jisuanji",
    "chinese": "hanyu-yanwen",
}

MAJORS = [
    {"code": "gongshang-guanli", "name": "工商管理", "category": "经济管理类",
     "subjects": ["政治", "英语", "高等数学（二）"]},
    {"code": "shichang-yingxiao", "name": "市场营销", "category": "经济管理类",
     "subjects": ["政治", "英语", "高等数学（二）"]},
    {"code": "kuaiji", "name": "会计学", "category": "经济管理类",
     "subjects": ["政治", "英语", "高等数学（二）"]},
    {"code": "caiwu-guanli", "name": "财务管理", "category": "经济管理类",
     "subjects": ["政治", "英语", "高等数学（二）"]},
    {"code": "shenji", "name": "审计学", "category": "经济管理类",
     "subjects": ["政治", "英语", "高等数学（二）"]},
    {"code": "renli-ziyuan", "name": "人力资源管理", "category": "经济管理类",
     "subjects": ["政治", "英语", "高等数学（二）"]},
    {"code": "guomao", "name": "国际经济与贸易", "category": "经济管理类",
     "subjects": ["政治", "英语", "高等数学（二）"]},
    {"code": "jingjixue", "name": "经济学", "category": "经济管理类",
     "subjects": ["政治", "英语", "高等数学（二）"]},
    {"code": "jinrong", "name": "金融学", "category": "经济管理类",
     "subjects": ["政治", "英语", "高等数学（二）"]},
    {"code": "caizheng", "name": "财政学", "category": "经济管理类",
     "subjects": ["政治", "英语", "高等数学（二）"]},
    {"code": "dianzi-shangwu", "name": "电子商务", "category": "经济管理类",
     "subjects": ["政治", "英语", "高等数学（二）"]},
    {"code": "wuliu-guanli", "name": "物流管理", "category": "经济管理类",
     "subjects": ["政治", "英语", "高等数学（二）"]},
    {"code": "lvyou-guanli", "name": "旅游管理", "category": "经济管理类",
     "subjects": ["政治", "英语", "高等数学（二）"]},
    {"code": "xingzheng-guanli", "name": "行政管理", "category": "经济管理类",
     "subjects": ["政治", "英语", "高等数学（二）"]},
    {"code": "gonggong-shiye", "name": "公共事业管理", "category": "经济管理类",
     "subjects": ["政治", "英语", "高等数学（二）"]},
    {"code": "gongcheng-guanli", "name": "工程管理", "category": "经济管理类",
     "subjects": ["政治", "英语", "高等数学（二）"]},
    {"code": "fangdichan", "name": "房地产开发与管理", "category": "经济管理类",
     "subjects": ["政治", "英语", "高等数学（二）"]},
    {"code": "nonglin-jingji", "name": "农林经济管理", "category": "经济管理类",
     "subjects": ["政治", "英语", "高等数学（二）"]},
    {"code": "jisuanji", "name": "计算机科学与技术", "category": "理工类",
     "subjects": ["政治", "英语", "高等数学（一）"]},
    {"code": "ruanjian", "name": "软件工程", "category": "理工类",
     "subjects": ["政治", "英语", "高等数学（一）"]},
    {"code": "wangluo-gongcheng", "name": "网络工程", "category": "理工类",
     "subjects": ["政治", "英语", "高等数学（一）"]},
    {"code": "wulianwang", "name": "物联网工程", "category": "理工类",
     "subjects": ["政治", "英语", "高等数学（一）"]},
    {"code": "dashuju", "name": "数据科学与大数据技术", "category": "理工类",
     "subjects": ["政治", "英语", "高等数学（一）"]},
    {"code": "rengong-zhineng", "name": "人工智能", "category": "理工类",
     "subjects": ["政治", "英语", "高等数学（一）"]},
    {"code": "xinxi-guanli", "name": "信息管理与信息系统", "category": "理工类",
     "subjects": ["政治", "英语", "高等数学（一）"]},
    {"code": "dianzi-xinxi", "name": "电子信息工程", "category": "理工类",
     "subjects": ["政治", "英语", "高等数学（一）"]},
    {"code": "tongxin", "name": "通信工程", "category": "理工类",
     "subjects": ["政治", "英语", "高等数学（一）"]},
    {"code": "zidonghua", "name": "自动化", "category": "理工类",
     "subjects": ["政治", "英语", "高等数学（一）"]},
    {"code": "dianqi", "name": "电气工程及其自动化", "category": "理工类",
     "subjects": ["政治", "英语", "高等数学（一）"]},
    {"code": "jixie-gongcheng", "name": "机械工程", "category": "理工类",
     "subjects": ["政治", "英语", "高等数学（一）"]},
    {"code": "jixie-zhizao", "name": "机械设计制造及其自动化", "category": "理工类",
     "subjects": ["政治", "英语", "高等数学（一）"]},
    {"code": "cheliang", "name": "车辆工程", "category": "理工类",
     "subjects": ["政治", "英语", "高等数学（一）"]},
    {"code": "tumu", "name": "土木工程", "category": "理工类",
     "subjects": ["政治", "英语", "高等数学（一）"]},
    {"code": "jianzhuxue", "name": "建筑学", "category": "理工类",
     "subjects": ["政治", "英语", "高等数学（一）"]},
    {"code": "jipaishui", "name": "给排水科学与工程", "category": "理工类",
     "subjects": ["政治", "英语", "高等数学（一）"]},
    {"code": "huagong", "name": "化学工程与工艺", "category": "理工类",
     "subjects": ["政治", "英语", "高等数学（一）"]},
    {"code": "huanjing", "name": "环境工程", "category": "理工类",
     "subjects": ["政治", "英语", "高等数学（一）"]},
    {"code": "shipin", "name": "食品科学与工程", "category": "理工类",
     "subjects": ["政治", "英语", "高等数学（一）"]},
    {"code": "cailiao", "name": "材料科学与工程", "category": "理工类",
     "subjects": ["政治", "英语", "高等数学（一）"]},
    {"code": "cehui", "name": "测绘工程", "category": "理工类",
     "subjects": ["政治", "英语", "高等数学（一）"]},
    {"code": "anquan", "name": "安全工程", "category": "理工类",
     "subjects": ["政治", "英语", "高等数学（一）"]},
    {"code": "faxue", "name": "法学", "category": "法学类",
     "subjects": ["政治", "英语", "民法"]},
    {"code": "zhishi-chanquan", "name": "知识产权", "category": "法学类",
     "subjects": ["政治", "英语", "民法"]},
    {"code": "shehui-gongzuo", "name": "社会工作", "category": "法学类",
     "subjects": ["政治", "英语", "民法"]},
    {"code": "jianyuxue", "name": "监狱学", "category": "法学类",
     "subjects": ["政治", "英语", "民法"]},
    {"code": "jiaoyuxue", "name": "教育学", "category": "教育学类",
     "subjects": ["政治", "英语", "教育理论"]},
    {"code": "xueqian", "name": "学前教育", "category": "教育学类",
     "subjects": ["政治", "英语", "教育理论"]},
    {"code": "xiaoxue-jiaoyu", "name": "小学教育", "category": "教育学类",
     "subjects": ["政治", "英语", "教育理论"]},
    {"code": "tiyu-jiaoyu", "name": "体育教育", "category": "教育学类",
     "subjects": ["政治", "英语", "教育理论"]},
    {"code": "jiaoyu-jishu", "name": "教育技术学", "category": "教育学类",
     "subjects": ["政治", "英语", "教育理论"]},
    {"code": "teshu-jiaoyu", "name": "特殊教育", "category": "教育学类",
     "subjects": ["政治", "英语", "教育理论"]},
    {"code": "yingyong-xinli", "name": "应用心理学", "category": "教育学类",
     "subjects": ["政治", "英语", "教育理论"]},
    {"code": "shehui-tiyu", "name": "社会体育指导与管理", "category": "教育学类",
     "subjects": ["政治", "英语", "教育理论"]},
    {"code": "hanyu-yanwen", "name": "汉语言文学", "category": "文史中医类",
     "subjects": ["政治", "英语", "大学语文"]},
    {"code": "xinwen", "name": "新闻学", "category": "文史中医类",
     "subjects": ["政治", "英语", "大学语文"]},
    {"code": "guanggao", "name": "广告学", "category": "文史中医类",
     "subjects": ["政治", "英语", "大学语文"]},
    {"code": "guangbo-dianshi", "name": "广播电视学", "category": "文史中医类",
     "subjects": ["政治", "英语", "大学语文"]},
    {"code": "xinmeiti", "name": "网络与新媒体", "category": "文史中医类",
     "subjects": ["政治", "英语", "大学语文"]},
    {"code": "mishu", "name": "秘书学", "category": "文史中医类",
     "subjects": ["政治", "英语", "大学语文"]},
    {"code": "yingyu", "name": "英语", "category": "文史中医类",
     "subjects": ["政治", "英语", "大学语文"]},
    {"code": "shangwu-yingyu", "name": "商务英语", "category": "文史中医类",
     "subjects": ["政治", "英语", "大学语文"]},
    {"code": "riyu", "name": "日语", "category": "文史中医类",
     "subjects": ["政治", "英语", "大学语文"]},
    {"code": "lishi", "name": "历史学", "category": "文史中医类",
     "subjects": ["政治", "英语", "大学语文"]},
    {"code": "zhongyi", "name": "中医学", "category": "文史中医类",
     "subjects": ["政治", "英语", "大学语文"]},
    {"code": "zhongyao", "name": "中药学", "category": "文史中医类",
     "subjects": ["政治", "英语", "大学语文"]},
    {"code": "zhenjiu", "name": "针灸推拿学", "category": "文史中医类",
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
        # 老版本只有 6 个专业，且 code 与现在前端档案不一致；先原地升级 code。
        legacy_removed = 0
        for old_code, new_code in LEGACY_MAJOR_CODE_MAP.items():
            old = db.query(Major).filter_by(code=old_code).first()
            new = db.query(Major).filter_by(code=new_code).first()
            if old is None:
                continue
            if new is None:
                old.code = new_code
            elif old.id != new.id:
                db.delete(old)
                legacy_removed += 1
        db.flush()

        added = updated = 0
        for item in MAJORS:
            major = db.query(Major).filter_by(code=item["code"]).first()
            if major is None:
                # 防止历史库里残留同名专业但 code 不一致。
                major = db.query(Major).filter_by(name=item["name"], category=item["category"]).first()
                if major is not None:
                    major.code = item["code"]
            if major is None:
                major = Major(code=item["code"], name=item["name"], category=item["category"])
                major.subjects = [MajorSubject(subject=s) for s in item["subjects"]]
                db.add(major)
                added += 1
                continue

            before = (
                major.code,
                major.name,
                major.category,
                [subject.subject for subject in major.subjects],
            )
            major.name = item["name"]
            major.category = item["category"]
            if [subject.subject for subject in major.subjects] != item["subjects"]:
                major.subjects = [MajorSubject(subject=s) for s in item["subjects"]]
            after = (
                major.code,
                major.name,
                major.category,
                [subject.subject for subject in major.subjects],
            )
            if before != after:
                updated += 1
        db.commit()
        print(f"新增省份 {province_added} 个（共 {db.query(Province).count()}）；"
              f"新增专业 {added} 个，更新专业 {updated} 个，清理旧专业 {legacy_removed} 个"
              f"（共 {db.query(Major).count()}）")

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
