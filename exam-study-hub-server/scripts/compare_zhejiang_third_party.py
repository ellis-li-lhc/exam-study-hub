"""抓取两家第三方浙江成考专业目录，并用官方院校备案清单交叉核验。

输出文件只用于候选数据核验，不会被 seed.py 导入数据库：

* scraped-data/third-party/zhejiang-zj-ck-candidates.json
* scraped-data/third-party/zhejiang-zjck-org-candidates.json
* scraped-data/third-party/zhejiang-comparison-report.json

两家站点当前展示的快照年份分别为 2024 和 2026，因此不能冒充 2025 招生计划。
脚本保留来源标识、抓取时间和原始名称，并用浙江省教育考试院 2025 年成人高校
招生章程索引核验省内院校代码/名称。
"""
from __future__ import annotations

import datetime as dt
import html
import json
import re
import urllib.request
from html.parser import HTMLParser
from pathlib import Path


UA = {"User-Agent": "Mozilla/5.0 (compatible; exam-study-data-audit/1.0)"}
OUT_DIR = Path(__file__).resolve().parent.parent / "scraped-data" / "third-party"

SOURCE_A = {
    "key": "zj-ck.com",
    "snapshot_year": 2024,
    "url": "https://www.zj-ck.com/ckzy/",
}
SOURCE_B = {
    "key": "zjck.org.cn",
    "snapshot_year": 2026,
    "url": "https://www.zjck.org.cn/zhuanye/",
}
SOURCE_B_QUALITY_PROBE = "https://www.zjck.org.cn/zhuanye/major-b9a50c22/"
OFFICIAL_SOURCE = {
    "year": 2025,
    "url": "https://www.zjzs.net/art/2025/10/22/art_155_11643.html",
}
OFFICIAL_PROGRAM_SAMPLE = {
    "institution_code": "450",
    "institution_name": "浙江理工大学",
    "year": 2025,
    "url": "https://cj.zstu.edu.cn/info/1033/3591.htm",
}

INSTITUTION_ALIASES = {
    "嘉兴学院": "嘉兴大学",
    "浙江树人大学": "浙江树人学院",
    "宁波理工学院": "浙大宁波理工学院",
    "宁波职业技术学院": "宁波职业技术大学",
    "金华职业技术学院": "金华职业技术大学",
    "浙江机电职业技术学院": "浙江机电职业技术大学",
    "浙江科技学院": "浙江科技大学",
}
LEVEL_MAP = {
    "高升专": "高职（专科）",
    "高起专": "高职（专科）",
    "专升本": "专升本",
    "高升本": "高中起点本科",
    "高起本": "高中起点本科",
}


def fetch_html(url: str) -> str:
    request = urllib.request.Request(url, headers=UA)
    with urllib.request.urlopen(request, timeout=45) as response:
        charset = response.headers.get_content_charset() or "utf-8"
        return response.read().decode(charset, errors="replace")


def strip_tags(fragment: str) -> str:
    return re.sub(r"\s+", " ", html.unescape(re.sub(r"<[^>]+>", "", fragment))).strip()


class TableCellParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.depth = 0
        self.buffer: list[str] = []
        self.cells: list[str] = []

    def handle_starttag(self, tag: str, attrs):
        if tag.lower() == "td":
            self.depth += 1
            self.buffer = []

    def handle_data(self, data: str):
        if self.depth:
            self.buffer.append(data)

    def handle_endtag(self, tag: str):
        if tag.lower() == "td" and self.depth:
            self.cells.append(re.sub(r"\s+", "", "".join(self.buffer)))
            self.depth -= 1


def parse_official_program_sample(page: str) -> set[tuple[str, str]]:
    """解析浙江理工大学官网 2025 表格，返回去重后的（层次，专业）集合。"""
    parser = TableCellParser()
    parser.feed(page)
    cells = parser.cells
    if cells[:9] != [
        "层次", "学习形式", "学制", "教学点", "专业名称", "学校代码",
        "专业代码", "科类名称", "备注",
    ]:
        raise RuntimeError("浙江理工大学官网专业表结构已变化")
    rows = [cells[index:index + 9] for index in range(9, len(cells), 9)]
    return {
        (LEVEL_MAP.get(row[0], row[0]), normalize_major(row[4]))
        for row in rows
        if len(row) == 9 and row[5] == OFFICIAL_PROGRAM_SAMPLE["institution_code"]
    }


def normalize_institution(name: str) -> str:
    normalized = re.sub(r"\s+", "", name)
    return INSTITUTION_ALIASES.get(normalized, normalized)


def normalize_major(name: str) -> str:
    normalized = re.sub(r"\s+", "", name)
    normalized = re.sub(r"^浙江(?=[\u4e00-\u9fff])", "", normalized)
    normalized = re.sub(r"专业$", "", normalized)
    return normalized


def parse_official_institutions(page: str) -> dict[str, str]:
    text = strip_tags(page)
    pairs = re.findall(r"(?<!\d)(\d{3})\s+([^\d]{2,40}?)\.pdf", text, flags=re.I)
    institutions = {}
    for code, name in pairs:
        cleaned = normalize_institution(name.strip(" /|"))
        if cleaned:
            institutions[code] = cleaned
    return dict(sorted(institutions.items()))


def parse_source_a(page: str, official_name_to_code: dict[str, str]) -> list[dict]:
    records = []
    tables = re.findall(
        r'<table\s+class="zytable1".*?</table>', page, flags=re.I | re.S
    )
    for table in tables:
        institution_match = re.search(
            r'<a[^>]+class="xxmc"[^>]*>(.*?)</a>', table, flags=re.I | re.S
        )
        if institution_match is None:
            continue
        raw_institution = strip_tags(institution_match.group(1))
        institution = normalize_institution(raw_institution)
        code = official_name_to_code.get(institution)

        for row in re.findall(r"<tr.*?</tr>", table, flags=re.I | re.S):
            level_match = re.search(
                r'<td[^>]+class="cengcin"[^>]*>(.*?)</td>', row, flags=re.I | re.S
            )
            majors_match = re.search(
                r'<td[^>]+class="czhuanye"[^>]*>(.*?)</td>', row, flags=re.I | re.S
            )
            if level_match is None or majors_match is None:
                continue
            raw_level = strip_tags(level_match.group(1))
            level = LEVEL_MAP.get(raw_level, raw_level)
            raw_majors = [
                strip_tags(value)
                for value in re.findall(r"<a[^>]*>(.*?)</a>", majors_match.group(1), re.I | re.S)
            ]
            for raw_major in filter(None, raw_majors):
                records.append(
                    {
                        "province": "zhejiang",
                        "year": SOURCE_A["snapshot_year"],
                        "level": level,
                        "institution_code": code,
                        "institution_name": institution,
                        "major_code": None,
                        "major_name": normalize_major(raw_major),
                        "category_code": None,
                        "category_name": None,
                        "plan_count": None,
                        "line_type": "第三方专业目录候选",
                        "round": None,
                        "source_url": SOURCE_A["url"],
                        "source_key": SOURCE_A["key"],
                        "source_institution_name": raw_institution,
                        "source_major_name": raw_major,
                        "official_institution_match": code is not None,
                    }
                )
    return records


def parse_source_b(page: str, official_institutions: dict[str, str]) -> list[dict]:
    blocks = re.findall(
        r'<script[^>]+type="application/ld\+json"[^>]*>(.*?)</script>',
        page,
        flags=re.I | re.S,
    )
    payload = next(
        (json.loads(html.unescape(block)) for block in blocks if '"itemListElement"' in block),
        None,
    )
    if payload is None:
        raise RuntimeError("第二个第三方页面没有找到专业 ItemList JSON-LD")

    records = []
    for element in payload.get("itemListElement", []):
        item = element.get("item", {})
        raw_major = str(item.get("name", "")).strip()
        description = str(item.get("description", ""))
        levels_text = description.split("|", 1)[0]
        levels = [part.strip() for part in re.split(r"[、,，]", levels_text) if part.strip()]
        provider = item.get("provider", {})
        codes = re.findall(r"(?<!\d)\d{3}(?!\d)", str(provider.get("name", "")))
        for code in codes:
            institution = official_institutions.get(code)
            for raw_level in levels:
                records.append(
                    {
                        "province": "zhejiang",
                        "year": SOURCE_B["snapshot_year"],
                        "level": LEVEL_MAP.get(raw_level, raw_level),
                        "institution_code": code,
                        "institution_name": institution,
                        "major_code": None,
                        "major_name": normalize_major(raw_major),
                        "category_code": None,
                        "category_name": None,
                        "plan_count": None,
                        "line_type": "第三方专业目录候选",
                        "round": None,
                        "source_url": item.get("url") or SOURCE_B["url"],
                        "source_key": SOURCE_B["key"],
                        "source_major_name": raw_major,
                        "official_institution_match": institution is not None,
                    }
                )
    return records


def record_key(record: dict) -> tuple[str, str, str]:
    institution_key = record.get("institution_code") or record.get("institution_name") or ""
    return institution_key, record["level"], record["major_name"]


def deduplicate_records(records: list[dict]) -> list[dict]:
    unique = {}
    for record in records:
        unique.setdefault(record_key(record), record)
    return list(unique.values())


def inspect_source_b_quality(page: str) -> dict:
    text = strip_tags(page)
    claimed_match = re.search(r"(\d+)所院校在浙江招收该专业", text)
    displayed_match = re.search(r"招生院校\s*(\d+)所", text)
    return {
        "probe_major": "计算机科学与技术",
        "probe_url": SOURCE_B_QUALITY_PROBE,
        "claimed_institution_count": int(claimed_match.group(1)) if claimed_match else None,
        "displayed_institution_count": int(displayed_match.group(1)) if displayed_match else None,
        "structured_course_instances_empty": '"hasCourseInstance":[]' in page,
    }


def build_report(
    official_institutions: dict[str, str],
    official_program_sample: set[tuple[str, str]],
    source_a: list[dict],
    source_b: list[dict],
    source_b_quality: dict,
) -> dict:
    a_keys = {record_key(record) for record in source_a}
    b_local = [record for record in source_b if record["official_institution_match"]]
    b_keys = {record_key(record) for record in b_local}
    overlap = a_keys & b_keys

    a_institutions = {record["institution_name"] for record in source_a}
    a_matched = {record["institution_name"] for record in source_a if record["official_institution_match"]}
    b_codes = {record["institution_code"] for record in source_b}
    b_matched_codes = b_codes & set(official_institutions)

    sample_code = OFFICIAL_PROGRAM_SAMPLE["institution_code"]
    a_sample = {
        (record["level"], record["major_name"])
        for record in source_a
        if record["institution_code"] == sample_code
    }
    b_sample = {
        (record["level"], record["major_name"])
        for record in source_b
        if record["institution_code"] == sample_code
    }

    def sample_metrics(candidates: set[tuple[str, str]]) -> dict:
        matches = candidates & official_program_sample
        return {
            "candidate_pair_count": len(candidates),
            "official_match_count": len(matches),
            "precision": round(len(matches) / len(candidates), 4) if candidates else None,
            "recall": round(len(matches) / len(official_program_sample), 4)
            if official_program_sample else None,
            "false_positive_pairs": [
                {"level": level, "major_name": major}
                for level, major in sorted(candidates - official_program_sample)
            ],
            "missing_official_pairs": [
                {"level": level, "major_name": major}
                for level, major in sorted(official_program_sample - candidates)
            ],
        }

    return {
        "generated_at": dt.datetime.now(dt.timezone.utc).isoformat(),
        "scope": "浙江成人高考院校-层次-专业候选目录",
        "warning": "两家第三方快照年份不同，结果不得直接作为2025招生计划入库。",
        "official_baseline": {
            "year": OFFICIAL_SOURCE["year"],
            "source_url": OFFICIAL_SOURCE["url"],
            "institution_count": len(official_institutions),
        },
        "sources": {
            SOURCE_A["key"]: {
                "snapshot_year": SOURCE_A["snapshot_year"],
                "source_url": SOURCE_A["url"],
                "record_count": len(source_a),
                "institution_count": len(a_institutions),
                "official_institution_match_count": len(a_matched),
                "official_institution_name_precision": round(
                    len(a_matched) / len(a_institutions), 4
                ) if a_institutions else None,
                "official_2025_institution_coverage": round(
                    len(a_matched) / len(official_institutions), 4
                ) if official_institutions else None,
                "unmatched_institutions": sorted(a_institutions - a_matched),
            },
            SOURCE_B["key"]: {
                "snapshot_year": SOURCE_B["snapshot_year"],
                "source_url": SOURCE_B["url"],
                "record_count": len(source_b),
                "provider_code_count": len(b_codes),
                "official_local_provider_match_count": len(b_matched_codes),
                "official_2025_local_institution_coverage": round(
                    len(b_matched_codes) / len(official_institutions), 4
                ) if official_institutions else None,
                "note": "目录页结构化数据仅展示部分院校代码；未匹配代码也可能是省外招生院校，因此不能据此计算误报率。",
                "quality_probe": source_b_quality,
            },
        },
        "cross_source": {
            "source_a_unique_pairs": len(a_keys),
            "source_b_official_local_unique_pairs": len(b_keys),
            "agreed_pairs": len(overlap),
            "source_a_pair_agreement_rate": round(len(overlap) / len(a_keys), 4)
            if a_keys else None,
            "source_b_local_pair_agreement_rate": round(len(overlap) / len(b_keys), 4)
            if b_keys else None,
            "agreed_pair_sample": [
                {"institution_code": code, "level": level, "major_name": major}
                for code, level, major in sorted(overlap)[:50]
            ],
            "interpretation": "一致率仅表示两站相互印证，不等同于相对官方的专业准确率。",
        },
        "official_program_sample_check": {
            "institution_code": sample_code,
            "institution_name": OFFICIAL_PROGRAM_SAMPLE["institution_name"],
            "year": OFFICIAL_PROGRAM_SAMPLE["year"],
            "source_url": OFFICIAL_PROGRAM_SAMPLE["url"],
            "official_unique_pair_count": len(official_program_sample),
            SOURCE_A["key"]: sample_metrics(a_sample),
            SOURCE_B["key"]: sample_metrics(b_sample),
            "interpretation": "这是单校完整表抽样结果，不能外推为全省专业准确率。",
        },
        "import_recommendation": "quarantine",
    }


def write_json(name: str, payload) -> None:
    path = OUT_DIR / name
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"写入 {path} ({len(payload) if isinstance(payload, list) else 'report'})")


def run() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    official_institutions = parse_official_institutions(fetch_html(OFFICIAL_SOURCE["url"]))
    if len(official_institutions) < 80:
        raise RuntimeError(f"官方院校清单只解析到 {len(official_institutions)} 所，拒绝继续")
    official_name_to_code = {name: code for code, name in official_institutions.items()}
    official_program_sample = parse_official_program_sample(
        fetch_html(OFFICIAL_PROGRAM_SAMPLE["url"])
    )
    if len(official_program_sample) < 5:
        raise RuntimeError("浙江理工大学官网专业样本解析结果异常")

    source_a = deduplicate_records(
        parse_source_a(fetch_html(SOURCE_A["url"]), official_name_to_code)
    )
    source_b = deduplicate_records(
        parse_source_b(fetch_html(SOURCE_B["url"]), official_institutions)
    )
    source_b_quality = inspect_source_b_quality(fetch_html(SOURCE_B_QUALITY_PROBE))
    report = build_report(
        official_institutions,
        official_program_sample,
        source_a,
        source_b,
        source_b_quality,
    )

    write_json("zhejiang-zj-ck-candidates.json", source_a)
    write_json("zhejiang-zjck-org-candidates.json", source_b)
    write_json("zhejiang-comparison-report.json", report)


if __name__ == "__main__":
    run()
