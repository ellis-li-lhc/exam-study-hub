"""Download and validate official Shandong adult 专升本 catalogs and collection plans.

Run python -m scripts.scrape_shandong; --refresh downloads sources again.
Control-line images are transcribed after visual review and pinned by SHA-256.
"""
import argparse
from collections import Counter
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import re
from urllib.request import urlopen
from xml.etree import ElementTree as ET
from zipfile import ZipFile

import xlrd

DATA = Path(__file__).resolve().parent.parent / "scraped-data"
ROOT = DATA / "sources/shandong"
BASE = "https://www.sdzk.cn/"
SOURCES = [
    ("catalog-2025.xls", "Floadup/file/20250826/6389181420201527561730930.xls", 7026, 2025, "招生专业目录"),
    ("catalog-2026.xlsx", "Floadup/file/20260826/6392332047617500952996405.xlsx", 7348, 2026, "招生专业目录"),
    ("collection1-2025.xls", "Floadup/file/20251213/6390122307221753192498480.xls", 7096, 2025, "第一次征集志愿"),
    ("collection2-2025.xls", "Floadup/file/20251217/6390157090293786768422343.xls", 7113, 2025, "第二次征集志愿"),
]
CONTROL_SOURCES = [
    (2023, 6382, "Floadup/image/20231121/6383617703936837785896992.png"),
    (2024, 6738, "Floadup/image/20241125/6386812164196963954636792.png"),
    (2025, 7077, "Floadup/image/20251123/6389949885451560281575876.png"),
]
NS = {"s": "http://schemas.openxmlformats.org/spreadsheetml/2006/main"}
CITY_URL = "https://www.moe.gov.cn/jyb_xxgk/s5743/s5744/202606/W020260618416094865984.xls"
CITY_OVERRIDES = {
    "060": {"city": "济南", "source_url": "https://www.sdou.edu.cn/col/col9859/index.html"},
    "087": {"city": "青岛", "source_url": "https://www.qingdao.gov.cn/ywdt/zwzl/ggqsydwgk/jy_208048/gdxx/qdkfdx/zsks/zsjh/202507/t20250715_9852866.shtml"},
    "320": {"city": "保定", "source_url": "https://www.ncepu.edu.cn/xxgk/xxzc/index.htm"},
}


def build_cities(plans, path):
    sheet = xlrd.open_workbook(path).sheet_by_index(0)
    normalize = lambda value: value.replace("（", "(").replace("）", ")").strip()
    lookup = {normalize(text(sheet.cell_value(i, 1))): sheet.row_values(i)
              for i in range(3, sheet.nrows) if sheet.cell_value(i, 1)}
    row_numbers = {normalize(text(sheet.cell_value(i, 1))): i + 1
                   for i in range(3, sheet.nrows) if sheet.cell_value(i, 1)}
    latest = {plan["institution_code"]: plan for plan in sorted(plans, key=lambda p: p["year"])}
    cities = {}
    for code, plan in latest.items():
        row = lookup.get(normalize(plan["institution_name"]))
        if code in CITY_OVERRIDES:
            cities[code] = CITY_OVERRIDES[code]
        elif row and row[4]:
            cities[code] = {"city": text(row[4]).removesuffix("市"), "source_url": CITY_URL,
                            "source_row": row_numbers[normalize(plan["institution_name"])], "source_city_raw": row[4]}
        else: raise ValueError(f"Missing official city reference: {code}/{plan['institution_name']}")
    return cities


def text(value):
    if value is None: return ""
    if isinstance(value, float) and value.is_integer(): return str(int(value))
    return str(value).strip()


def workbook_rows(path):
    """Read values without executing workbook formulas or macros."""
    if path.suffix == ".xls":
        book = xlrd.open_workbook(path)
        if book.nsheets != 1: raise ValueError(f"Unexpected sheets in {path.name}")
        sheet = book.sheet_by_index(0)
        return sheet.name, [[text(v) for v in sheet.row_values(i)] for i in range(sheet.nrows)]
    with ZipFile(path) as book:
        sheets = ET.fromstring(book.read("xl/workbook.xml")).findall("s:sheets/s:sheet", NS)
        if len(sheets) != 1: raise ValueError(f"Unexpected sheets in {path.name}")
        shared = []
        if "xl/sharedStrings.xml" in book.namelist():
            shared = ["".join(si.itertext()) for si in ET.fromstring(book.read("xl/sharedStrings.xml"))]
        rows = []
        for row in ET.fromstring(book.read("xl/worksheets/sheet1.xml")).findall("s:sheetData/s:row", NS):
            values = [""] * 11
            for cell in row.findall("s:c", NS):
                if cell.find("s:f", NS) is not None: raise ValueError("Unexpected formula in official catalog")
                column = re.match(r"[A-Z]+", cell.attrib["r"])[0]
                index = 0
                for char in column: index = index * 26 + ord(char) - 64
                if index > 11: raise ValueError("Unexpected catalog column")
                value = cell.find("s:v", NS)
                value = value.text if value is not None else ""
                if cell.get("t") == "s": value = shared[int(value)]
                elif cell.get("t") == "inlineStr": value = "".join(cell.find("s:is", NS).itertext())
                values[index - 1] = text(value)
            if any(values): rows.append(values)
        return sheets[0].attrib["name"], rows


def normalized_category(raw, major_name):
    category = raw.removeprefix("专升本")
    if category in ("文史、中医类", "文史中医类", "文史类"):
        return "中医类" if major_name in ("中医学", "中药学", "针灸推拿学") else "文史类"
    if category in ("经管类", "经济、管理类", "经济管理类"): return "经济管理类"
    if category == "教育学类" and major_name in ("体育教育", "运动训练", "休闲体育"): return "体育类"
    if category not in ("理工类", "医学类", "教育学类", "法学类", "艺术类", "农学类"):
        raise ValueError(f"Unknown category: {raw}")
    return category


def parse_programs(path, year, round_name, source_url):
    sheet, rows = workbook_rows(path)
    collection = round_name != "招生专业目录"
    header_index = 2 if collection else 1
    expected = (["序号", "院校代码", "院校名称", "层次", "专业代码", "专业名称", "科类", "学习形式", "学制", "招生范围", "计划数", "备注"] if collection else
                ["招生学校代码", "招生学校名称", "省编院校专业代号", "国标专业代码", "专业名称", "层次名称", "科类名称", "招生范围名称", "学制", "学习形式名称", "备注"])
    if rows[header_index] != expected: raise ValueError(f"Changed source schema: {path.name}")
    if str(year) not in rows[0][0]: raise ValueError("Catalog year mismatch")
    records, excluded, seen, footnotes = [], Counter(), set(), []
    reminder = rows[1][0] if collection else None
    for row_number, row in enumerate(rows[header_index + 1:], header_index + 2):
        if not any(row): continue
        if row[0].startswith("✱本目录信息截止至") and not any(row[1:]):
            footnotes.append(row[0])
            continue
        if len(row) != len(expected): raise ValueError(f"Invalid row {row_number}")
        level = row[3] if collection else row[5]
        if level not in ("专升本", "高职（专科）", "高中起点本科"):
            raise ValueError(f"Unknown level on row {row_number}: {level}")
        if collection and row[0] != str(row_number - header_index - 1):
            raise ValueError(f"Non-contiguous source sequence on row {row_number}")
        if level != "专升本":
            excluded[level] += 1
            continue
        if collection:
            code, name, local_major, major_name, category = row[1], row[2], row[4], row[5], row[6]
            if not row[10].isdigit(): raise ValueError(f"Invalid plan count: {row}")
            count, duration, form, scope, remarks = int(row[10]), row[8], row[7], row[9], row[11]
            national_major = None
            source_major = local_major
            # The catalog uses 8 digits (school + 5-digit major); collection
            # sheets explicitly split the same school and 5-digit major code.
            local_major = code + local_major
        else:
            code, name, local_major, national_major, major_name = row[:5]
            category, scope, duration, form, remarks = row[6:]
            count, source_major = None, local_major
        if not re.fullmatch(r"\d{3}", code) or not re.fullmatch(code + r"\d{5}", local_major):
            raise ValueError(f"Invalid official code on row {row_number}: {code}/{local_major}")
        if (code, local_major) in seen: raise ValueError("Duplicate school/major in batch")
        seen.add((code, local_major))
        records.append({
            "province": "shandong", "institution_code": code, "institution_name": name, "year": year,
            "major_code": local_major, "major_code_raw": source_major, "national_major_code": national_major,
            "major_name": major_name, "level": level, "category_code": None,
            "category_name": normalized_category(category, major_name), "category_name_raw": category,
            "plan_count": count, "line_type": "征集计划" if collection else "招生专业目录", "round": round_name,
            "study_duration_raw": f"{duration} 年", "minimum_study_duration_raw": None,
            "study_form": form, "enrollment_scope": scope, "remarks": remarks or None,
            "teaching_site": None, "tuition_raw": None, "tuition_amount": None, "tuition_unit": None,
            "foreign_language": None, "source_url": source_url, "source_sheet": sheet, "source_row": row_number,
        })
    return records, {"rows": len(records), "institutions": len({r["institution_code"] for r in records}),
                     "excluded_levels": dict(excluded), "source_data_rows": len(rows) - header_index - 1 - len(footnotes),
                     "plan_count": sum(r["plan_count"] for r in records) if collection else None,
                     "batch_reminder": reminder, "footnotes": footnotes}


def run(refresh=False):
    ROOT.mkdir(parents=True, exist_ok=True)
    manifest_sources, plans = [], []

    def fetch(filename, url):
        path = ROOT / filename
        if refresh or not path.exists(): path.write_bytes(urlopen(url, timeout=45).read())
        manifest_sources.append({"path": str(path.relative_to(DATA)), "url": url,
                                 "sha256": hashlib.sha256(path.read_bytes()).hexdigest()})
        return path

    for filename, route, article_id, year, round_name in SOURCES:
        fetch(filename.rsplit('.', 1)[0] + ".html", BASE + f"NewsInfo.aspx?NewsID={article_id}")
        path = fetch(filename, BASE + route)
        records, summary = parse_programs(path, year, round_name, BASE + route)
        plans.extend(records)
        manifest_sources[-1].update(summary)
    catalog_2025 = {p["major_code"]: p for p in plans if p["year"] == 2025 and p["round"] == "招生专业目录"}
    for plan in plans:
        if plan["line_type"] == "征集计划":
            main = catalog_2025.get(plan["major_code"])
            if main is None or main["institution_code"] != plan["institution_code"]:
                raise ValueError(f"Unmatched collection code: {plan['major_code']}")
            if main["major_name"].split("（")[0] != plan["major_name"].split("（")[0]:
                raise ValueError("Collection major name mismatch")
            plan["national_major_code"] = main["national_major_code"]
    reviewed = json.loads((DATA / "shandong-controls-reviewed.json").read_text())
    controls = []
    for year, article_id, route in CONTROL_SOURCES:
        fetch(f"controls-{year}.html", BASE + f"NewsInfo.aspx?NewsID={article_id}")
        image_path = fetch(f"controls-{year}.png", BASE + route)
        review = reviewed[str(year)]
        if hashlib.sha256(image_path.read_bytes()).hexdigest() != review["sha256"]:
            raise ValueError(f"Control image changed; requires visual review: {year}")
        for code, name, score in review["rows"]:
            controls.append({"province": "shandong", "year": year, "level": "专升本", "category_code": code,
                             "category_name": name, "category_name_raw": "经济、管理及药学类" if name == "经济管理类" else name,
                             "score": score, "line_type": "省控线", "round": "最低录取控制分数线",
                             "source_url": BASE + f"NewsInfo.aspx?NewsID={article_id}", "source_image_url": BASE + route,
                             "review_status": "visually_verified"})
    city_path = fetch("moe-universities-2026.xls", CITY_URL)
    city_records = build_cities(plans, city_path)
    schools = {}
    for plan in plans:
        code = plan["institution_code"]
        if code not in schools or plan["year"] > schools[code]["latest_catalog_year"]:
            city = city_records.get(code, {})
            schools[code] = {"province": "shandong", "institution_code": code, "institution_name": plan["institution_name"],
                             "latest_catalog_year": plan["year"], "city": city.get("city"), "city_source_url": city.get("source_url")}
    manifest = {"province": "shandong", "checked_at": datetime.now(timezone.utc).isoformat(), "institutions": len(schools),
                "program_rows": len(plans), "program_rows_by_year_round": dict(Counter(f"{p['year']}/{p['round']}" for p in plans)),
                "control_rows": len(controls), "institution_score_rows": 0, "sources": manifest_sources,
                "limitations": ["目录未公布首次志愿计划人数、学费和教学点，不作推断", "尚未收录院校实际录取线或2026省控线", "职业本科及限制招生对象的专业保留完整名称与条件"]}
    for name, data in {"shandong-adult-programs.json": plans, "shandong-adult-control-scores.json": controls,
                       "shandong-institution-cities.json": city_records,
                       "shandong-institutions.json": list(schools.values()), "shandong-manifest.json": manifest}.items():
        (DATA / name).write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({k: v for k, v in manifest.items() if k != "sources"}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--refresh", action="store_true")
    run(parser.parse_args().refresh)
