"""抓取浙江省教育考试院公布的 2025 年成人高校招生章程专业目录。

官方报名系统中的生源计划数和征求计划需要考生身份登录，无法从公开网页
稳定获取；考试院同时公开了各院校招生章程 PDF，其中包含院校代码、招生
层次、专业和科类。本脚本只把章程中明确列出的专升本专业写入正式目录，
不推测计划人数、专业代码或院校投档线。

输出：scraped-data/zhejiang-adult-program-catalog-2025.json
运行：在 server 目录下执行 ``python -m scripts.scrape_zhejiang_programs``
"""
from __future__ import annotations

import hashlib
import io
import json
import re
import urllib.request
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import urljoin

import pdfplumber


UA = {"User-Agent": "Mozilla/5.0 (compatible; exam-study-hub/1.0)"}
OUT_DIR = Path(__file__).resolve().parent.parent / "scraped-data"
INDEX_SOURCE = {
    "year": 2025,
    "url": "https://www.zjzs.net/art/2025/10/22/art_155_11643.html",
}

CATEGORY_NAME_MAP = {
    "经管": "专升本经管类",
    "经济管理": "专升本经管类",
    "管理": "专升本经管类",
    "药学": "专升本经管类",
    "理工": "专升本理工类",
    "工学": "专升本理工类",
    "法学": "专升本法学类",
    "文史": "专升本文史中医类",
    "文史中医": "专升本文史中医类",
    "中医文史": "专升本文史中医类",
    "文学": "专升本文史中医类",
    "教育": "专升本教育学类",
    "教育学": "专升本教育学类",
    "医学": "专升本医学类",
    "农学": "专升本农学类",
    "艺术": "专升本艺术类",
}

CATEGORY_LABEL = (
    r"(?:经济[、,]?管理|经管|管理|药学|理工|工学|法学|"
    r"文史[、,]?中医|文史中医|中医文史|文史|文学|"
    r"教育学|教育|医学|农学|艺术)类?"
)
CATEGORY_HEADING_RE = re.compile(
    rf"(?P<prefix>专升本)?(?P<label>{CATEGORY_LABEL})\s*[：:]"
)
CATEGORY_PAIR_RE = re.compile(
    rf"(?P<major>[\u4e00-\u9fffA-Za-z0-9]+?)"
    rf"[（(](?P<label>{CATEGORY_LABEL})[）)]"
)
CATEGORY_BLOCK_RE = re.compile(
    rf"(?P<label>{CATEGORY_LABEL})[（(](?P<majors>[^）)]*)[）)]"
)

INSTITUTION_NAME_FIXES = {
    # 考试院索引原文将“义乌”写成了“义务”，章程正文名称正确。
    "义务工商职业技术学院": "义乌工商职业技术学院",
}
MAJOR_NAME_FIXES = {
    "机械设计及其自动化": "机械设计制造及其自动化",
    "视觉传达": "视觉传达设计",
    "环境艺术设计": "环境设计",
}
PROGRAM_OVERRIDES = {
    # 该章程按表演方向展开，没有重复标注“艺术类”标题。
    "123": [
        ("专升本艺术类", "音乐表演"),
        ("专升本艺术类", "音乐学"),
    ],
}


class CharterLinkParser(HTMLParser):
    """提取考试院章程索引中的 PDF 链接和可见名称。"""

    def __init__(self):
        super().__init__()
        self.current_href: str | None = None
        self.current_text: list[str] = []
        self.links: list[tuple[str, str, str]] = []

    def handle_starttag(self, tag: str, attrs):
        if tag.lower() != "a":
            return
        href = dict(attrs).get("href")
        if href and "pdf" in href.lower():
            self.current_href = href
            self.current_text = []

    def handle_data(self, data: str):
        if self.current_href is not None:
            self.current_text.append(data)

    def handle_endtag(self, tag: str):
        if tag.lower() != "a" or self.current_href is None:
            return
        text = re.sub(r"\s+", " ", "".join(self.current_text)).strip()
        match = re.match(r"(\d{3})\s+(.+?)(?:\.pdf)?$", text, flags=re.I)
        if match:
            name = INSTITUTION_NAME_FIXES.get(match.group(2), match.group(2))
            self.links.append((match.group(1), name, self.current_href))
        self.current_href = None
        self.current_text = []


def fetch_bytes(url: str) -> bytes:
    request = urllib.request.Request(url, headers=UA)
    with urllib.request.urlopen(request, timeout=60) as response:
        return response.read()


def parse_charter_links(page: str, base_url: str = INDEX_SOURCE["url"]) -> list[dict]:
    parser = CharterLinkParser()
    parser.feed(page)
    unique = {}
    for code, name, href in parser.links:
        unique[code] = {
            "institution_code": code,
            "institution_name": name,
            "source_url": urljoin(base_url, href),
        }
    return [unique[code] for code in sorted(unique)]


def compact_text(value: str | None) -> str:
    return re.sub(r"\s+", "", value or "")


def extract_charter_fields(pdf_bytes: bytes) -> dict[str, str]:
    """从考试院统一章程表格中提取字段名和值。"""
    fields: dict[str, str] = {}
    with pdfplumber.open(io.BytesIO(pdf_bytes)) as pdf:
        for page in pdf.pages:
            for table in page.extract_tables() or []:
                for row in table:
                    if not row:
                        continue
                    key = compact_text(row[0])
                    value = next((cell for cell in reversed(row[1:]) if cell), None)
                    if key and value:
                        fields[key] = value
    return fields


def field_value(fields: dict[str, str], prefix: str) -> str:
    return next((value for key, value in fields.items() if key.startswith(prefix)), "")


def has_undergraduate_level(level_text: str) -> bool:
    return bool(re.search(r"[☑■√✓]\s*专科起点本科", level_text))


def normalize_category(label: str) -> str | None:
    normalized = re.sub(r"[、,\s]", "", label).removesuffix("类")
    return CATEGORY_NAME_MAP.get(normalized)


def isolate_undergraduate_section(text: str) -> str:
    """在同时列出多个层次时，只保留专升本部分。"""
    compact = compact_text(text)
    start_patterns = [
        r"(?:\d+[、.])?专科起点本科招生专业[：:]?",
        r"(?:\d+[、.])?专科起点本科[：:]?",
        r"专科起点专业[：:]?",
        r"(?:\d+[、.])?专升本[：:]?",
    ]
    starts = []
    for pattern in start_patterns:
        match = re.search(pattern, compact)
        if match:
            starts.append((match.start(), match.end()))
    if not starts:
        return compact

    _, start = min(starts)
    section = compact[start:]
    end_match = re.search(
        r"(?:\d+[、.])?(?:高中起点本科|高中起点专科|高起本|高起专)[：:]?",
        section,
    )
    return section[:end_match.start()] if end_match else section


def clean_major_name(value: str) -> str | None:
    name = re.sub(r"^[（(]?\d+[、.)）]", "", value)
    name = re.sub(r"[（(][^）)]*[）)]", "", name)
    name = name.strip("：:；;，,、。.说明注")
    name = re.sub(r"^(?:专业名称|招生专业)", "", name)
    if not (2 <= len(name) <= 40):
        return None
    if any(word in name for word in ("须参加", "加试", "考生", "报考", "招生计划")):
        return None
    return MAJOR_NAME_FIXES.get(name, name)


def parse_programs(text: str, institution_code: str) -> list[tuple[str, str]]:
    if institution_code in PROGRAM_OVERRIDES:
        return PROGRAM_OVERRIDES[institution_code]

    section = isolate_undergraduate_section(text)
    paired = []
    for match in CATEGORY_PAIR_RE.finditer(section):
        category_name = normalize_category(match.group("label"))
        major_name = clean_major_name(match.group("major"))
        if category_name and major_name:
            paired.append((category_name, major_name))
    if paired:
        return deduplicate_programs(paired)

    parenthesized_blocks = []
    for match in CATEGORY_BLOCK_RE.finditer(section):
        category_name = normalize_category(match.group("label"))
        if category_name is None:
            continue
        for raw_major in re.split(r"[、，,；;。]", match.group("majors")):
            major_name = clean_major_name(raw_major)
            if major_name:
                parenthesized_blocks.append((category_name, major_name))
    if parenthesized_blocks:
        return deduplicate_programs(parenthesized_blocks)

    headings = list(CATEGORY_HEADING_RE.finditer(section))
    programs = []
    for index, heading in enumerate(headings):
        category_name = normalize_category(heading.group("label"))
        if category_name is None:
            continue
        end = headings[index + 1].start() if index + 1 < len(headings) else len(section)
        values = section[heading.end():end]
        values = re.sub(r"[（(][^）)]*[）)]", "", values)
        for raw_major in re.split(r"[、，,；;。]", values):
            major_name = clean_major_name(raw_major)
            if major_name:
                programs.append((category_name, major_name))
    return deduplicate_programs(programs)


def deduplicate_programs(programs: list[tuple[str, str]]) -> list[tuple[str, str]]:
    """同一专业只保留首次出现的官方科类，避免跨层次重复污染。"""
    unique = {}
    for category_name, major_name in programs:
        unique.setdefault(major_name, (category_name, major_name))
    return list(unique.values())


def internal_major_code(category_name: str, major_name: str) -> str:
    """章程未公开报考专业代码；生成明确带 charter 前缀的稳定内部键。"""
    digest = hashlib.sha1(
        f"{category_name}|{major_name}".encode("utf-8")
    ).hexdigest()[:10]
    return f"charter-{digest}"


def parse_charter(pdf_bytes: bytes, meta: dict) -> list[dict]:
    fields = extract_charter_fields(pdf_bytes)
    level_text = field_value(fields, "五、层次")
    if not has_undergraduate_level(level_text):
        return []

    institution_code = compact_text(field_value(fields, "二、浙江省院校代码"))
    institution_name = compact_text(field_value(fields, "一、院校全称"))
    if institution_code != meta["institution_code"]:
        raise RuntimeError(
            f"章程代码不一致：索引 {meta['institution_code']}，PDF {institution_code or '空'}"
        )
    if not institution_name:
        institution_name = meta["institution_name"]

    program_text = field_value(fields, "八、招生专业")
    programs = parse_programs(program_text, institution_code)
    if not programs:
        raise RuntimeError(f"{institution_code} {institution_name} 未解析到专升本专业")

    return [
        {
            "province": "zhejiang",
            "year": INDEX_SOURCE["year"],
            "level": "专升本",
            "institution_code": institution_code,
            "institution_name": institution_name,
            "major_code": internal_major_code(category_name, major_name),
            "major_name": major_name,
            "category_code": None,
            "category_name": category_name,
            "plan_count": None,
            "line_type": "招生专业目录",
            "round": "2025招生章程",
            "source_url": meta["source_url"],
        }
        for category_name, major_name in programs
    ]


def run() -> None:
    page = fetch_bytes(INDEX_SOURCE["url"]).decode("utf-8")
    charters = parse_charter_links(page)
    if len(charters) != 92:
        raise RuntimeError(f"官方章程索引应有 92 所院校，实际解析 {len(charters)} 所")

    records = []
    undergraduate_institutions = 0
    for index, meta in enumerate(charters, start=1):
        pdf_bytes = fetch_bytes(meta["source_url"])
        if not pdf_bytes.startswith(b"%PDF"):
            raise RuntimeError(f"{meta['institution_code']} 下载内容不是 PDF")
        yearly_records = parse_charter(pdf_bytes, meta)
        if yearly_records:
            undergraduate_institutions += 1
            records.extend(yearly_records)
        print(
            f"[{index:02d}/{len(charters)}] {meta['institution_code']} "
            f"{meta['institution_name']}：{len(yearly_records)} 条"
        )

    records.sort(
        key=lambda item: (
            item["institution_code"], item["category_name"], item["major_name"]
        )
    )
    output = OUT_DIR / "zhejiang-adult-program-catalog-2025.json"
    output.write_text(json.dumps(records, ensure_ascii=False, indent=2), encoding="utf-8")
    print(
        f"写入 {len(records)} 条、{undergraduate_institutions} 所专升本院校 → {output}"
    )


if __name__ == "__main__":
    run()
