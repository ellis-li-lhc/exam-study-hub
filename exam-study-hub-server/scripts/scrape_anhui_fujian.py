"""Collect complete current public adult 专升本 catalogues from Anhui and Fujian.
Read-only to the database. Offline replay by default; --refresh repeats archived public form requests.
"""
import argparse
from collections import Counter
from hashlib import sha256
import json
from pathlib import Path
import re
import subprocess
import xlrd
from scripts.adult_source_utils import TableReader
from scripts.scrape_hubei import expand
from scripts.scrape_hunan_jiangxi import CATEGORIES, MOE_PATH, MOE_URL, category, plain

DATA=Path(__file__).resolve().parent.parent/'scraped-data'
CONFIG={'anhui':dict(name='安徽',pages=37,public_rows=1104,programs=1104,institutions=71),
        'fujian':dict(name='福建',pages=25,public_rows=965,programs=468,institutions=40)}


def catalog_table(path,province):
    reader=TableReader();reader.feed(path.read_text(encoding='utf-8',errors='replace'))
    heading='院校专业代码'if province=='anhui'else'层次'
    table=next(t for t in reader.tables if t and t[0]and t[0][0][1]==heading)
    if province=='fujian':
        # Wabacus emits hidden td placeholders alongside real rowspans; they are not data columns.
        table=[[c for c in row if 'display:none'not in c[0].get('style','').replace(' ','')]for row in table]
    rows=list(expand(table))[1:]
    if any(len(r)!=(9 if province=='anhui'else 10)or any('\ufffd'in c for c in r)for r in rows):raise ValueError('Incomplete primary catalogue table')
    return rows


def parse_catalogue(province,root,urls):
    config=CONFIG[province];records=[];all_count=0;college_codes={}
    if province=='fujian' and '2026年福建省成人高校招生全国统一考试' not in plain((root/'portal-home-2026.html').read_text()):raise ValueError('Unverified active catalogue year')
    if province=='anhui' and '2026年全国各类成人高校在皖统一招生计划说明' not in plain((root/'catalog-query-2026.html').read_text()):raise ValueError('Unverified active catalogue year')
    for page in range(1,config['pages']+1):
        name=f'catalog-2026-{page:03}.html';html=(root/name).read_text(errors='replace')
        marker=re.search(r'name="currPage"[^>]*value="(\d+)"',html)if province=='anhui'else re.search(r'_PAGENO=(\d+)',html)
        if not marker or int(marker[1])!=page:raise ValueError('Catalogue pagination mismatch')
        rows=catalog_table(root/name,province);all_count+=len(rows)
        if len(rows)!=(30 if province=='anhui'else 40)and page!=config['pages']:raise ValueError('Missing catalogue rows')
        for index,row in enumerate(rows,1):
            if province=='anhui':
                major_code,school,major,form,level,cat,duration,fee,scope=row
                school_code=major_code[:3];remark=scope
                first=scope.split('。',1)[0]
                site=first if any(term in first for term in ['教学点','校本部','校区'])else None
            else:
                level,school_code,school,major_code,major,duration,cat,form,phone,scope=row
                if level!='专升本':continue
                match=re.fullmatch(r'收费标准[:：](.*?)，专业备注[:：](.*?)，授课地点[:：](.*)',scope)
                if not match:raise ValueError('Changed Fujian remarks schema')
                fee,remark,site=match.groups()
            if level!='专升本':raise ValueError('Other education level in Anhui filtered catalogue')
            if school in college_codes and college_codes[school]!=school_code:raise ValueError('School code mismatch')
            college_codes[school]=school_code;category_code=category(cat)
            raw_major=major;direction=None
            match=re.fullmatch(r'(.+?)[（(]([^()（）]+)[）)]',major)
            if match:major,direction=match.groups()
            fee_match=re.fullmatch(r'(\d+)(?:\.0)?元/(?:每)?(?:学年|年)',fee)
            # An amount without a stated billing period stays raw, with unknown unit and amount.
            amount=int(fee_match[1])if fee_match else None
            restricted=bool(re.search(r'只招|限招|不面向社会|委托培养|定向|面向[“"\u201c]?一村一名大学生',remark))
            if '社会招生或'in remark:restricted=False
            if re.fullmatch(r'\d+(?:元)?',fee):remark=(remark+'；'if remark else '')+'收费原文未注明计费周期，不可当作年学费。'
            records.append(dict(province=province,institution_name=school,institution_code=school_code,
                institution_code_raw=school_code,year=2026,level=level,major_code=major_code,
                major_code_raw=major_code,major_name=major,major_name_raw=raw_major,major_direction=direction,
                category_code=category_code,category_name=CATEGORIES[category_code],category_name_raw=cat,
                study_form=form,study_duration_raw=duration or None,minimum_study_duration_raw=None,
                plan_count=None,tuition_amount=amount,tuition_unit='per_academic_year'if amount is not None else None,
                tuition_raw=fee or None,teaching_site=site or None,enrollment_scope='安徽省'if province=='anhui'else'福建省',
                remarks=remark or None,foreign_language=None,selection_eligible=not restricted,
                restriction_note='专项或单位报考限制，不作为普通备考目标'if restricted else None,
                line_type='招生专业目录',round='省级公开招生专业目录',source_url=urls[name],
                source_query_page=page,source_table_row=index,source_filename=name))
    if all_count!=config['public_rows']or len(records)!=config['programs']:raise ValueError('Public catalogue count mismatch')
    if len({(r['institution_code'],r['major_code'])for r in records})!=len(records):raise ValueError('Duplicate catalogue keys')
    if len(college_codes)!=config['institutions']:raise ValueError('School count mismatch')
    return records


def school_identities(province,records,root,urls):
    sh=xlrd.open_workbook(MOE_PATH).sheet_by_index(0);clean=lambda s:s.replace('（','(').replace('）',')')
    moe={clean(str(sh.cell_value(i,1))):(str(int(float(sh.cell_value(i,2)))),str(sh.cell_value(i,4)).removesuffix('市'))for i in range(3,sh.nrows)if str(sh.cell_value(i,2)).replace('.','',1).isdigit()}
    exceptional={'安徽开放大学':('合肥','identity-ahou-admissions-2026.html','九华山路3号'),
                 '福建开放大学':('福州','identity-fjou-2026.html','桂山路109号'),
                 '福建教育学院':('福州','identity-fjjyxy-2022.html','梦山路73号')}
    schools={}
    for row in records:
        key=row['institution_code']
        if key in schools:continue
        name=row['institution_name'];national=None
        if clean(name)in moe:
            national,city=moe[clean(name)];city={'湘西土家族苗族自治州':'湘西'}.get(city,city);city_source=MOE_URL
        else:
            city,filename,address=exceptional[name];text=plain((root/filename).read_text())
            if city not in text or address not in text:raise ValueError('Unverified adult college location')
            city_source=urls[filename]
        schools[key]=dict(province=province,institution_code=key,institution_name=name,city=city,
            national_institution_code=national,identity_basis='省级公开招生院校代码；城市按教育部名单或学校/教育厅官方地址核验',
            city_source_url=city_source,source_urls=list(dict.fromkeys(r['source_url']for r in records if r['institution_code']==key)))
    return list(schools.values())


def parse_controls(province,root,urls):
    controls=[]
    if province=='anhui':
        for year in [2024,2025]:
            name=f'controls-{year}.html';text=plain((root/name).read_text()).split('三、专科起点升本科',1)[1]
            pairs=re.findall(r'\d+[.．](文史中医类|理工类|经管类|法学类|教育学类|农学类|医学类|艺术类)(\d+)分',text)
            if len(pairs)!=8:raise ValueError('Incomplete Anhui controls')
            for raw,score in pairs:controls.append((year,raw,int(score),urls[name]))
    else:
        reviewed=json.loads((root/'controls-2025-reviewed.json').read_text())
        if sha256((root/'controls-2025.png').read_bytes()).hexdigest()!=reviewed['source_sha256']:raise ValueError('Fujian control image changed; visual review required')
        controls=[(2025,raw,score,urls['controls-2025.html'])for raw,score in reviewed['ordinary_zsb_controls'].items()]
    return [dict(province=province,year=year,level='专升本',category_code=category(raw),category_name=CATEGORIES[category(raw)],
        category_name_raw=raw,score=score,line_type='省控线',round='统考生',source_url=url)for year,raw,score,url in controls]


def run(refresh=False):
    for province,config in CONFIG.items():
        root=DATA/'sources'/province;urls=json.loads((root/'source-urls.json').read_text());requests=json.loads((root/'source-requests.json').read_text())
        if refresh:
            for name,url in urls.items():
                command=['curl','--http1.0','-fsSL','--max-time','30',url]
                if name in requests:command+=['--data',requests[name]['body']]
                (root/name).write_bytes(subprocess.check_output(command))
        plans=parse_catalogue(province,root,urls);schools=school_identities(province,plans,root,urls);controls=parse_controls(province,root,urls)
        pairs=len({(r['institution_code'],r['major_name_raw'])for r in plans});restricted=sum(not r['selection_eligible']for r in plans)
        note=f'已接入2026省级公开专升本目录{len(schools)}校{len(plans)}条记录（{pairs}个院校专业组合），含不同教学点；{len(controls)}条历史省控线单列。{restricted}条专项限制记录不作普通备考目标；目录未公布人数，暂无院校实际录取线'
        for suffix,value in [('institutions',schools),('adult-programs',plans),('adult-control-scores',controls),('adult-category-collection-plans',[])]:
            (DATA/f'{province}-{suffix}.json').write_text(json.dumps(value,ensure_ascii=False,indent=2)+'\n')
        sources=[dict(path=str((root/name).relative_to(DATA)),url=url,sha256=sha256((root/name).read_bytes()).hexdigest(),**requests.get(name,{}))for name,url in urls.items()]
        sources.append(dict(path=str(MOE_PATH.relative_to(DATA)),url=MOE_URL,sha256=sha256(MOE_PATH.read_bytes()).hexdigest()))
        if province=='fujian':
            local=root/'controls-2025-reviewed.json';sources.append(dict(path=str(local.relative_to(DATA)),url=urls['controls-2025.png'],sha256=sha256(local.read_bytes()).hexdigest(),role='visually_reviewed_extraction'))
        manifest=dict(province=province,province_name=config['name'],catalog_year=2026,coverage_note=note,
            counts=dict(institutions=len(schools),programs=len(plans),controls=len(controls),category_collections=0),
            public_query=dict(pages=config['pages'],all_level_records=config['public_rows'],zsb_records=len(plans),
                completeness='all_current_public_query_pages',ordinary_target_excluded_records=restricted,school_major_pairs=pairs),sources=sources,
            limitations=['目录不是人数计划；无2027目录；2026资料仅作2027备考历史参考','省控线不是院校实际录取线；报考需符合相应专业资格',
                '查询分页使用公开POST表单，source_filename和source_query_page绑定原始页；直接打开官方链接为默认查询首页',
                '收费金额缺计费周期时保留原文，不推定为每年',
                '安徽省属高校备案Excel只归档核对，不与省级招生目录重复入库'if province=='anhui'else'2025征求公告仅列院校剩余人数，未标专业科类，本次仅归档不分摊为专业计划'])
        (DATA/f'{province}-manifest.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+'\n');print(province,manifest['counts'],note)

if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--refresh',action='store_true');run(parser.parse_args().refresh)
