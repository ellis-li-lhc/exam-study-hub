"""抓取并解析江苏省成人高校招生「专升本投档分数线 / 本科征求计划」。

数据来源：江苏省教育考试院（www.jseea.cn）成人高校招生公示的 .xls 文件。
输出：结构化 JSON 到 exam-study-hub-server/scraped-data/。
用法：在 server 目录下 `./.venv/bin/python -m scripts.scrape_jiangsu`

说明：投档线粒度为「院校 × 科类 × 投档分」；本科征求计划包含「院校 × 专业」
余缺计划明细，可用于一部分江苏院校的真实专业匹配。报名期完整专业目录仍以
江苏省教育考试院报名系统和院校当年招生简章为准。
"""
import json
import urllib.request
from collections import defaultdict
from pathlib import Path

import xlrd

# 数据源：可按年份 / 批次扩充
SCORE_SOURCES = [
    {
        "year": 2025,
        "level": "专升本",
        "line_type": "院校投档线",
        "round": "预填志愿(主批次)",
        "url": "https://www.jseea.cn/webfile/upload/2025/12-09/10-14-350709-1513280903.xls",
    },
]

PLAN_SOURCES = [
    {
        "year": 2025,
        "level": "专升本",
        "line_type": "征求计划",
        "round": "本科录取阶段征求计划",
        "url": "https://www.jseea.cn/webfile/upload/2025/12-10/19-26-37081638699529.xls",
    },
]

UA = {"User-Agent": "Mozilla/5.0"}
OUT_DIR = Path(__file__).resolve().parent.parent / "scraped-data"


def fetch_xls(url: str) -> bytes:
    req = urllib.request.Request(url, headers=UA)
    with urllib.request.urlopen(req, timeout=40) as resp:
        return resp.read()


def parse_scores(content: bytes, meta: dict) -> list[dict]:
    wb = xlrd.open_workbook(file_contents=content)
    sh = wb.sheet_by_index(0)
    records = []
    for r in range(sh.nrows):
        row = [sh.cell_value(r, c) for c in range(sh.ncols)]
        if len(row) < 5:
            continue
        code = str(row[0]).strip()
        cat_name = str(row[3]).strip()
        # 数据行特征：有院校代码，且科类名以“专升本”开头（过滤标题/表头/空行）
        if not code or not cat_name.startswith("专升本"):
            continue
        try:
            score = float(row[4])
        except (ValueError, TypeError):
            score = None
        records.append({
            "province": "jiangsu",
            "year": meta["year"],
            "level": meta["level"],
            "institution_code": code,
            "institution_name": str(row[1]).strip(),
            "category_code": str(row[2]).strip(),
            "category_name": cat_name,
            "score": score,
            "line_type": meta["line_type"],
            "round": meta["round"],
            "source_url": meta["url"],
        })
    return records


def parse_plans(content: bytes, meta: dict) -> list[dict]:
    wb = xlrd.open_workbook(file_contents=content)
    sh = wb.sheet_by_index(0)
    headers = [str(sh.cell_value(1, c)).strip() for c in range(sh.ncols)] if sh.nrows > 1 else []
    required = [
        "院校代号",
        "院校名称",
        "层次名称",
        "专业代码",
        "专业名称",
        "科类代码",
        "科类名称",
        "院校计划数",
    ]
    missing = [name for name in required if name not in headers]
    if missing:
        raise RuntimeError(f"江苏征求计划表头缺失：{missing}")

    col = {name: headers.index(name) for name in headers}
    aggregated: dict[tuple[str, str, str, str, str, str], int] = defaultdict(int)
    for r in range(2, sh.nrows):
        row = [sh.cell_value(r, c) for c in range(sh.ncols)]
        institution_code = str(row[col["院校代号"]]).strip()
        institution_name = str(row[col["院校名称"]]).strip()
        level = str(row[col["层次名称"]]).strip()
        major_code = str(row[col["专业代码"]]).strip()
        major_name = str(row[col["专业名称"]]).strip()
        category_code = str(row[col["科类代码"]]).strip()
        category_name = str(row[col["科类名称"]]).strip()
        if not institution_code or level != meta["level"] or not major_code or not major_name:
            continue
        try:
            plan_count = int(float(row[col["院校计划数"]]))
        except (ValueError, TypeError):
            plan_count = 0
        key = (institution_code, institution_name, major_code, major_name, category_code, category_name)
        aggregated[key] += plan_count

    records = []
    for (institution_code, institution_name, major_code, major_name, category_code, category_name), plan_count in sorted(aggregated.items()):
        records.append({
            "province": "jiangsu",
            "year": meta["year"],
            "level": meta["level"],
            "institution_code": institution_code,
            "institution_name": institution_name,
            "major_code": major_code,
            "major_name": major_name,
            "category_code": category_code,
            "category_name": category_name,
            "plan_count": plan_count,
            "line_type": meta["line_type"],
            "round": meta["round"],
            "source_url": meta["url"],
        })
    return records


def run():
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    all_scores = []
    for meta in SCORE_SOURCES:
        content = fetch_xls(meta["url"])
        recs = parse_scores(content, meta)
        all_scores.extend(recs)
        print(f"{meta['year']} {meta['level']} {meta['round']}: 解析 {len(recs)} 条")

    scores_out = OUT_DIR / "jiangsu-adult-scores.json"
    scores_out.write_text(json.dumps(all_scores, ensure_ascii=False, indent=2), encoding="utf-8")
    score_institutions = {(r["institution_code"], r["institution_name"]) for r in all_scores}
    print(f"投档线合计 {len(all_scores)} 条，去重院校 {len(score_institutions)} 所 → {scores_out}")

    all_plans = []
    for meta in PLAN_SOURCES:
        content = fetch_xls(meta["url"])
        recs = parse_plans(content, meta)
        all_plans.extend(recs)
        print(f"{meta['year']} {meta['level']} {meta['round']}: 解析专业计划 {len(recs)} 条")

    plans_out = OUT_DIR / "jiangsu-adult-collection-plan-2025.json"
    plans_out.write_text(json.dumps(all_plans, ensure_ascii=False, indent=2), encoding="utf-8")
    plan_institutions = {(r["institution_code"], r["institution_name"]) for r in all_plans}
    print(f"征求计划合计 {len(all_plans)} 条，去重院校 {len(plan_institutions)} 所 → {plans_out}")


if __name__ == "__main__":
    run()
