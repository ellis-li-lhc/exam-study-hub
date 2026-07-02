"""抓取并解析河南省成人高招专升本相关公开数据。

当前可公开、可追溯的数据分两类：
- 近三年「专科起点升本科」录取最低控制分数线（省控线）。
- 2025 年成人高招录取征集志愿计划 PDF 中的院校 / 专业 / 备档线。

注意：河南公开数据不是江苏那种「院校 × 科类投档线」。征集志愿备档线仅反映
征集志愿阶段余缺计划的参考线，不能等同于主批次院校投档线。

输出：
- scraped-data/henan-adult-control-scores.json
- scraped-data/henan-adult-collection-plan-2025.json
- scraped-data/henan-adult-scores.json（仅院校 / 科类备档线，不含省控线）

用法：在 server 目录下 `python -m scripts.scrape_henan`
"""
from __future__ import annotations

import json
import re
import tempfile
import urllib.error
import urllib.request
from html import unescape
from pathlib import Path


UA = {"User-Agent": "Mozilla/5.0"}
OUT_DIR = Path(__file__).resolve().parent.parent / "scraped-data"

CONTROL_SOURCES = [
    {
        "year": 2025,
        "official_url": "https://www.haeea.cn/a/202511/43602_5ad2ccaf.shtml",
        "mirror_url": "http://www.henanchengkao.net/hnck/lqfs/280.html",
    },
    {
        "year": 2024,
        "official_url": "https://www.haeea.cn/a/202411/43420_326c0414.shtml",
        "mirror_url": "http://www.henanchengkao.net/hnck/lqfs/216.html",
    },
    {
        "year": 2023,
        "official_url": "https://www.haeea.cn/a/202311/43224_63d01ffe.shtml",
        "mirror_url": "http://www.henanchengkao.net/hnck/lqfs/64.html",
    },
]

COLLECTION_PLAN_2025 = {
    "year": 2025,
    "level": "专升本",
    "line_type": "征集志愿备档线",
    "round": "征集志愿",
    "url": "https://www.haeea.cn/attach/file/20251212/20251212175749_1654_34d14f63.pdf",
}

CONTROL_INSTITUTION = {
    "code": "henan-control-line",
    "name": "河南省成人高招省控线（参考）",
}

# 河南成人高招专业代码中，院校码后三位用于标识专升本科类。
CATEGORY_BY_CODE_PREFIX = {
    "11": "专升本文史中医类",
    "12": "专升本艺术类",
    "13": "专升本理工类",
    "14": "专升本经管类",
    "15": "专升本法学类",
    "16": "专升本教育学类",
    "17": "专升本农学类",
    "18": "专升本医学类",
}

CATEGORY_PATTERNS = [
    ("专升本文史中医类", r"文史中医类\s*(\d+)\s*分"),
    ("专升本中医类", r"[（(]中医类\s*(\d+)\s*分[）)]"),
    ("专升本艺术类", r"艺术类\s*(\d+)\s*分"),
    ("专升本理工类", r"理工类\s*(\d+)\s*分"),
    ("专升本经管类", r"经管类\s*(\d+)\s*分"),
    ("专升本法学类", r"法学类\s*(\d+)\s*分"),
    ("专升本教育学类", r"教育学类\s*(\d+)\s*分"),
    ("专升本农学类", r"农学类\s*(\d+)\s*分"),
    ("专升本医学类", r"医学类\s*(\d+)\s*分"),
]


def fetch_bytes(url: str) -> bytes:
    req = urllib.request.Request(url, headers=UA)
    with urllib.request.urlopen(req, timeout=50) as resp:
        return resp.read()


def fetch_first_available(*urls: str) -> tuple[str, bytes]:
    errors = []
    for url in urls:
        try:
            return url, fetch_bytes(url)
        except (urllib.error.URLError, TimeoutError) as exc:
            errors.append(f"{url}: {exc}")
    raise RuntimeError("所有来源均无法访问：\n" + "\n".join(errors))


def html_to_text(content: bytes) -> str:
    text = content.decode("utf-8", errors="ignore")
    text = re.sub(r"<script[\s\S]*?</script>", "", text, flags=re.I)
    text = re.sub(r"<style[\s\S]*?</style>", "", text, flags=re.I)
    text = re.sub(r"<[^>]+>", "\n", text)
    text = unescape(text)
    text = text.replace("\u3000", " ").replace("\xa0", " ")
    return re.sub(r"\s+", " ", text)


def parse_control_scores() -> list[dict]:
    records = []
    for meta in CONTROL_SOURCES:
        fetched_url, content = fetch_first_available(meta["official_url"], meta["mirror_url"])
        text = html_to_text(content)
        for category_name, pattern in CATEGORY_PATTERNS:
            match = re.search(pattern, text)
            if not match:
                continue
            records.append({
                "province": "henan",
                "year": meta["year"],
                "level": "专升本",
                "institution_code": CONTROL_INSTITUTION["code"],
                "institution_name": CONTROL_INSTITUTION["name"],
                "category_code": None,
                "category_name": category_name,
                "score": int(match.group(1)),
                "line_type": "省控线",
                "round": "录取最低控制分数线",
                "source_url": meta["official_url"],
                "fetch_url": fetched_url,
            })
        print(f"{meta['year']} 省控线: 解析 {sum(1 for r in records if r['year'] == meta['year'])} 条")
    return records


def parse_collection_plan() -> tuple[list[dict], list[dict]]:
    try:
        import pdfplumber
    except ImportError as exc:
        raise SystemExit("解析河南征集志愿 PDF 需要 pdfplumber，请先安装项目依赖。") from exc

    content = fetch_bytes(COLLECTION_PLAN_2025["url"])
    raw_records: list[dict] = []
    with tempfile.NamedTemporaryFile(suffix=".pdf") as tmp:
        tmp.write(content)
        tmp.flush()
        with pdfplumber.open(tmp.name) as pdf:
            for page in pdf.pages:
                for table in page.extract_tables():
                    for row in table[1:]:
                        if len(row) < 7:
                            continue
                        code, name, major_code, major_name, level, plan_count, backup_score = [
                            (cell or "").replace("\n", "").strip() for cell in row[:7]
                        ]
                        if not re.fullmatch(r"\d{3}", code) or level != "专升本":
                            continue
                        category_code = major_code[3:6]
                        category_name = CATEGORY_BY_CODE_PREFIX.get(category_code[:2])
                        raw_records.append({
                            "province": "henan",
                            "year": COLLECTION_PLAN_2025["year"],
                            "level": level,
                            "institution_code": code,
                            "institution_name": name,
                            "major_code": major_code,
                            "major_name": major_name,
                            "category_code": category_code,
                            "category_name": category_name,
                            "plan_count": int(plan_count) if plan_count.isdigit() else None,
                            "backup_score": int(backup_score) if backup_score.isdigit() else None,
                            "line_type": COLLECTION_PLAN_2025["line_type"],
                            "round": COLLECTION_PLAN_2025["round"],
                            "source_url": COLLECTION_PLAN_2025["url"],
                        })

    grouped: dict[tuple[str, str, str, str | None, int | None], dict] = {}
    for rec in raw_records:
        key = (
            rec["institution_code"],
            rec["institution_name"],
            rec["category_code"],
            rec["category_name"],
            rec["backup_score"],
        )
        item = grouped.setdefault(key, {
            "province": rec["province"],
            "year": rec["year"],
            "level": rec["level"],
            "institution_code": rec["institution_code"],
            "institution_name": rec["institution_name"],
            "category_code": rec["category_code"],
            "category_name": rec["category_name"],
            "score": rec["backup_score"],
            "line_type": rec["line_type"],
            "round": rec["round"],
            "source_url": rec["source_url"],
            "majors": [],
        })
        item["majors"].append({
            "major_code": rec["major_code"],
            "major_name": rec["major_name"],
            "plan_count": rec["plan_count"],
        })

    score_records = sorted(
        grouped.values(),
        key=lambda item: (item["institution_code"], item["category_code"] or ""),
    )
    print(f"2025 征集志愿计划: 解析专业 {len(raw_records)} 条，聚合院校科类 {len(score_records)} 条")
    return raw_records, score_records


def run():
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    control_scores = parse_control_scores()
    collection_raw, collection_scores = parse_collection_plan()
    institution_scores = sorted(
        collection_scores,
        key=lambda item: (item["province"], item["institution_code"], item["year"], item["category_name"] or ""),
    )

    outputs = {
        "henan-adult-control-scores.json": control_scores,
        "henan-adult-collection-plan-2025.json": collection_raw,
        "henan-adult-scores.json": institution_scores,
    }
    for filename, data in outputs.items():
        out = OUT_DIR / filename
        out.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
        print(f"写入 {len(data)} 条 → {out}")

    institutions = {(r["institution_code"], r["institution_name"]) for r in institution_scores}
    print(f"院校科类分数 {len(institution_scores)} 条，去重院校 {len(institutions)} 所")


if __name__ == "__main__":
    run()
