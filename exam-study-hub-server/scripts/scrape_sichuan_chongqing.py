"""Replay the 2026 official adult 专升本 catalogues of Sichuan and Chongqing.

Sichuan publishes images: hash-bound, reconciled OCR extraction is required.
Chongqing publishes a public JSON query. Raw jhs is not shown by its public UI
and is deliberately not treated as a published enrolment count.
"""
import argparse
from collections import Counter
from hashlib import sha256
import json
from pathlib import Path
import re
import subprocess
import xlrd
from scripts.scrape_hunan_jiangxi import CATEGORIES, MOE_PATH, MOE_URL, category, plain

DATA=Path(__file__).resolve().parent.parent/'scraped-data'
CONFIG={'sichuan':dict(name='四川',rows=1329), 'chongqing':dict(name='重庆',rows=472)}


def canonical(raw):
    return category({'经济、管理类':'经济管理类','教育学类(含体教)':'教育学类'}.get(raw,raw))


def parse_catalogue(province,root,urls):
    records=[]
    if province=='chongqing':
        if '重庆市2026年全国成人高校招生专业目录' not in plain((root/'portal-home-2026.html').read_text()):raise ValueError('Unverified catalogue year')
        all_rows=json.loads((root/'catalog-all-levels-2026.json').read_text())
        zsb=json.loads((root/'catalog-zsb-2026.json').read_text())
        if all_rows['status']!=200 or zsb['status']!=200:raise ValueError('Failed public query')
        raw=zsb['data'];filtered=[r for r in all_rows['data']if r['ccmc'].strip()=='专升本']
        if raw!=filtered or len(all_rows['data'])!=742:raise ValueError('Filtered query differs from full public query')
        for i,r in enumerate(raw,1):
            if r['ccmc'].strip()!='专升本' or r['wyyzmc']!='英语':raise ValueError('Changed level/language schema')
            remark=r['zydz'];nature=remark.split()[0]
            if nature not in ['社会招生','直属与社会','直属单位','委托培养']:raise ValueError('Unrecognized admissions scope')
            restricted=nature in ['直属单位','委托培养'] or bool(re.search(r'仅招收|只招收|限招|在职人民警察',remark))
            # Public heading says 学校地址, not a confirmed teaching site.
            fee_match=re.search(r'(?<=\s)(总学费\d+元|\d+元/三年总学费|\d+(?:元/(?:学年|生/年|人·年|生\.年|年)|（元/生[·/]年）|/年)|按规定标准收费|\d+)(?=\s|[；;]|$)',remark)
            fee=fee_match[1]if fee_match else ('按规定标准收费'if '规定标准执行'in remark else None)
            if fee=='28002':remark+='；原文收费值28002有歧义，请以学校确认为准。'
            if fee and re.fullmatch(r'\d+',fee):remark+='；收费原文未注明计费周期，不可当作年学费。'
            code=canonical(r['klmc'])
            records.append(dict(province=province,institution_name=r['yxmc'],institution_code=r['yxdm'],institution_code_raw=r['yxdm'],
                year=2026,level='专升本',major_code=r['zydm'],major_code_raw=r['zydm'],major_name=r['zymc'],major_name_raw=r['zymc'],
                major_direction=None,category_code=code,category_name=CATEGORIES[code],category_name_raw=r['klmc'],
                study_form=r['xxxsmc'],study_duration_raw=r['xz']+'年',minimum_study_duration_raw=None,
                plan_count=None,tuition_raw=fee,teaching_site=None,enrollment_scope='重庆市',remarks=remark,
                foreign_language=r['wyyzmc'],selection_eligible=not restricted,
                restriction_note='直属单位或委托培养限制，不作为普通备考目标'if restricted else None,
                line_type='招生专业目录',round='省级公开招生专业目录',source_url=urls['catalog-2026.html'],
                source_table_row=i,source_filename='catalog-zsb-2026.json'))
    else:
        reviewed=json.loads((root/'catalog-reviewed-2026.json').read_text())
        for name,digest in reviewed['source_sha256'].items():
            if sha256((root/name).read_bytes()).hexdigest()!=digest:raise ValueError('Sichuan image/OCR changed; reconciliation required')
        if len(reviewed['physical_rows_per_page'])!=55 or sum(reviewed['physical_rows_per_page'].values())!=1329:raise ValueError('Incomplete image grid')
        for r in reviewed['rows']:
            school_code,school,major_code,major,cat,duration,fee,form,exam,site,address,remark=r['cells']
            code=canonical(cat)
            if code!=str(10+int(exam)):raise ValueError('Category/exam code conflict')
            if not re.fullmatch(r'\d{3}',school_code)or not re.fullmatch(r'\d{6}',major_code)or not major_code.startswith(school_code):raise ValueError('Invalid source codes')
            restricted=bool(re.search(r'限招|仅招|只招|不面向社会|委托培养|定向|在职.*警察',remark))
            name=f"catalog-2026-{r['page']:03}.png"
            records.append(dict(province=province,institution_name=school,institution_code=school_code,institution_code_raw=school_code,
                year=2026,level='专升本',major_code=major_code,major_code_raw=major_code,major_name=major,major_name_raw=major,
                major_direction=None,category_code=code,category_name=CATEGORIES[code],category_name_raw=cat,
                study_form=form,study_duration_raw=duration,minimum_study_duration_raw=None,plan_count=None,tuition_raw=fee or None,
                teaching_site=site or None,teaching_site_address_raw=address or None,enrollment_scope='四川省',remarks=remark or None,
                foreign_language=None,selection_eligible=not restricted,
                restriction_note='原目录有限定招生对象，不作为普通备考目标'if restricted else None,
                line_type='招生专业目录',round='省级公开招生专业目录',source_url=urls[name],
                source_page=r['page'],source_table_row=r['row'],source_filename=name))
    for r in records:
        fee=r['tuition_raw']or'';m=re.fullmatch(r'(\d+)(?:元/(?:学年|生/年|人·年|生\.年|年)|（元/生[·/]年）|/年)',fee)
        r['tuition_amount']=int(m[1])if m else None
        r['tuition_unit']='per_academic_year'if m else None
    if len(records)!=CONFIG[province]['rows']:raise ValueError('Incomplete catalogue')
    keys=[(r['institution_code'],r['major_code'])for r in records]
    if len(set(keys))!=len(keys):raise ValueError('Duplicate school/major codes')
    return records


def school_identities(province,records,root,urls):
    sh=xlrd.open_workbook(MOE_PATH).sheet_by_index(0)
    clean=lambda x:x.replace('（','(').replace('）',')')
    moe={clean(str(sh.cell_value(i,1))):(str(int(float(sh.cell_value(i,2)))),str(sh.cell_value(i,4)).removesuffix('市'))for i in range(3,sh.nrows)if str(sh.cell_value(i,2)).replace('.','',1).isdigit()}
    aliases={'华北电力大学(北京)':'华北电力大学'}
    cities={'阿坝藏族羌族自治州':'阿坝','甘孜藏族自治州':'甘孜','凉山彝族自治州':'凉山','湘西土家族苗族自治州':'湘西'}
    schools={}
    for r in records:
        key=r['institution_code'];name=r['institution_name'];normalized=clean(name);national=None
        if key in schools:
            if schools[key]['institution_name']!=name:raise ValueError('School code/name conflict')
            continue
        if normalized in ['四川开放大学','重庆开放大学']:
            city,filename,address=('成都','identity-scou.html','一环路西3段3号')if province=='sichuan'else('重庆','identity-cqou.html','华龙大道1号')
            text=plain((root/filename).read_text())
            if city not in text or address not in text:raise ValueError('Unverified open university location')
            source=urls[filename]
        else:
            national,city=moe[aliases.get(normalized,normalized)];city=cities.get(city,city);source=MOE_URL
            if province=='chongqing'and national[-5:]!=key:raise ValueError('National institution identity mismatch')
        schools[key]=dict(province=province,institution_code=key,institution_name=name,city=city,national_institution_code=national,
            identity_basis='省级官方专升本目录院校编码；城市按教育部高校名单或学校官网地址核验',city_source_url=source,
            source_urls=list(dict.fromkeys(x['source_url']for x in records if x['institution_code']==key)))
    return list(schools.values())


def parse_controls(province,root,urls):
    records=[]
    for year in [2024,2025]:
        name=f'controls-{year}.html';text=plain((root/name).read_text()).split('专科起点升本科',1)[1]
        text=text.split('三、艺术'if province=='sichuan'else'二、高中',1)[0]
        pairs=re.findall(r'（([一二三四五六七八])）(.*?)(\d+)分',text)
        if len(pairs)!=8 or [p[0]for p in pairs]!=list('一二三四五六七八'):raise ValueError('Incomplete control score categories')
        for i,(_,raw,score)in enumerate(pairs,11):
            records.append(dict(province=province,year=year,level='专升本',category_code=str(i),category_name=CATEGORIES[str(i)],
                category_name_raw=raw.removesuffix('：'),score=int(score),line_type='省控线',round='统考生',source_url=urls[name]))
    return records


def run(refresh=False):
    for province,config in CONFIG.items():
        root=DATA/'sources'/province;urls=json.loads((root/'source-urls.json').read_text());requests=json.loads((root/'source-requests.json').read_text())if (root/'source-requests.json').exists()else{}
        if refresh:
            for filename,url in urls.items():
                if filename.startswith('discovery-'):continue
                command=['curl','--http1.0','-fsSL','--max-time','45',url]
                if filename in requests:command+=['--data',requests[filename]['body']]
                content=subprocess.check_output(command)
                temporary=root/(filename+'.download');temporary.write_bytes(content);temporary.replace(root/filename)
        plans=parse_catalogue(province,root,urls);schools=school_identities(province,plans,root,urls);controls=parse_controls(province,root,urls)
        pairs=len({(r['institution_code'],r['major_name'])for r in plans});restricted=sum(not r['selection_eligible']for r in plans)
        note=f'已接入2026省级公开专升本目录{len(schools)}校{len(plans)}条记录（{pairs}个院校专业组合）；2024—2025省控线16条单列。{restricted}条限定招生记录不作普通备考目标；人数未作为公开计划导入，暂无院校实际录取线'
        for suffix,value in [('institutions',schools),('adult-programs',plans),('adult-control-scores',controls),('adult-category-collection-plans',[])]:
            (DATA/f'{province}-{suffix}.json').write_text(json.dumps(value,ensure_ascii=False,indent=2)+'\n')
        sources=[dict(path=str((root/name).relative_to(DATA)),url=url,sha256=sha256((root/name).read_bytes()).hexdigest(),**requests.get(name,{}))for name,url in urls.items()if 'discovery-'not in name]
        sources.append(dict(path=str(MOE_PATH.relative_to(DATA)),url=MOE_URL,sha256=sha256(MOE_PATH.read_bytes()).hexdigest()))
        if province=='sichuan':
            for path in [root/'catalog-reviewed-2026.json',*sorted(root.glob('*.ocr.json'))]:
                sources.append(dict(path=str(path.relative_to(DATA)),url=urls['catalog-2026.html'],sha256=sha256(path.read_bytes()).hexdigest(),role='image_extraction'))
        manifest=dict(province=province,province_name=config['name'],catalog_year=2026,coverage_note=note,
            counts=dict(institutions=len(schools),programs=len(plans),controls=len(controls),category_collections=0),
            public_query=dict(pages=55 if province=='sichuan'else 1,all_level_records=1329 if province=='sichuan'else 742,zsb_records=len(plans),
                completeness='all_55_official_catalogue_images'if province=='sichuan'else'all_public_json_rows_cross_checked_with_level_filter',
                ordinary_target_excluded_records=restricted,school_major_pairs=pairs),sources=sources,
            limitations=['2026目录为2027备考历史参考，不代表2027招生安排','省控线不是院校实际录取线；特殊专业资格要求仍需考生自行核实',
                '同名专业可因教学点、地址等不同占多行，不能把记录数当作专业数',
                '图片目录经网格分行、多次OCR比对与111处文字复核；图片或识别结果变化须重新核验'if province=='sichuan'else'公开页面未展示API中的jhs字段，因此未把该字段当作公开人数计划；学校地址不自动当作授课地点',
                '收费未注明周期时保留原文，不推算年学费'])
        (DATA/f'{province}-manifest.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+'\n');print(province,manifest['counts'],note)

    from scripts.sichuan_current_catalog import run as current_sichuan
    current_sichuan()

if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--refresh',action='store_true');run(parser.parse_args().refresh)
