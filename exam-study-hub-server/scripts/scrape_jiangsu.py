"""抓取并解析江苏省成人高校招生「专升本投档分数线」。

数据来源：江苏省教育考试院（www.jseea.cn）成人高校招生公示的 .xls 文件。
输出：结构化 JSON 到 exam-study-hub-server/scraped-data/。
用法：在 server 目录下 `./.venv/bin/python -m scripts.scrape_jiangsu`

说明：该数据粒度为「院校 × 科类 × 投档分」，不含逐校具体专业名
（成人高考的专业目录在网上报名系统内、报名期才开放，非公开可下载）。
"""
import json
import urllib.request
from pathlib import Path

import xlrd

# 数据源：可按年份 / 批次扩充
SOURCES = [
    {
        "year": 2025,
        "level": "专升本",
        "line_type": "院校投档线",
        "round": "预填志愿(主批次)",
        "url": "https://www.jseea.cn/webfile/upload/2025/12-09/10-14-350709-1513280903.xls",
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


def run():
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    all_records = []
    for meta in SOURCES:
        content = fetch_xls(meta["url"])
        recs = parse_scores(content, meta)
        all_records.extend(recs)
        print(f"{meta['year']} {meta['level']} {meta['round']}: 解析 {len(recs)} 条")

    out = OUT_DIR / "jiangsu-adult-scores.json"
    out.write_text(json.dumps(all_records, ensure_ascii=False, indent=2), encoding="utf-8")
    institutions = {(r["institution_code"], r["institution_name"]) for r in all_records}
    print(f"合计 {len(all_records)} 条，去重院校 {len(institutions)} 所 → {out}")


if __name__ == "__main__":
    run()
