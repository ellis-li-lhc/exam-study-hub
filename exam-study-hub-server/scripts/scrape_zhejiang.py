"""抓取并解析浙江省成人高校招生专升本录取最低控制分数线。

数据来源：浙江省教育考试院（www.zjzs.net）公开的年度分数线页面。
输出：scraped-data/zhejiang-adult-control-scores.json。
用法：在 server 目录下运行 `python -m scripts.scrape_zhejiang`。

浙江省考试院公开页面目前只提供省控线；院校专业生源计划和征求计划需登录
成人高校招生报名系统查询，因此本脚本不抓取、也不推测院校投档线或专业计划。
"""
from __future__ import annotations

import json
import re
import urllib.request
from html.parser import HTMLParser
from pathlib import Path


UA = {"User-Agent": "Mozilla/5.0"}
OUT_DIR = Path(__file__).resolve().parent.parent / "scraped-data"

CONTROL_SOURCES = [
    {
        "year": 2025,
        "url": "https://www.zjzs.net/art/2025/11/20/art_53_11730.html",
    },
    {
        "year": 2024,
        "url": "https://www.zjzs.net/art/2024/11/19/art_53_10344.html",
    },
    {
        "year": 2023,
        "url": "https://www.zjzs.net/art/2023/11/17/art_53_5973.html",
    },
    {
        "year": 2022,
        "url": "https://www.zjzs.net/art/2022/11/25/art_53_5031.html",
    },
    {
        "year": 2021,
        "url": "https://www.zjzs.net/art/2021/11/24/art_53_5964.html",
    },
    {
        "year": 2020,
        "url": "https://www.zjzs.net/art/2020/11/23/art_53_5986.html",
    },
    {
        "year": 2019,
        "url": "https://www.zjzs.net/art/2019/11/21/art_53_5983.html",
    },
    {
        "year": 2018,
        "url": "https://www.zjzs.net/art/2018/11/22/art_155_8386.html",
    },
]

CATEGORY_NAME_MAP = {
    "文史、中医": "专升本文史中医类",
    "艺术": "专升本艺术类",
    "理工": "专升本理工类",
    "经济、管理": "专升本经管类",
    "法学": "专升本法学类",
    "教育学": "专升本教育学类",
    "农学": "专升本农学类",
    "医学": "专升本医学类",
}


class TableRowParser(HTMLParser):
    """提取 HTML 表格中的单元格纯文本。"""

    def __init__(self):
        super().__init__()
        self.rows: list[list[str]] = []
        self.current_row: list[str] | None = None
        self.current_cell: list[str] | None = None

    def handle_starttag(self, tag: str, attrs):
        if tag.lower() == "tr":
            self.current_row = []
        elif tag.lower() in {"td", "th"} and self.current_row is not None:
            self.current_cell = []

    def handle_data(self, data: str):
        if self.current_cell is not None:
            self.current_cell.append(data)

    def handle_endtag(self, tag: str):
        normalized_tag = tag.lower()
        if normalized_tag in {"td", "th"} and self.current_cell is not None:
            text = re.sub(r"\s+", "", "".join(self.current_cell))
            self.current_row.append(text)
            self.current_cell = None
        elif normalized_tag == "tr" and self.current_row is not None:
            if self.current_row:
                self.rows.append(self.current_row)
            self.current_row = None


def fetch_html(url: str) -> str:
    request = urllib.request.Request(url, headers=UA)
    with urllib.request.urlopen(request, timeout=40) as response:
        return response.read().decode("utf-8")


def parse_control_scores(html: str, meta: dict) -> list[dict]:
    parser = TableRowParser()
    parser.feed(html)

    score_by_category: dict[str, int] = {}
    for row in parser.rows:
        if len(row) < 2:
            continue
        source_category = row[0].replace("，", "、")
        source_category = source_category.replace(",", "、")
        category_name = CATEGORY_NAME_MAP.get(source_category)
        if category_name is None or not re.fullmatch(r"\d{2,3}", row[1]):
            continue
        score_by_category[category_name] = int(row[1])

    missing = set(CATEGORY_NAME_MAP.values()) - set(score_by_category)
    if missing:
        raise RuntimeError(f"{meta['year']} 浙江专升本省控线缺少科类：{sorted(missing)}")

    return [
        {
            "province": "zhejiang",
            "year": meta["year"],
            "level": "专升本",
            "institution_code": "zhejiang-control-line",
            "institution_name": "浙江省成人高校招生省控线（参考）",
            "category_code": None,
            "category_name": category_name,
            "score": score_by_category[category_name],
            "line_type": "省控线",
            "round": "录取最低控制分数线",
            "source_url": meta["url"],
            "fetch_url": meta["url"],
        }
        for category_name in CATEGORY_NAME_MAP.values()
    ]


def run():
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    records = []
    for meta in CONTROL_SOURCES:
        yearly_records = parse_control_scores(fetch_html(meta["url"]), meta)
        records.extend(yearly_records)
        print(f"{meta['year']} 浙江专升本省控线：解析 {len(yearly_records)} 条")

    output = OUT_DIR / "zhejiang-adult-control-scores.json"
    output.write_text(json.dumps(records, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"写入 {len(records)} 条 → {output}")


if __name__ == "__main__":
    run()
