"""抓取并解析广东省 2025 年成人高考专升本公开数据。

官方来源：广东省教育考试院。
- 第一批专科起点本科招生专业计划；
- 第一批专科起点本科层次院校第一志愿投档情况；
- 各类成人高校招生录取最低分数线。

输出：
- scraped-data/guangdong-adult-program-plan-2025.json
- scraped-data/guangdong-adult-scores.json
- scraped-data/guangdong-adult-control-scores.json

运行：在 server 目录执行 ``python -m scripts.scrape_guangdong``。
"""
from __future__ import annotations

import json
import re
import tempfile
import urllib.request
from html import unescape
from pathlib import Path


UA = {"User-Agent": "Mozilla/5.0", "Referer": "https://eea.gd.gov.cn/"}
OUT_DIR = Path(__file__).resolve().parent.parent / "scraped-data"

PLAN_SOURCE = {
    "year": 2025,
    "official_url": "https://eea.gd.gov.cn/attachment/0/598/598444/4800934.pdf",
    # 省考试院附件偶尔会拒绝直连，佛山市教育局保留了同一份官方附件。
    "mirror_url": "https://edu.foshan.gov.cn/attachment/0/576/576329/6898223.pdf",
}
SCORE_SOURCE = {
    "year": 2025,
    "official_url": "https://eea.gd.gov.cn/attachment/0/600/600480/4810290.pdf",
    "mirror_url": "https://imgbdb4.bendibao.com/szbdb/edu/202512/08/20251208193520_12550.pdf",
}
CONTROL_SOURCE = {
    "year": 2025,
    "official_url": "https://eea.gd.gov.cn/tzgg/content/post_4801603.html",
}

EXPECTED_PLAN_COUNT = 746
EXPECTED_SCORE_COUNT = 199
EXPECTED_INSTITUTION_COUNT = 79

# 广东把理工和经管专业放在同一个 103 科目组，不能把它误标为单独的理工类。
GROUP_TO_CATEGORY = {
    "101": "专升本文史中医类",
    "102": "专升本艺术类",
    "103": "专升本理工经管类",
    "104": "专升本法学类",
    "105": "专升本教育学类",
    "106": "专升本农学类",
    "107": "专升本医学类",
}


def fetch_bytes(url: str) -> bytes:
    request = urllib.request.Request(url, headers=UA)
    with urllib.request.urlopen(request, timeout=60) as response:
        return response.read()


def fetch_first_available(*urls: str) -> tuple[str, bytes]:
    errors = []
    for url in urls:
        try:
            return url, fetch_bytes(url)
        except (OSError, TimeoutError) as exc:
            errors.append(f"{url}: {exc}")
    raise RuntimeError("所有来源均无法访问：\n" + "\n".join(errors))


def _pdf_tables(content: bytes):
    try:
        import pdfplumber
    except ImportError as exc:
        raise SystemExit("解析广东 PDF 需要 pdfplumber，请先安装项目依赖。") from exc

    with tempfile.NamedTemporaryFile(suffix=".pdf") as tmp:
        tmp.write(content)
        tmp.flush()
        with pdfplumber.open(tmp.name) as pdf:
            for page in pdf.pages:
                # 官方 PDF 的斜向水印字号约 76pt；正文最大 12pt。先过滤水印再抽表，
                # 否则“广东省教育考试院”会被拆散后混入院校名和专业代码。
                clean_page = page.filter(
                    lambda obj: obj.get("object_type") != "char" or obj.get("size", 0) < 20
                )
                yield from clean_page.extract_tables()


def _clean_row(row) -> list[str]:
    return [re.sub(r"\s+", "", cell or "") for cell in row]


def parse_plan_pdf(content: bytes) -> list[dict]:
    records = []
    for table in _pdf_tables(content):
        for raw_row in table:
            row = _clean_row(raw_row)
            if len(row) < 8 or not re.fullmatch(r"\d{5}", row[0]):
                continue
            institution_code, institution_name, source_category = row[:3]
            major_code, major_name, study_form, group_code, plan_count = row[3:8]
            if not re.fullmatch(r"\d{6}", major_code) or group_code not in GROUP_TO_CATEGORY:
                continue
            if study_form != "非脱产" or not plan_count.isdigit():
                raise RuntimeError(f"广东招生计划出现无法识别的数据行：{row}")
            records.append({
                "province": "guangdong",
                "year": PLAN_SOURCE["year"],
                "level": "专升本",
                "institution_code": institution_code,
                "institution_name": institution_name,
                "major_code": major_code,
                "major_name": major_name,
                "category_code": group_code,
                "category_name": GROUP_TO_CATEGORY[group_code],
                "plan_count": int(plan_count),
                "line_type": "招生专业计划",
                "round": "第一批专科起点本科",
                "study_form": study_form,
                "source_category_name": source_category,
                "source_url": PLAN_SOURCE["official_url"],
            })

    institutions = {(item["institution_code"], item["institution_name"]) for item in records}
    if len(records) != EXPECTED_PLAN_COUNT or len(institutions) != EXPECTED_INSTITUTION_COUNT:
        raise RuntimeError(
            f"广东招生计划数量异常：专业 {len(records)} 条、院校 {len(institutions)} 所，"
            f"预期 {EXPECTED_PLAN_COUNT} 条、{EXPECTED_INSTITUTION_COUNT} 所"
        )
    return records


def parse_score_pdf(content: bytes) -> list[dict]:
    records = []
    for table in _pdf_tables(content):
        for raw_row in table:
            row = _clean_row(raw_row)
            if len(row) < 7 or not re.fullmatch(r"\d{5}", row[0]):
                continue
            institution_code, institution_name, property_code, source_category = row[:4]
            plan_count, submitted_count, score = row[4:7]
            group_code = property_code[-3:]
            if not re.fullmatch(r"\d{5}", property_code) or group_code not in GROUP_TO_CATEGORY:
                continue
            if not all(value.isdigit() for value in (plan_count, submitted_count, score)):
                raise RuntimeError(f"广东投档线出现无法识别的数据行：{row}")
            records.append({
                "province": "guangdong",
                "year": SCORE_SOURCE["year"],
                "level": "专升本",
                "institution_code": institution_code,
                "institution_name": institution_name,
                "category_code": property_code,
                "category_name": GROUP_TO_CATEGORY[group_code],
                "score": int(score),
                "line_type": "院校投档线",
                "round": "第一志愿",
                "source_category_name": source_category,
                "source_plan_count": int(plan_count),
                "submitted_count": int(submitted_count),
                "source_url": SCORE_SOURCE["official_url"],
            })

    institutions = {(item["institution_code"], item["institution_name"]) for item in records}
    if len(records) != EXPECTED_SCORE_COUNT or len(institutions) != EXPECTED_INSTITUTION_COUNT:
        raise RuntimeError(
            f"广东投档线数量异常：记录 {len(records)} 条、院校 {len(institutions)} 所，"
            f"预期 {EXPECTED_SCORE_COUNT} 条、{EXPECTED_INSTITUTION_COUNT} 所"
        )
    return records


def html_to_text(content: bytes) -> str:
    text = content.decode("utf-8", errors="ignore")
    text = re.sub(r"<script[\s\S]*?</script>", "", text, flags=re.I)
    text = re.sub(r"<style[\s\S]*?</style>", "", text, flags=re.I)
    text = unescape(re.sub(r"<[^>]+>", " ", text))
    text = re.sub(r"\s+", " ", text)
    # 页面正文为适配移动端，把三位分数拆成了“1 2 0”。
    return re.sub(r"(?<=\d)\s+(?=\d)", "", text)


def parse_control_scores(content: bytes) -> list[dict]:
    text = html_to_text(content)
    section = text[text.find("专科升本科"):text.find("高中起点本科")]
    patterns = {
        "文法教育医农": r"文史、中医类.*?农学类\s*[：:]\s*(\d+)\s*分",
        "艺术体育": r"艺术类\s*[，,]\s*体育类\s*[：:]\s*(\d+)\s*分",
        "理工经管": r"理工、经管类\s*[：:]\s*(\d+)\s*分",
    }
    scores = {}
    for key, pattern in patterns.items():
        match = re.search(pattern, section)
        if match is None:
            raise RuntimeError(f"广东 2025 省控线页面缺少 {key} 分数")
        scores[key] = int(match.group(1))

    categories = [
        ("101", "专升本文史中医类", scores["文法教育医农"]),
        ("104", "专升本法学类", scores["文法教育医农"]),
        ("105", "专升本教育学类", scores["文法教育医农"]),
        ("107", "专升本医学类", scores["文法教育医农"]),
        ("106", "专升本农学类", scores["文法教育医农"]),
        ("102", "专升本艺术类", scores["艺术体育"]),
        ("sports", "专升本体育类", scores["艺术体育"]),
        ("103-science", "专升本理工类", scores["理工经管"]),
        ("103-management", "专升本经管类", scores["理工经管"]),
    ]
    return [{
        "province": "guangdong",
        "year": CONTROL_SOURCE["year"],
        "level": "专升本",
        "institution_code": "guangdong-control-line",
        "institution_name": "广东省成人高校招生省控线（参考）",
        "category_code": category_code,
        "category_name": category_name,
        "score": score,
        "line_type": "省控线",
        "round": "录取最低控制分数线",
        "source_url": CONTROL_SOURCE["official_url"],
        "fetch_url": CONTROL_SOURCE["official_url"],
    } for category_code, category_name, score in categories]


def run():
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    plan_fetch_url, plan_content = fetch_first_available(
        PLAN_SOURCE["official_url"], PLAN_SOURCE["mirror_url"]
    )
    score_fetch_url, score_content = fetch_first_available(
        SCORE_SOURCE["official_url"], SCORE_SOURCE["mirror_url"]
    )
    control_content = fetch_bytes(CONTROL_SOURCE["official_url"])

    plans = parse_plan_pdf(plan_content)
    scores = parse_score_pdf(score_content)
    controls = parse_control_scores(control_content)
    outputs = {
        "guangdong-adult-program-plan-2025.json": plans,
        "guangdong-adult-scores.json": scores,
        "guangdong-adult-control-scores.json": controls,
    }
    for filename, records in outputs.items():
        output = OUT_DIR / filename
        output.write_text(json.dumps(records, ensure_ascii=False, indent=2), encoding="utf-8")
        print(f"写入 {len(records)} 条 → {output}")

    print(
        f"广东 2025：专业计划 {len(plans)} 条，院校投档线 {len(scores)} 条，"
        f"省控线 {len(controls)} 条；计划下载源 {plan_fetch_url}；投档线下载源 {score_fetch_url}"
    )


if __name__ == "__main__":
    run()
