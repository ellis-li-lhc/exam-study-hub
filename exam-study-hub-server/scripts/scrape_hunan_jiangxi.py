"""Archive and normalize official adult 专升本 sources. Never writes the database.
Run python -m scripts.scrape_hunan_jiangxi [--refresh].
"""
import argparse
from hashlib import sha256
from html import unescape
import json
from pathlib import Path
import re
import subprocess
from urllib.request import Request, urlopen
import xlrd
from scripts.adult_source_utils import tables

DATA=Path(__file__).resolve().parent.parent/'scraped-data'
CATEGORIES={'11':'文史中医类','12':'艺术类','13':'理工类','14':'经济管理类','15':'法学类','16':'教育学类','17':'农学类','18':'医学类'}
ALIASES={'文史类':'文史中医类','文史、中医类':'文史中医类','经管类':'经济管理类','教育类':'教育学类'}
MOE_URL='https://www.moe.gov.cn/jyb_xxgk/s5743/s5744/202606/W020260618416094865984.xls'
MOE_PATH=DATA/'sources/hubei/moe-universities-2026.xls'

def category(raw):
    name=ALIASES.get(raw,raw)
    return next(code for code,value in CATEGORIES.items() if value==name)

def plain(html):
    html=re.sub(r'<(?:script|style)\b.*?</(?:script|style)>','',html,flags=re.S|re.I)
    return re.sub(r'\s+','',unescape(re.sub('<[^>]*>','',html)))

def program(province,school,major,cat,url,**kw):
    code=category(cat)
    return dict(province=province,institution_name=school,year=2026,level='专升本',
        major_name=major,major_name_raw=major,category_code=code,category_name=CATEGORIES[code],
        category_name_raw=cat,major_code_raw=None,study_form=None,study_duration_raw=None,
        foreign_language=None,tuition_amount=None,tuition_unit=None,tuition_raw=None,
        teaching_site=None,enrollment_scope=None,plan_count=None,line_type='招生专业目录',
        round='招生专业目录' if province=='hunan' else '院校招生简章（最终以批准目录为准）',source_url=url,**kw)

def control(province,year,cat,score,url):
    code=category(cat)
    return dict(province=province,year=year,level='专升本',category_code=code,
        category_name=CATEGORIES[code],score=int(score),line_type='省控线',round='统考生',source_url=url)

def hunan(root,urls):
    plans=[]; schools={}; independent=0; current=level=cat=None
    for name in ['catalog-page7-2026.html','catalog-prev-2026.html','catalog-last-2026.html']:
        section=(root/name).read_text().split('<!--enpcontent-->')[1].split('<!--/enpcontent-->')[0]
        independent+=len(re.findall(r'\(1\d\d\)',section))
        for number, fragment in enumerate(re.split('</p>',section,flags=re.I),1):
            text=plain(fragment)
            match=re.match(r'^(\d{5})(.+?)(?:电话|$)',text)
            if match:
                code,school=match.groups();current=code;level=cat=None
                schools[code]=dict(institution_code=code,institution_name=school,source_urls=[urls[name]],address_raw=None)
                continue
            if text.startswith('地址:'):
                schools[current]['address_raw']=text[3:];continue
            if text in ('专升本','高中起点本科','高职（专科）'):level=text;cat=None;continue
            if level!='专升本':continue
            form_match=re.match(r'^(.+?)(非脱产|脱产)(.*)$',text)
            if form_match:cat,form,text=form_match.groups()
            for code,major in re.findall(r'\((\d{3})\)(.*?)(?=\(\d{3}\)|$)',text):
                row=program('hunan',schools[current]['institution_name'],major,cat,urls[name],
                    institution_code=current,institution_code_raw=current,source_paragraph=number)
                row.update(major_code=code,major_code_raw=code,study_form=form,enrollment_scope='湖南省')
                plans.append(row)
    if len(plans)!=independent or len(plans)!=677:raise ValueError('湖南目录专业计数不完整')
    controls=[]
    for year in [2024,2025]:
        name=f'controls-{year}.html'
        rows=[r for r in tables(root/name)[0] if len(r)==3 and r[0]=='专科起点升本科']
        if len(rows)!=8:raise ValueError('湖南省控线缺失')
        controls.extend(control('hunan',year,r[1],r[2],urls[name]) for r in rows)
    collections=[]
    for round_no in [1,2]:
        name=f'collection-2025-{round_no}.html'
        rows=[r for r in tables(root/name)[0] if len(r)==7 and r[1]=='专升本']
        if len(rows)!={1:124,2:114}[round_no]:raise ValueError('湖南征集计划不完整')
        for seq,level,cat,form,code,school,count in rows:
            schools.setdefault(code,dict(institution_code=code,institution_name=school,address_raw=None,source_urls=[urls[name]]))
            if urls[name] not in schools[code]['source_urls']:schools[code]['source_urls'].append(urls[name])
            collections.append(dict(province='hunan',year=2025,institution_code=code,institution_code_raw=code,
                institution_name=school,level=level,category_code=category(cat),category_name=CATEGORIES[category(cat)],
                category_name_raw=cat,study_form=form,plan_count=int(count),major_code=None,major_name=None,
                line_type='征集计划',round=f'第{round_no}次征集志愿',granularity='institution_category',
                source_url=urls[name],source_table_row=int(seq)+1))
    included={r['institution_code'] for r in plans+collections}
    return plans,controls,collections,[v for k,v in schools.items() if k in included]

def jiangxi(root,urls):
    plans=[]
    schools={'jxnu':'江西师范大学','jxau':'江西农业大学','nchu':'南昌航空大学','gnnu':'赣南师范大学'}
    for key,school in schools.items():
        name=f'brochure-{key}-2026.html';ts=tables(root/name);url=urls[name]
        if key=='jxnu':
            table=next(t for t in ts if len(t)==25 and t[0][1]=='专业代码')
            for num,code,major,kind,cat,discipline,duration,subjects,scope in table[1:]:
                row=program('jiangxi',school,major,cat,url,source_table_row=int(num)+1)
                row.update(major_code=code,major_code_raw=code,study_form='非脱产',study_duration_raw=duration,
                    enrollment_scope=scope,exam_subjects_raw=subjects,discipline_raw=discipline)
                row.update(tuition_amount=2100 if row['category_code']=='12' else 1700,tuition_unit='per_academic_year',
                    tuition_raw='2100元/学年' if row['category_code']=='12' else '1700元/学年')
                plans.append(row)
        elif key=='jxau':
            table=next(t for t in ts if t and t[0]==['层次','序号','招生专业','学制','科类','统考科目','学习形式'])
            for index,r in enumerate(table[1:],2):
                level,num,major,duration,cat,subjects,form=r
                if level!='专科起点升本科':continue
                row=program('jiangxi',school,major,cat,url,source_table_row=index)
                row.update(study_form=form,study_duration_raw=duration,exam_subjects_raw=subjects,
                    tuition_amount=1700,tuition_unit='per_academic_year',tuition_raw='1700元/年')
                plans.append(row)
        elif key=='nchu':
            table=next(t for t in ts if t and t[0]==['层次','专业名称','专业学院','专业属性','学制']*2)
            for index,r in enumerate(table[1:],2):
                for start in [0,5]:
                    level,major,college,cat,duration=r[start:start+5]
                    if level!='专升本':continue
                    row=program('jiangxi',school,major,cat,url,source_table_row=index,source_table_column=start+1)
                    row.update(study_duration_raw=duration,tuition_amount=2100 if row['category_code']=='12' else 1700,
                        tuition_unit='per_academic_year',tuition_raw='2100元/年' if row['category_code']=='12' else '1700元/年')
                    plans.append(row)
        else:
            table=next(t for t in ts if t and t[0]==['号','院校代码','院校名称','专业代码','专业名称','层次','科类','学习形式','学制'])
            # Verify the explicit English exam column independently of academic discipline.
            subjects=next(t for t in ts if t and t[0][-1]=='统考公共课')
            subject_by_major={r[1]:r[-1] for r in subjects[1:]}
            for index,r in enumerate(table[1:],2):
                num,inst_code,school_name,code,major,level,cat,form,duration=r
                if level!='专升本':continue
                if '英语' not in subject_by_major[major]:raise ValueError('赣南师大外语科目变化')
                row=program('jiangxi',school,major,cat,url,source_table_row=index,institution_code_raw=inst_code)
                row.update(major_code=code,major_code_raw=code,study_form=form,study_duration_raw=duration+'年',foreign_language='英语')
                plans.append(row)
    if len(plans)!=85:raise ValueError('江西4校目录计数不符')
    text=plain((root/'controls-2025.html').read_text()).split('专科起点升本科的',1)[1].split('。',1)[0]
    pairs=re.findall(r'([^；]+?类)(\d+)分',text)
    if len(pairs)!=8:raise ValueError('江西普通省控线缺失或混入专项')
    controls=[control('jiangxi',2025,cat,score,urls['controls-2025.html']) for cat,score in pairs]
    from scripts.jiangxi_catalog_extensions import catalogues
    extra, extra_schools=catalogues(root,urls,program,CATEGORIES)
    plans.extend(extra)
    return plans,controls,[],[dict(institution_name=school,source_urls=[urls[f'brochure-{key}-2026.html']]) for key,school in schools.items()]+extra_schools

def normalize(province,plans,collections,schools):
    sheet=xlrd.open_workbook(MOE_PATH).sheet_by_index(0)
    moe={str(int(float(sheet.cell_value(i,2))))[-5:]:(str(sheet.cell_value(i,1)),str(int(float(sheet.cell_value(i,2)))),str(sheet.cell_value(i,4)).removesuffix('市'))
         for i in range(3,sheet.nrows) if str(sheet.cell_value(i,2)).replace('.','',1).isdigit()}
    clean=lambda s:s.replace('（','(').replace('）',')')
    by_name={clean(v[0]):v for v in moe.values()}
    by_school={}
    cities=['长沙','株洲','湘潭','衡阳','邵阳','岳阳','常德','张家界','益阳','郴州','永州','怀化','娄底','湘西']
    for school in schools:
        if province=='jiangxi':
            official,code,city=by_name[clean(school['institution_name'])];school.update(institution_code=code,city=city,city_source_url=MOE_URL,identity_basis='教育部学校标识码')
        else:
            code=school['institution_code'];entry=moe.get(code)
            if entry:
                official,national,city=entry
                if clean(official)!=clean(school['institution_name']):raise ValueError(('湖南院校代码/名称不符',school,entry))
                city={'湘西土家族苗族自治州':'湘西'}.get(city,city)
                school.update(city=city,city_source_url=MOE_URL,national_institution_code=national)
            else:
                matches=[c for c in cities if c in (school['address_raw'] or '')]
                # Adult colleges do not appear in the ordinary-university list.
                city=matches[0] if len(matches)==1 else None
                if not city:raise ValueError(('无法核实院校城市',school))
                school.update(city=city,city_source_url=school['source_urls'][0])
            school['identity_basis']='湖南省招生院校代码；按代码跨年关联，原始校名保留于来源记录'
        school['province']=province
        by_school[school['institution_name']]=school
    for row in plans:
        school=by_school[row['institution_name']];row['institution_code']=school['institution_code']
        if not row.get('major_code'):row['major_code']='catalog-'+sha256(row['major_name'].encode()).hexdigest()[:16]
    return schools

def run(refresh=False):
    for province,parse in [('hunan',hunan),('jiangxi',jiangxi)]:
        root=DATA/'sources'/province;urls=json.loads((root/'source-urls.json').read_text())
        if refresh:
            for name,url in urls.items():
                try:content=urlopen(Request(url,headers={'User-Agent':'Mozilla/5.0'}),timeout=30).read()
                except OSError:
                    # macOS curl supports the Hunan government TLS curve used by this site.
                    content=subprocess.check_output(['curl','--fail','--silent','--show-error','--location','--max-time','30',url])
                (root/name).write_bytes(content)
        plans,controls,collections,schools=parse(root,urls)
        normalize(province,plans,collections,schools)
        keys=[(r['institution_code'],r['year'],r['major_code'],r['line_type'],r['round']) for r in plans]
        if len(keys)!=len(set(keys)):raise ValueError('专业目录重复')
        for suffix,records in [('adult-programs',plans),('adult-control-scores',controls),('adult-category-collection-plans',collections),('institutions',schools)]:
            (DATA/f'{province}-{suffix}.json').write_text(json.dumps(records,ensure_ascii=False,indent=2)+'\n')
        sources=[dict(path=str((root/name).relative_to(DATA)),url=url,sha256=sha256((root/name).read_bytes()).hexdigest())for name,url in urls.items()]
        sources.append(dict(path=str(MOE_PATH.relative_to(DATA)),url=MOE_URL,sha256=sha256(MOE_PATH.read_bytes()).hexdigest()))
        if province=='jiangxi':
            for local in ['brochure-xyc-2026-reviewed.json','brochure-ncu-2026-reviewed.json']:
                sources.append(dict(path=str((root/local).relative_to(DATA)),url=urls['brochure-xyc-2026-2.jpg' if 'xyc' in local else 'brochure-ncu-2026.pdf'],sha256=sha256((root/local).read_bytes()).hexdigest(),role='visually_reviewed_extraction'))
            for suffix in ['txt','doc']:
                local=DATA/f'sources/hubei/exam-categories-2026.{suffix}'
                sources.append(dict(path=str(local.relative_to(DATA)),url=json.loads((DATA/'sources/hubei/source-urls.json').read_text())['exam-categories-2026.doc'],sha256=sha256(local.read_bytes()).hexdigest(),role='national_exam_category_crosscheck'))
        manifest=dict(province=province,catalog_year=2026,counts=dict(institutions=len(schools),programs=len(plans),controls=len(controls),category_collections=len(collections)),sources=sources,
            limitations=['专业目录非人数计划；未公布字段为null','暂无院校实际录取分数线','暂无2027专业目录', f'江西覆盖{len(schools)}校官方简章及教学点公告，非全省完整目录；仅2025普通统考省控线；未核实科类及科目冲突不作备考目标' if province=='jiangxi' else '湖南2026专业目录为湖南日报7—9版；未公布人数、学费、学制和专业教学点；历史征集按科类/轮次单列'])
        (DATA/f'{province}-manifest.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+'\n')
        print(province,manifest['counts'])

if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--refresh',action='store_true');run(parser.parse_args().refresh)
