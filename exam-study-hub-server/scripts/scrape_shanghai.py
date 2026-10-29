"""Fetch official Shanghai adult 专升本 catalogs and control lines.

Run: python -m scripts.scrape_shanghai (cached sources); add --refresh to refetch.
All PDF rows, teaching-point references and school totals are checked before writing.
"""
import argparse
from collections import Counter
from datetime import datetime, timezone
import hashlib
from html.parser import HTMLParser
import json
from pathlib import Path
import re
from urllib.request import Request, urlopen

import pdfplumber

DATA = Path(__file__).resolve().parent.parent / "scraped-data"
SOURCES = [
    ("plan-2025.pdf", "https://www.shmeea.edu.cn/download/20251117/01.pdf", 2025, "主批次", "招生计划"),
    ("collection-2025.pdf", "https://www.shmeea.edu.cn/download/20251209/02.pdf", 2025, "征求志愿", "征求计划"),
    ("catalog-2026.pdf", "https://www.shmeea.edu.cn/resource/upload/www/202608/27143612fgxg.pdf", 2026, "招生专业目录", "招生专业目录"),
]
CONTROLS = {
    2023: "https://www.shmeea.edu.cn/page/08000/20231124/17990.html",
    2024: "https://www.shmeea.edu.cn/page/05200/20241119/18902.html",
    2025: "https://www.shmeea.edu.cn/page/08000/20251117/19852.html",
}
CATEGORIES = ["文史、中医类", "艺术类", "理工类", "经济管理类", "法学类", "教育学类", "农学类", "医学类"]
# School headquarters, separate from the Shanghai teaching points in each plan.
OUTSIDE_CITIES = {
    "976": "北京", "979": "南京", "980": "西安", "981": "长沙", "982": "镇江",
    "987": "青岛", "988": "武汉", "989": "武汉", "990": "雅安", "991": "大连",
    "992": "西安", "993": "南昌", "994": "大连",
}


def compact(value):
    return re.sub(r"\s+", "", value or "")


def tuition_fields(raw):
    """Integer annual amounts only; fractional credit charges stay exact in raw text."""
    match = re.fullmatch(r"(\d+)元/(?:学年|年)", raw)
    return {"tuition_raw": raw, "tuition_amount": int(match[1]) if match else None,
            "tuition_unit": "per_academic_year" if match else "per_credit" if "元/学分" in raw else None}


def institution_name(raw):
    # Parenthesized university qualifiers are names; the following parentheses are addresses.
    match = re.match(r"(.+?(?:大学|学院)(?:\((?:华东|武汉)\))?)", raw)
    if not match:
        raise ValueError(f"Unknown institution name: {raw}")
    return match[1]


def parse_catalog(path, year, round_name, line_type, source_url):
    plans, totals, sites = [], {}, {}
    school_code = school_name = None
    need_school = True
    with pdfplumber.open(path) as pdf:
        for page_number, original in enumerate(pdf.pages, 1):
            # The collection PDF has 50.9pt KaiTi watermark characters across cells.
            page = original.filter(lambda obj: obj["object_type"] != "char" or obj["size"] < 30)
            tables = page.find_tables()
            if len(tables) != 1:
                raise ValueError(f"Expected one complete table on {path.name} page {page_number}")
            table = tables[0]
            for row_index, raw in enumerate(table.extract()):
                row = [compact(value) for value in raw]
                if row[0] == "院校代码":
                    continue
                if row[2].startswith("教学点名称及地点："):
                    if not school_code:
                        raise ValueError("Teaching points without institution")
                    sites[school_code] = dict(re.findall(r"(?:^|[;；])(\d+)\.(.*?)(?=;\d+\.|；\d+\.|$)", row[2].split("：", 1)[1]))
                    if not sites[school_code]:
                        raise ValueError(f"Missing teaching points: {school_code}")
                    need_school = True
                    continue
                if row[2] == "总计":
                    if len(row) != 16 or not row[11].isdigit():
                        raise ValueError(f"Invalid total: {row}")
                    totals[school_code] = int(row[11])
                    continue
                if not re.fullmatch(r"\d{2}", row[2]):
                    raise ValueError(f"Unparsed row: {path.name}/{page_number}: {row}")
                if row[0]:
                    if not re.fullmatch(r"\d{3}", row[0]):
                        raise ValueError(f"Invalid institution code: {row}")
                    school_code, school_name = row[0], institution_name(row[1])
                    need_school = False
                elif need_school:
                    # The 2025 Shanghai Dianji institution cell spans pp.7–8 and is
                    # open at the page edge. Recover its actual left-column text.
                    cell = table.rows[row_index].cells[2]
                    label = compact(page.crop((table.bbox[0], cell[1], cell[0], table.bbox[3])).extract_text())
                    match = re.fullmatch(r"(\d{3})(.+)", label)
                    if not match:
                        raise ValueError(f"Unresolved merged institution cell: {label}")
                    school_code, school_name = match[1], institution_name(match[2])
                    need_school = False
                if row[4] not in CATEGORIES or len(row) not in (15, 16):
                    raise ValueError(f"Unexpected category/schema: {row}")
                offset = 1 if len(row) == 16 else 0
                count = int(row[11]) if offset else None
                plans.append({
                    "province": "shanghai", "institution_code": school_code, "institution_name": school_name,
                    "year": year, "major_code": row[2], "major_name": row[3], "level": "专升本",
                    "category_code": None, "category_name": row[4], "plan_count": count,
                    "line_type": line_type, "round": round_name, "source_url": source_url, "source_page": page_number,
                    "study_duration_raw": row[5], "minimum_study_duration_raw": row[6], "major_direction": row[7],
                    "foreign_language": row[8], "fee_basis": row[10], **tuition_fields(row[9]),
                    "study_form": row[11 + offset], "teaching_site_codes": row[12 + offset],
                    "enrollment_scope": row[13 + offset], "remarks": row[14 + offset],
                })
    seen = set()
    for plan in plans:
        key = (plan["institution_code"], plan["major_code"])
        if key in seen:
            raise ValueError(f"Duplicate source plan: {key}")
        seen.add(key)
        point_codes = re.findall(r"\d+", plan["teaching_site_codes"])
        point_map = sites.get(plan["institution_code"], {})
        if any(code not in point_map for code in point_codes):
            raise ValueError(f"Unresolved teaching site: {key}/{point_codes}")
        plan["teaching_site"] = "；".join(f"{code}. {point_map[code].rstrip(';；')}" for code in point_codes) or None
    for code in {p["institution_code"] for p in plans}:
        if year == 2025:
            actual = sum(p["plan_count"] for p in plans if p["institution_code"] == code)
            if code not in totals or actual != totals[code]:
                raise ValueError(f"School total mismatch: {code} {actual} != {totals.get(code)}")
    return plans, totals


class TableParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.rows, self.row, self.cell = [], None, None

    def handle_starttag(self, tag, attrs):
        if tag == "tr": self.row = []
        if tag in ("td", "th"): self.cell = []

    def handle_data(self, data):
        if self.cell is not None: self.cell.append(data)

    def handle_endtag(self, tag):
        if tag in ("td", "th") and self.row is not None and self.cell is not None:
            self.row.append(compact("".join(self.cell)))
            self.cell = None
        if tag == "tr" and self.row is not None:
            self.rows.append(self.row)
            self.row = None


def parse_controls(html, year, url):
    parser = TableParser()
    parser.feed(html)
    rows = [r for r in parser.rows if len(r) >= 4 and r[1] in CATEGORIES
            and r[2].startswith("政治、") and r[3].isdigit()]
    if [r[1] for r in rows] != CATEGORIES:
        raise ValueError(f"Expected exactly eight 专升本 control lines for {year}: {rows}")
    return [{"province": "shanghai", "year": year, "level": "专升本", "category_code": None,
             "category_name": r[1], "score": int(r[3]), "line_type": "省控线", "round": "最低录取控制分数线",
             "subjects_raw": r[2], "remarks": r[4] if len(r) > 4 else "", "source_url": url} for r in rows]


def run(refresh=False):
    root = DATA / "sources" / "shanghai"
    root.mkdir(parents=True, exist_ok=True)
    source_manifest, all_plans, controls = [], [], []

    def fetch(filename, url):
        path = root / filename
        if refresh or not path.exists():
            path.write_bytes(urlopen(Request(url, headers={"User-Agent": "Mozilla/5.0"}), timeout=90).read())
        content = path.read_bytes()
        source_manifest.append({"path": str(path.relative_to(DATA)), "url": url, "sha256": hashlib.sha256(content).hexdigest()})
        return path

    for filename, url, year, round_name, line_type in SOURCES:
        path = fetch(filename, url)
        plans, totals = parse_catalog(path, year, round_name, line_type, url)
        all_plans.extend(plans)
        source_manifest[-1].update(rows=len(plans), institution_count=len({p["institution_code"] for p in plans}), plan_count=sum(totals.values()) if totals else None)
    for year, url in CONTROLS.items():
        path = fetch(f"controls-{year}.html", url)
        controls.extend(parse_controls(path.read_text(encoding="utf-8"), year, url))
    names = {p["institution_code"]: p["institution_name"] for p in all_plans}
    schools = [{"province": "shanghai", "institution_code": code, "institution_name": name,
                "city": OUTSIDE_CITIES.get(code, "上海")} for code, name in sorted(names.items())]
    outputs = {"shanghai-adult-programs.json": all_plans, "shanghai-adult-control-scores.json": controls,
               "shanghai-institutions.json": schools}
    manifest = {"province": "shanghai", "checked_at": datetime.now(timezone.utc).isoformat(),
                "institutions": len(schools), "plan_rows_by_year_round": dict(Counter(f"{p['year']}/{p['round']}" for p in all_plans)),
                "control_rows": len(controls), "institution_score_rows": 0,
                "limitations": ["未收录院校实际录取线；市控线独立保存，不能视为院校录取线", "2026目录未公布计划人数，保留null", "专业目录包含委托培养及非英语语种，请核对报考条件"],
                "sources": source_manifest}
    outputs["shanghai-manifest.json"] = manifest
    for filename, data in outputs.items():
        (DATA / filename).write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({key: value for key, value in manifest.items() if key != "sources"}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--refresh", action="store_true")
    run(parser.parse_args().refresh)
