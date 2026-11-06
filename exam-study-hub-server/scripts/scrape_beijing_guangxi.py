"""Replay/fetch the complete 2026 official Beijing and Guangxi adult 专升本 catalogues."""
import argparse
from collections import Counter
from hashlib import sha256
import json
from pathlib import Path
import re
import subprocess
import xlrd
from scripts.adult_source_utils import TableReader
from scripts.scrape_hunan_jiangxi import CATEGORIES, MOE_PATH, MOE_URL, category, plain

DATA=Path(__file__).resolve().parent.parent/'scraped-data'
CONFIG={'beijing':dict(name='北京',programs=287,schools=45),'guangxi':dict(name='广西',programs=569,schools=55)}


def html(path):
    data=path.read_bytes()
    try:return data.decode('utf-8')
    except UnicodeDecodeError:return data.decode('gb18030')


def beijing_fields(path):
    reader=TableReader();reader.feed(html(path));fields={}
    for table in reader.tables:
        for i,row in enumerate(table):
            cells=[c[1]for c in row]
            if len(cells)==2 and cells[0].endswith('：'):fields[cells[0][:-1]]=cells[1]
            elif cells==['备注']and i+1<len(table):fields['备注']=''.join(c[1]for c in table[i+1])
    return fields


def paragraphs(path):return [plain(p)for p in re.findall(r'<p\b[^>]*>(.*?)</p>',html(path),re.S|re.I)]


def school_headers(province,root):
    if province=='beijing':
        source=html(root/'catalog-2026.html');result={}
        for m in re.finditer(r"goschool\('(\d+)'\)[^>]*>(.*?)</a>(.*?)<br\s*/?>",source,re.S|re.I):
            code,name,address=m.groups();result[code]=(plain(name),plain(address).strip('()（）'))
        return result
    result={};ps=paragraphs(root/'catalog-2026.html')
    for i,p in enumerate(ps):
        m=re.fullmatch(r'(\d{5})(.+)',p)
        if m:
            if '地址：'not in ps[i+1]:raise ValueError('Unrecognized school address paragraph')
            result[m[1]]=(m[2],ps[i+1])
    return result


def parse_catalogue(province,root,urls):
    plans=[];schools=school_headers(province,root)
    if province=='beijing':
        text=plain(html(root/'catalog-2026.html'))
        if '2026年北京成人高等学校招生专业目录'not in text:raise ValueError('Wrong Beijing catalogue year')
        index=re.findall(r"gospecialty\('(\d+)','(\d+)'\)",html(root/'catalog-2026.html'))
        if len(index)!=287 or len(set(index))!=287:raise ValueError('Changed Beijing catalogue coverage')
        for school_code,major_code in index:
            filename=f'detail-2026-{major_code}.html';f=beijing_fields(root/filename)
            required=['专业代码','专业名称','专业层次','专业类别','学制','学习形式','招生范围','外语语种','统考科目','上课地点','是否专业课加试','加试专业课名称']
            if any(k not in f for k in required)or f['专业代码']!=major_code or f['专业层次']!='专升本':raise ValueError('Incomplete Beijing professional detail')
            cat=re.sub(r'\(专升本\)$','',f['专业类别']);code=category(cat)
            scope=f['招生范围'];restricted=scope.startswith(('直属单位','委托培养'))or bool(re.search(r'只招|仅招|不面向社会',scope))
            remark='；'.join(x for x in [scope,f.get('备注'),f"专业课加试：{f['是否专业课加试']}"+(f"（{f['加试专业课名称']}）"if f['加试专业课名称']else'')]if x)
            plans.append(dict(province=province,institution_code=school_code,institution_name=schools[school_code][0],
                major_code=major_code,major_name=f['专业名称'],major_direction=f.get('专业方向')or None,
                category_code=code,category_name=CATEGORIES[code],category_name_raw=f['专业类别'],study_form=f['学习形式'],
                study_duration_raw=f['学制']+'年',foreign_language=f['外语语种'],exam_subjects_raw=f['统考科目'],
                enrollment_scope=scope,teaching_site=f['上课地点']or None,tuition_raw=None,remarks=remark,
                selection_eligible=not restricted,restriction_note='限定单位或委托培养，不作为普通备考目标'if restricted else None,
                source_url=urls[filename]+'?'+f'schoolcode={school_code}&specialtycode={major_code}&examId=6311',source_filename=filename,source_query_body=f'schoolcode={school_code}&specialtycode={major_code}&examId=6311'))
    else:
        if '本目录为2026年在广西招生的成人高校和招生专业'not in plain(html(root/'catalog-2026.html')):raise ValueError('Wrong Guangxi catalogue year')
        if '英语（专升本）'not in plain(html(root/'exam-2026.html')):raise ValueError('Unverified Guangxi foreign-language exam')
        current=None;level=None;all_level=Counter()
        for index,p in enumerate(paragraphs(root/'catalog-2026.html'),1):
            m=re.fullmatch(r'(\d{5})(.+)',p)
            if m:current=m[1];level=None;continue
            if p in ['专升本','高中起点本科','高职（专科）']:level=p;continue
            if not re.match(r'^\d{3}\D',p):continue
            if not current or not level:raise ValueError('Programme without school/level')
            all_level[level]+=1
            if level!='专升本':continue
            m=re.fullmatch(r'(\d{3})(.+?)(文史、中医类|文史中医类|经济管理类|理工类|艺术类|法学类|教育学类|农学类|医学类)(二年半|三年|二年)(非脱产|脱产)\((.*)\)',p)
            if not m:raise ValueError('Unparsed Guangxi programme: '+p)
            major_code,major,cat,duration,form,details=m.groups();parts=details.split(',');scope=parts[0]
            if len(parts)<2 or scope not in ['社会招生','直属单位','委托培养','直属与社会']:raise ValueError('Changed Guangxi programme schema')
            fee=parts[1];site=parts[2]if len(parts)>2 else None
            if fee=='广西壮族自治区南宁市西乡塘区罗文大道33号':site=fee;fee=None
            restricted=scope in ['直属单位','委托培养']or bool(re.search(r'只招|仅招|限.{0,16}职工|不面向社会',details))
            code=category(cat)
            plans.append(dict(province=province,institution_code=current,institution_name=schools[current][0],major_code=major_code,
                major_name=major,major_direction=None,category_code=code,category_name=CATEGORIES[code],category_name_raw=cat,
                study_form=form,study_duration_raw=duration,foreign_language='英语',exam_subjects_raw=None,enrollment_scope=scope,
                teaching_site=site or None,tuition_raw=fee or None,remarks=details,selection_eligible=not restricted,
                restriction_note='单位、委托培养或职工限制，不作为普通备考目标'if restricted else None,
                source_url=urls['catalog-2026.html'],source_filename='catalog-2026.html',source_paragraph=index))
        if all_level!={'专升本':569,'高职（专科）':356,'高中起点本科':63}:raise ValueError('All-level catalogue counts changed')
    for r in plans:
        r.update(year=2026,level='专升本',major_code_raw=r['major_code'],institution_code_raw=r['institution_code'],
            major_name_raw=r['major_name'],plan_count=None,line_type='招生专业目录',round='省级公开招生专业目录')
        fee=r['tuition_raw']or'';m=re.fullmatch(r'(\d+)(?:\.0)?(?:元/(?:学年(?:/人)?|人·年|年)|/学年)',fee)
        r['tuition_amount']=int(m[1])if m else None;r['tuition_unit']='per_academic_year'if m else None
        if re.fullmatch(r'\d+(?:元)?',fee):r['remarks']+='；收费未注明计费周期，不可当作年学费。'
    if len(plans)!=CONFIG[province]['programs']or len({r['institution_code']for r in plans})!=CONFIG[province]['schools']:raise ValueError('Incomplete public catalogue')
    if len({(r['institution_code'],r['major_code'])for r in plans})!=len(plans):raise ValueError('Duplicate school/major keys')
    return plans


def school_identities(province,records,root,urls):
    sh=xlrd.open_workbook(MOE_PATH).sheet_by_index(0);clean=lambda s:s.replace('（','(').replace('）',')')
    moe={clean(str(sh.cell_value(i,1))):(str(int(float(sh.cell_value(i,2)))),str(sh.cell_value(i,4)).removesuffix('市'))for i in range(3,sh.nrows)if str(sh.cell_value(i,2)).replace('.','',1).isdigit()}
    aliases={'华北电力大学(北京)':'华北电力大学'};headers=school_headers(province,root);schools={}
    for r in records:
        code=r['institution_code'];name=r['institution_name'];national=None
        if code in schools:continue
        normalized=aliases.get(clean(name),clean(name))
        if normalized in moe:
            national,city=moe[normalized];source=MOE_URL
            if province=='guangxi'and national[-5:]!=code and (name,code,national[-5:])not in [('广西警察学院','11547','13520'),('广西职业师范学院','50869','14684')]:raise ValueError('National identity mismatch')
        else:
            address=headers[code][1]
            if province=='beijing'and ('北京'in address or re.search(r'东城区|西城区|朝阳区|石景山区',address)):city='北京'
            elif province=='guangxi'and '南宁市'in address:city='南宁'
            else:raise ValueError(f'Unverified school headquarters: {name}: {address}')
            source=urls['catalog-2026.html']
        schools[code]=dict(province=province,institution_code=code,institution_name=name,city=city,national_institution_code=national,
            identity_basis='考试院公开目录院校编码；校本部城市按教育部高校名单或目录院校官方地址核验',city_source_url=source,
            source_urls=list(dict.fromkeys(x['source_url']for x in records if x['institution_code']==code)))
    return list(schools.values())


def parse_controls(province,root,urls):
    records=[]
    for year in [2024,2025]:
        if province=='beijing':
            reviewed=json.loads((root/'controls-reviewed.json').read_text())[str(year)]
            if sha256((root/f'controls-{year}.png').read_bytes()).hexdigest()!=reviewed['source_sha256']:raise ValueError('Beijing control image changed; visual review required')
            values=[(code,CATEGORIES[code],score)for code,score in reviewed['ordinary_zsb_controls'].items()]
        else:
            text=plain(html(root/f'controls-{year}.html')).split('一、专科起点升本科',1)[1].split('二、高中起点',1)[0]
            pairs=re.findall(r'(文史、中医类|艺术类|理工类|经济管理类|法学类|教育学类|农学类|医学类)：(\d+)分',text)
            if len(pairs)!=8:raise ValueError('Incomplete Guangxi control scores')
            values=[(category(raw),raw,int(score))for raw,score in pairs]
        for code,raw,score in values:records.append(dict(province=province,year=year,level='专升本',category_code=code,
            category_name=CATEGORIES[code],category_name_raw=raw,score=score,line_type='省控线',round='统考生',source_url=urls[f'controls-{year}.html']))
    return records


def run(refresh=False):
    for province,config in CONFIG.items():
        root=DATA/'sources'/province;urls=json.loads((root/'source-urls.json').read_text());requests=json.loads((root/'source-requests.json').read_text())if(root/'source-requests.json').exists()else{}
        if refresh:
            for name,url in urls.items():
                command=['curl','-fsSL','--max-time','35',url]
                if name in requests:command+=['--data',requests[name]['body']]
                data=subprocess.check_output(command);temp=root/(name+'.download');temp.write_bytes(data);temp.replace(root/name)
        plans=parse_catalogue(province,root,urls);schools=school_identities(province,plans,root,urls);controls=parse_controls(province,root,urls)
        restricted=sum(not r['selection_eligible']for r in plans);pairs=len({(r['institution_code'],r['major_name'],r['major_direction'])for r in plans})
        note=f'2026考试院公开专升本目录{len(schools)}校{len(plans)}条记录（{pairs}个院校专业及方向组合）；2024—2025省市控线16条单列。{restricted}条限定招生记录不作普通备考目标；人数未公布，暂无院校实际录取线'
        for suffix,data in [('institutions',schools),('adult-programs',plans),('adult-control-scores',controls),('adult-category-collection-plans',[])]:
            (DATA/f'{province}-{suffix}.json').write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n')
        sources=[dict(path=str((root/name).relative_to(DATA)),url=url,sha256=sha256((root/name).read_bytes()).hexdigest(),**requests.get(name,{}))for name,url in urls.items()]
        sources.append(dict(path=str(MOE_PATH.relative_to(DATA)),url=MOE_URL,sha256=sha256(MOE_PATH.read_bytes()).hexdigest()))
        if province=='beijing':
            file=root/'controls-reviewed.json';sources.append(dict(path=str(file.relative_to(DATA)),url=urls['controls-index.html'],sha256=sha256(file.read_bytes()).hexdigest(),role='visually_reviewed_control_extraction'))
        manifest=dict(province=province,province_name=config['name'],catalog_year=2026,coverage_note=note,
            counts=dict(institutions=len(schools),programs=len(plans),controls=len(controls),category_collections=0),
            public_query=dict(all_level_records=len(plans)if province=='beijing'else 988,zsb_records=len(plans),
                completeness='all_index_entries_and_287_details'if province=='beijing'else'all_official_catalogue_paragraphs',
                ordinary_target_excluded_records=restricted,school_major_direction_pairs=pairs),sources=sources,
            limitations=['2026目录仅作2027备考历史参考，不代表2027招生计划','省市控线不是院校实际录取线；未公布人数，不推算人数',
                '北京目录未公开学费；原始采集使用公开POST表单，回链加2026对应examId=6311等参数支持GET查看'if province=='beijing'else'广西授课地点未全部列举，缺失不推测；广西警察学院11547及广西职业师范学院50869为目录招生编码，分别不同于教育部13520及14684；医学资格等要求以官方为准'])
        (DATA/f'{province}-manifest.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+'\n');print(province,manifest['counts'],note)

if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--refresh',action='store_true');run(parser.parse_args().refresh)
