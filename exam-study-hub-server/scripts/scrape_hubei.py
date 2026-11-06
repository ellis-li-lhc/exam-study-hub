"""Collect official Hubei adult 专升本 data; no database writes.
Run: python -m scripts.scrape_hubei [--refresh]
Scanned brochures remain raw sources for review, never guessed or imported.
"""
from html.parser import HTMLParser
from pathlib import Path
import re
class H(HTMLParser):
 def __init__(self):super().__init__();self.tables=[];self.table=None;self.row=None;self.cell=None;self.links=[];self.a=None
 def handle_starttag(self,t,a):
  a=dict(a)
  if t=='table':self.table=[]
  if t=='tr' and self.table is not None:self.row=[]
  if t in ('td','th') and self.row is not None:self.cell=[a,[]]
  if t=='a':self.a=[a.get('href',''),[]]
 def handle_data(self,s):
  if self.cell is not None:self.cell[1].append(s)
  if self.a is not None:self.a[1].append(s)
 def handle_endtag(self,t):
  if t in ('td','th') and self.cell is not None:self.row.append((self.cell[0],re.sub(r'\s+','',''.join(self.cell[1]))));self.cell=None
  if t=='tr' and self.row is not None:self.table.append(self.row);self.row=None
  if t=='table' and self.table is not None:self.tables.append(self.table);self.table=None
  if t=='a' and self.a is not None:self.links.append((self.a[0],''.join(self.a[1]).strip()));self.a=None

import argparse
import hashlib
import json
from datetime import datetime, timezone
from urllib.request import Request, urlopen
import pdfplumber

DATA = Path(__file__).resolve().parent.parent / 'scraped-data'
ROOT = DATA / 'sources/hubei'
CATEGORIES = {'11':'文史中医类','12':'艺术类','13':'理工类','14':'经济管理类','15':'法学类','16':'教育学类','17':'农学类','18':'医学类'}


def document(name):
    h = H()
    h.feed((ROOT / name).read_text(encoding='utf-8'))
    return h


def expand(table):
    """Expand actual HTML row/column spans; never forward-fill unrelated cells."""
    occupied = {}
    for r, row in enumerate(table):
        c = 0
        for attrs, value in row:
            while (r, c) in occupied: c += 1
            for dr in range(int(attrs.get('rowspan', 1))):
                for dc in range(int(attrs.get('colspan', 1))):
                    if (r+dr, c+dc) in occupied: raise ValueError('Overlapping HTML spans')
                    occupied[r+dr, c+dc] = value
            c += int(attrs.get('colspan', 1))
        cols = [col for rr, col in occupied if rr == r]
        yield [occupied.get((r, col), '') for col in range(max(cols, default=-1)+1)]


def parse_controls(year, source_url):
    text = re.sub(r'\s+', '', re.sub(r'<[^>]*>', '', (ROOT/f'controls-{year}.html').read_text()))
    text = text.split('三、专科起点升本科', 1)[1]
    result = []
    for score, group in re.findall(r'以下科类录取控制分数线为(\d+)分[：:](.*?)。', text):
        for code in re.findall(r'代号(1[1-8])', group):
            result.append(dict(province='hubei', year=year, category_code=code,
                               category_name=CATEGORIES[code], score=int(score), level='专升本',
                               line_type='省控线', round='统考生', source_url=source_url))
    if len(result) != 8 or len({r['category_code'] for r in result}) != 8:
        raise ValueError(f'Incomplete control lines: {year}')
    return result


def parse_collections(year, source_url):
    records = []
    with pdfplumber.open(ROOT/f'collection-{year}.pdf') as pdf:
        for page_no, page in enumerate(pdf.pages, 1):
            tables = page.extract_tables()
            if not tables: raise ValueError('Collection PDF lost tables')
            school_code = school_name = None
            for row in tables[0]:
                cells = [re.sub(r'\s+', '', v or '') for v in row]
                if any('高中起点' in v for v in cells): break
                if year == 2024:
                    if len(cells) != 4: raise ValueError('Changed 2024 collection schema')
                    if cells[0].isdigit(): school_code, school_name = cells[:2]
                    category, count = cells[2:]
                else:
                    if cells[0] and re.match(r'^\d{3}', cells[0]):
                        school_code, school_name = cells[0][:3], cells[0][3:]
                    choices = [v for v in cells if re.match(r'^1[1-8][－-]', v)]
                    if not choices: continue
                    category = choices[0]
                    count = next((v for v in cells[3:] if v.isdigit()), '')
                match = re.fullmatch(r'((?:12)?1[1-8])[－-](.+?)（(非脱产)）', category)
                if not match: continue
                if not school_code or not school_name or not count.isdigit(): raise ValueError('Incomplete collection row')
                records.append(dict(province='hubei', year=year, institution_code_raw=school_code,
                    institution_name=school_name, level='专升本', category_code=match[1][-2:],
                    category_code_raw=match[1], category_name=CATEGORIES[match[1][-2:]],
                    study_form=match[3], plan_count=int(count), major_name=None, major_code=None,
                    line_type='征集计划', round='征集志愿', granularity='institution_category',
                    source_url=source_url, source_page=page_no))
        # Independent complete-PDF text count excludes 高起本科类41/45.
        independent = sum(len(re.findall(r'(?:12)?1[1-8][－-].*?（非脱产）\s+\d+', p.extract_text() or '')) for p in pdf.pages)
    if len(records) != independent or len(records) != {2024:9, 2025:16}[year]:
        raise ValueError(f'Incomplete collection: {len(records)} != {independent}')
    return records


def catalogues(urls):
    records = []
    for key, school in [('hbucm','湖北中医药大学'),('hbmu','湖北医药学院'),('hzau','华中农业大学'),('hubu','湖北大学'),('hbeu','湖北工程学院')]:
        name = f'brochure-{key}-2026.html'
        h = document(name)
        tables = [list(expand(t)) for t in h.tables]
        if key == 'hubu': selected = [t for t in tables if t and t[0] and t[0][0]=='专业名称'][1]
        elif key == 'hbeu': selected = [t for t in tables if t and '学费' in t[0] and '学科门类' in t[0]][1]
        else: selected = next(t for t in tables if t and any('学制' in x for x in t[0]))
        for row_no, row in enumerate(selected[1:], 2):
            major_code = category = form = duration = scope = fee = degree = discipline = None
            if key == 'hbucm':
                major_code, major, duration, level, category, form, fee = row
                if level != '专升本': continue
            elif key == 'hbmu':
                major, level, duration, degree, fee, form = row
                if level != '专升本': continue
            elif key == 'hzau':
                level, major, duration, category, scope = row
                if level != '专升本' or '湖北' not in scope: continue
            elif key == 'hubu': major, category, form, duration, fee, scope = row
            else: major, fee, discipline, duration, form = row
            raw_major = major
            major = re.sub(r'[＊*]|（新增专业）', '', major)
            tuition_amount = int(re.sub(r'元(?:/年)?', '', fee)) if fee else None
            records.append(dict(province='hubei', institution_name=school, institution_code_raw=None,
                year=2026, level='专升本', major_code=major_code, major_name=major, major_name_raw=raw_major,
                category_name_raw=category, discipline_raw=discipline, study_form=form,
                study_duration_raw=duration, degree_raw=degree, enrollment_scope=scope,
                tuition_amount=tuition_amount, tuition_unit='per_academic_year' if fee else None,
                tuition_raw=fee, tuition_source_basis='table_header_per_year' if fee else None,
                teaching_site=None, plan_count=None, line_type='招生专业目录',
                round='院校招生简章（最终以批准目录为准）', source_url=urls[name], source_table_row=row_no))
    if len({(r['institution_name'],r['major_name']) for r in records}) != len(records):
        raise ValueError('Duplicate institution/major catalogue row')
    return records



def normalize_records(catalog, collections, institutions):
    import xlrd
    # Plain text is a derived, archived extraction from the official DOC attachment.
    text = (ROOT/'exam-categories-2026.txt').read_text()
    text = text.split('四、专科起点升本科招生专业与统一考试科目对照表', 1)[1].split('附件 2', 1)[0]
    starts = list(re.finditer(r'（([一二三四五六七八])）', text))
    by_name = {}
    for index, start in enumerate(starts):
        category_code = str(11 + '一二三四五六七八'.index(start[1]))
        segment = text[start.end():starts[index+1].start() if index+1 < len(starts) else len(text)]
        for national_code, name in re.findall(r'(?m)^(\d{6})\s*\n([^\d\n][^\n]*)', segment):
            name = re.sub(r'\s+', '', name)
            by_name[name] = (national_code, category_code)
    sheet = xlrd.open_workbook(ROOT/'moe-universities-2026.xls').sheet_by_index(0)
    clean = lambda value: value.replace('（','(').replace('）',')')
    schools = {clean(str(sheet.cell_value(i,1))): (str(sheet.cell_value(i,2)), str(sheet.cell_value(i,4)).removesuffix('市')) for i in range(3,sheet.nrows)}
    identities = {}
    for inst in institutions:
        code, city = schools[clean(inst['name'])]
        inst.update(institution_name=inst['name'],institution_code=code,city=city,
                    city_source_url='https://www.moe.gov.cn/jyb_xxgk/s5743/s5744/202606/W020260618416094865984.xls',
                    identity_basis='教育部学校标识码')
        identities[inst['name']] = code
    for row in catalog:
        national, category = by_name.get(row['major_name'], (None, None))
        raw = row['category_name_raw']
        aliases = {'文学类':'文史中医类','文史、中医类':'文史中医类','文史类':'文史中医类','教育类':'教育学类','经管类':'经济管理类'}
        if category is None:
            category = next((code for code,name in CATEGORIES.items() if name == aliases.get(raw,raw)), None)
        if category is None:
            category = {'工学':'13','经济学':'14','管理学':'14','教育学':'16','法学':'15','农学':'17','文学':'11'}.get(row['discipline_raw'])
        if category is None: raise ValueError(f"未核实专业科类: {row['major_name']}")
        if raw and aliases.get(raw,raw) != CATEGORIES[category]:
            raise ValueError(f"院校科类与考试院对照表冲突: {row['major_name']}")
        row.update(institution_code=identities[row['institution_name']],major_code_raw=row['major_code'],
                   national_major_code=national,major_code=row['major_code'] or 'catalog-'+(national or hashlib.sha256(row['major_name'].encode()).hexdigest()[:12]),
                   category_code=category,category_name=CATEGORIES[category],
                   category_source_url='https://www.hbea.edu.cn/html/2026-08/16093.shtml',
                   foreign_language='英语')
        if row['tuition_amount'] is not None:
            row['tuition_raw'] = str(row['tuition_amount'])+'元/年'
    for row in collections: row['institution_code'] = identities[row['institution_name']]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--refresh', action='store_true')
    args = parser.parse_args()
    urls = json.loads((ROOT/'source-urls.json').read_text())
    if args.refresh:
        for name, url in urls.items():
            data = urlopen(Request(url, headers={'User-Agent':'Mozilla/5.0'}), timeout=30).read()
            if not data: raise ValueError(f'Empty source: {url}')
            if name == 'exam-categories-2026.doc' and data != (ROOT/name).read_bytes():
                raise ValueError('官方科类DOC已变化，需重新提取并核验对应TXT')
            (ROOT/name).write_bytes(data)
    controls = [r for year in (2023,2024,2025) for r in parse_controls(year,urls[f'controls-{year}.html'])]
    collections = [r for year in (2024,2025) for r in parse_collections(year,urls[f'collection-{year}.pdf'])]
    catalog = catalogues(urls)
    schools = sorted({r['institution_name'] for r in catalog+collections})
    institutions = [dict(province='hubei',name=school,
        official_codes_by_year={str(r['year']):r['institution_code_raw'] for r in collections if r['institution_name']==school},
        source_urls=sorted({r['source_url'] for r in catalog+collections if r['institution_name']==school})) for school in schools]
    normalize_records(catalog, collections, institutions)
    outputs = {'hubei-adult-control-scores.json':controls, 'hubei-adult-category-collection-plans.json':collections,
               'hubei-adult-programs.json':catalog, 'hubei-institutions.json':institutions}
    for name, data in outputs.items(): (DATA/name).write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n')
    manifest = dict(province='hubei', checked_at=datetime.now(timezone.utc).isoformat(), stage='normalized_ready_for_import',
        catalogue_institutions=len({r['institution_name'] for r in catalog}), catalogue_rows=len(catalog),
        collection_rows=len(collections), collection_plan_counts_by_year={str(y):sum(r['plan_count'] for r in collections if r['year']==y) for y in [2024,2025]},
        control_rows=len(controls), institution_score_rows=0,
        sources=[dict(path=f'sources/hubei/{name}',url=url,sha256=hashlib.sha256((ROOT/name).read_bytes()).hexdigest()) for name,url in sorted(urls.items())],
        derived_sources=[dict(path='sources/hubei/exam-categories-2026.txt', derived_from='sources/hubei/exam-categories-2026.doc', method='macOS textutil -convert txt', sha256=hashlib.sha256((ROOT/'exam-categories-2026.txt').read_bytes()).hexdigest())],
        limitations=['非全省完整专业目录，2026仅所列院校简章；拟招生专业仍以审核批准结果为准',
        '征集计划仅院校科类粒度，禁止分摊为逐专业人数', '2026省控线及院校实际录取线未取得',
        '湖北工业大学、湖北经济学院PDF为扫描件，其余无文本表格简章尚未结构化，均不并入专业行',
        '湖北医药学院为招生预告；科类按湖北考试院2026专业科目对照表核对，原始科类和学科门类分别保留',
        '华中农业大学表中*及新增标记保留原文；未明确专业学费、教学点和人数保持空'])
    (DATA/'hubei-manifest.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+'\n')
    print(json.dumps({k:v for k,v in manifest.items() if k!='sources'},ensure_ascii=False,indent=2))


if __name__ == '__main__': main()
