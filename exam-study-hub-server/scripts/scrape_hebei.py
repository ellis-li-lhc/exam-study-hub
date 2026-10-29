"""Parse official Hebei adult 专升本 plans and control lines without cross-year code collisions.

python -m scripts.scrape_hebei [--refresh]
The 2026 full catalog and collection-plan details have not been obtained.
"""
import argparse
from collections import Counter
from datetime import datetime, timezone
import hashlib
from html.parser import HTMLParser
import json
from pathlib import Path
import re
from urllib.request import urlopen

import pdfplumber
import xlrd

DATA = Path(__file__).resolve().parent.parent / "scraped-data"
ROOT = DATA / "sources/hebei"
PLAN_SOURCES = {
    2024: ("https://www.hebeea.edu.cn/c/2024-11-20/488610.html", "https://file.hebeea.edu.cn/files/article/2024/11/20241119090127_572.pdf"),
    2025: ("https://www.hebeea.edu.cn/c/2025-11-13/489224.html", "https://file.hebeea.edu.cn/files/article/2025/11/20251113133649_120.pdf"),
}
CONTROL_SOURCES = {
    2023: "https://jxjy.hebuet.edu.cn/info/1163/2203.htm",
    2024: "https://www.hebeea.edu.cn/c/2024-11-20/489573.html",
    2025: "https://www.hebeea.edu.cn/c/2025-11-13/489357.html",
}
CITY_URL = "https://www.moe.gov.cn/jyb_xxgk/s5743/s5744/202606/W020260618416094865984.xls"
CITY_OVERRIDES = {
    "河北开放大学": ("石家庄", "https://www.ccgp.gov.cn/cggg/dfgg/zbgg/202608/t20260806_27081458.htm"),
    "华北电力大学(保定)": ("保定", "https://www.ncepu.edu.cn/xxgk/xxzc/index.htm"),
    "防灾科技学院": ("廊坊", "https://www1.cidp.edu.cn/zjfz/xxpm.htm"),
    "华北科技学院": ("廊坊", "https://yz.chsi.com.cn/sch/schoolInfo--schId-302972737,categoryId-302972784,mindex-15.dhtml"),
    "涟源钢铁总厂职工大学": ("娄底", "https://www.sceea.cn/Html/202012/NewsDetail_1661_2.html"),
}
RAW_CATEGORIES = ["文史", "艺术", "理工", "经管", "法学", "教育", "农学", "医学", "中医"]
CATEGORY_NAMES = dict(zip(RAW_CATEGORIES, ["文史类", "艺术类", "理工类", "经济管理类", "法学类", "教育学类", "农学类", "医学类", "中医类"]))
BOUNDS = [78, 181, 218, 246, 267, 373, 464.5, 522]


def fee_fields(raw):
    annual = re.fullmatch(r"(\d+(?:\.\d+)?)元/(?:学年|年)", raw)
    total = re.search(r"总学费(\d+)元", raw) or re.match(r"(\d+)元(?:（总学费）|/2\.5年)", raw)
    amount, unit = None, None
    if annual:
        unit = "per_academic_year"
        if annual[1].isdigit(): amount = int(annual[1])
    elif total:
        amount, unit = int(total[1]), "total"
    return {"tuition_raw": raw, "tuition_amount": amount, "tuition_unit": unit}


def parse_plan(path, year, source_url):
    rows, school, current, remark_mode, stopped = [], None, None, False, False
    independent_rows = 0
    with pdfplumber.open(path) as pdf:
        # Independent text-based row count covers the complete PDF, including
        # the other two levels, but only counts 专升本科类1x records.
        for page in pdf.pages:
            independent_rows += len(re.findall(r"(?m)^\d{3}\s.+?\s(?:文史|艺术|理工|经管|法学|教育|农学|医学|中医)1\d\s", page.extract_text() or ""))
        for page_number, page in enumerate(pdf.pages, 1):
            lines = []
            for char in sorted((c for c in page.chars if c["text"].strip()), key=lambda c: (c["top"], c["x0"])):
                if not lines or abs(char["top"] - lines[-1][0]) > 2:
                    lines.append([char["top"], []])
                lines[-1][1].append(char)
            started = False
            for _, chars in lines:
                chars.sort(key=lambda c: c["x0"])
                full = "".join(c["text"] for c in chars)
                if re.match(r"^[（(]二[）)]高中起点升本科", full):
                    stopped = True
                    break
                if full.startswith("编号学校、专业名称"):
                    started = True
                    continue
                if not started or re.fullmatch(r"第\d+页", full): continue
                columns = [""] * 9
                for char in chars:
                    columns[sum(char["x0"] >= bound for bound in BOUNDS)] += char["text"]
                if columns[0]:
                    if not re.fullmatch(r"\d{3}", columns[0]): raise ValueError(f"Unknown PDF row {page_number}: {full}")
                    if re.fullmatch(r"(?:文史|艺术|理工|经管|法学|教育|农学|医学|中医)1\d", columns[2]):
                        if not school: raise ValueError("Professional row has no institution")
                        if current: rows.append(current)
                        current = {"school": school, "columns": columns, "remarks": "", "source_page": page_number, "source_lines": [full]}
                        remark_mode = False
                    elif not any(columns[3:]):
                        if current: rows.append(current)
                        current = None
                        # Long bold school names can extend into the category column.
                        school, remark_mode = (columns[0], "".join(columns[1:])), False
                    else: raise ValueError(f"Unknown PDF schema {page_number}: {columns}")
                elif full.startswith("备注") or remark_mode:
                    if current is None: raise ValueError("Unattached PDF remark")
                    current["remarks"] += full
                    current["source_lines"].append(full)
                    remark_mode = True
                elif current:
                    for index in range(1, 9): current["columns"][index] += columns[index]
                    current["source_lines"].append(full)
                else: raise ValueError(f"Unattached PDF continuation {page_number}: {full}")
            if stopped: break
    if current: rows.append(current)
    if not stopped or len(rows) != independent_rows:
        raise ValueError(f"Incomplete PDF extraction: {len(rows)} != {independent_rows}")
    records, seen = [], set()
    for row in rows:
        code, name, category, form, duration, scope, site, fee, count = row["columns"]
        school_code, school_name = row["school"]
        if not count.isdigit() or not re.fullmatch(r"\d(?:\.\d)?", duration) or not all((name, scope, site, fee)):
            raise ValueError(f"Invalid PDF values: {row}")
        if form not in ("函授", "业余", "非脱产", "脱产"): raise ValueError(f"Unknown study form: {form}")
        if (school_code, code) in seen: raise ValueError("Duplicate official school/major code in year")
        seen.add((school_code, code))
        category_name = CATEGORY_NAMES[category[:-2]]
        if name in ("中医学", "中药学", "针灸推拿学"): category_name = "中医类"
        records.append({
            "province": "hebei", "institution_code_raw": school_code, "institution_name": school_name,
            "year": year, "major_code": code, "major_name": name, "level": "专升本",
            "category_code": category[-2:], "category_name": category_name, "category_name_raw": category,
            "line_type": "招生计划", "round": "本科一志愿", "plan_count": int(count),
            "study_form": form, "study_duration_raw": f"{duration} 年", "minimum_study_duration_raw": None,
            "enrollment_scope": scope, "teaching_site": site, **fee_fields(fee),
            "remarks": row["remarks"].removeprefix("备注：") or None,
            "applicant_group": "农民工考生" if "限招农民工考生" in row["remarks"] else "统考生",
            "source_url": source_url, "source_page": row["source_page"], "source_lines": row["source_lines"],
        })
    return records


class Tables(HTMLParser):
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
            self.row.append(re.sub(r"\s+", "", "".join(self.cell)))
            self.cell = None
        if tag == "tr" and self.row is not None:
            self.rows.append(self.row)
            self.row = None


def parse_controls(html, year, source_url):
    table = Tables()
    table.feed(html)
    rows, active = [], False
    for row in table.rows:
        if row and row[0] == "专升本":
            active, row = True, row[1:]
        elif row and row[0] in ("高起本", "高起专"):
            active = False
        if active: rows.append(row)
    if [r[0] for r in rows] != RAW_CATEGORIES: raise ValueError(f"Changed control-line schema: {year}")
    controls = []
    for row in rows:
        groups = [("统考生", row[-1])] if year == 2023 else list(zip(("统考生", "农民工考生"), row[1:]))
        if len(groups) != (1 if year == 2023 else 2): raise ValueError("Missing control-line group")
        for group, score in groups:
            if not score.isdigit(): raise ValueError(f"Invalid control-line value: {row}")
            controls.append({"province": "hebei", "year": year, "level": "专升本", "category_code": None,
                             "category_name": CATEGORY_NAMES[row[0]], "category_name_raw": row[0], "score": int(score),
                             "line_type": "省控线", "round": group, "source_url": source_url, "review_status": "verified_text"})
    return controls


def school_identity_and_cities(plans, city_path):
    # Official Hebei school codes change between years. Link exact school names,
    # then use the latest source code; namespace schools absent from that year.
    latest_year = max(p["year"] for p in plans)
    current_codes = {p["institution_name"]: p["institution_code_raw"] for p in plans if p["year"] == latest_year}
    sheet = xlrd.open_workbook(city_path).sheet_by_index(0)
    normalize = lambda name: name.replace("（", "(").replace("）", ")")
    cities = {normalize(str(sheet.cell_value(i, 1))): (str(sheet.cell_value(i, 4)).removesuffix("市"), i + 1)
              for i in range(3, sheet.nrows) if sheet.cell_value(i, 1)}
    schools = {}
    for plan in sorted(plans, key=lambda p: p["year"]):
        name = plan["institution_name"]
        code = current_codes.get(name, f"{plan['year']}-{plan['institution_code_raw']}")
        plan["institution_code"] = code
        if name not in schools:
            if name in CITY_OVERRIDES:
                city, url = CITY_OVERRIDES[name]
            elif normalize(name) in cities:
                city, _ = cities[normalize(name)]
                url = CITY_URL
            else: raise ValueError(f"Missing official city: {name}")
            schools[name] = {"province": "hebei", "institution_code": code, "institution_name": name,
                             "city": city, "city_source_url": url, "source_codes_by_year": {}}
        codes = schools[name]["source_codes_by_year"]
        prior = codes.setdefault(str(plan["year"]), plan["institution_code_raw"])
        if prior != plan["institution_code_raw"]: raise ValueError("Ambiguous same-year institution identity")
    if len({s["institution_code"] for s in schools.values()}) != len(schools): raise ValueError("Institution identity collision")
    return sorted(schools.values(), key=lambda s: s["institution_code"])


def run(refresh=False):
    ROOT.mkdir(parents=True, exist_ok=True)
    sources, plans, controls = [], [], []

    def fetch(filename, url):
        path = ROOT / filename
        if refresh or not path.exists(): path.write_bytes(urlopen(url, timeout=45).read())
        sources.append({"path": str(path.relative_to(DATA)), "url": url, "sha256": hashlib.sha256(path.read_bytes()).hexdigest()})
        return path

    for year, (article, pdf_url) in PLAN_SOURCES.items():
        fetch(f"plan-{year}.html", article)
        path = fetch(f"plan-{year}.pdf", pdf_url)
        parsed = parse_plan(path, year, pdf_url)
        sources[-1].update(rows=len(parsed), institutions=len({p["institution_name"] for p in parsed}),
                           plan_count=sum(p["plan_count"] for p in parsed))
        plans.extend(parsed)
    for year, url in CONTROL_SOURCES.items():
        path = fetch("controls-2023-university.html" if year == 2023 else f"controls-{year}.html", url)
        controls.extend(parse_controls(path.read_text(encoding="utf-8"), year, url))
    schools = school_identity_and_cities(plans, fetch("moe-universities-2026.xls", CITY_URL))
    manifest = {"province": "hebei", "checked_at": datetime.now(timezone.utc).isoformat(), "institutions": len(schools),
                "plan_rows": len(plans), "plan_rows_by_year": dict(Counter(p["year"] for p in plans)),
                "control_rows": len(controls), "institution_score_rows": 0, "latest_available_catalog_year": max(p["year"] for p in plans),
                "sources": sources, "limitations": ["未取得2026完整目录及征集逐专业明细", "未收录院校实际录取线或2026省控线", "2023官方高校转载仅提供统考生线，农民工线未知"]}
    for filename, content in {"hebei-adult-programs.json": plans, "hebei-adult-control-scores.json": controls,
                              "hebei-institutions.json": schools, "hebei-manifest.json": manifest}.items():
        (DATA / filename).write_text(json.dumps(content, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({k: v for k, v in manifest.items() if k != "sources"}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--refresh", action="store_true")
    run(parser.parse_args().refresh)
