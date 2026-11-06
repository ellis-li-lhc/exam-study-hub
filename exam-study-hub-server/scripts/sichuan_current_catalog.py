"""2026-11-05 Sichuan second-stage plans; retain August catalogue as history."""
from hashlib import sha256
import json
import re
from app.models.catalog import AdmissionPlan, Institution, Province
from scripts.adult_catalog_import import DATA, FIELDS, DETAILS
from scripts.adult_source_utils import TableReader
from scripts.scrape_hubei import expand
from scripts.scrape_hunan_jiangxi import CATEGORIES, category

ROUND='2026年第二次公布'
LINE_TYPE='招生专业计划'
COVERAGE='四川2026年11月5日第二次公布49校1240条专升本计划，合计49031人；10条限定招生不作普通目标。8月1329条目录另存历史，不参与当前匹配；2024—2025省控线16条单列，暂无院校实际录取线'


def parse_current(data_dir=DATA):
    root=data_dir/'sources/sichuan';urls=json.loads((root/'source-urls.json').read_text())
    index=(root/'current-plans-index-2026.html').read_text()
    if '第二阶段编制工作已经完成'not in index or '2026/11/5'not in index:raise ValueError('Unverified Sichuan plan release')
    reader=TableReader();reader.feed((root/'current-plans-2026.html').read_text())
    table=next(t for t in reader.tables if t and '计划数'in [c[1]for c in t[0]])
    rows=list(expand(table));records=[]
    if rows[0]!=['院校代号','院校名称','专业代号','专业名称','科类','学制','收费标准','学习形式','计划数','专升本考试码','上课地点','上课地点','备注']:raise ValueError('Changed Sichuan second-stage headers')
    for row_no,row in enumerate(rows[1:],1):
        if len(row)!=13:raise ValueError('Incomplete Sichuan plan row')
        college,school,raw_code,major,cat,duration,fee,form,count,exam,site,address,remark=row
        code=raw_code.zfill(6);category_code=category(cat)
        if not re.fullmatch(r'\d{3}',college)or not re.fullmatch(r'\d{5,6}',raw_code)or not code.startswith(college):raise ValueError('Invalid source institution/professional code')
        if not count.isdigit()or int(count)<=0 or category_code!=str(10+int(exam)):raise ValueError('Invalid plan count or category')
        restricted=bool(re.search('限招|仅招|只招|不面向社会|委托培养',remark));m=re.fullmatch(r'(\d+)元/年',fee)
        records.append(dict(province='sichuan',year=2026,institution_code=college,institution_code_raw=college,institution_name=school,
            major_code=code,major_code_raw=raw_code,major_name=major,major_name_raw=major,level='专升本',category_code=category_code,
            category_name=CATEGORIES[category_code],category_name_raw=cat,plan_count=int(count),study_form=form,
            study_duration_raw=duration,foreign_language=None,teaching_site=site,teaching_site_address_raw=address,
            tuition_raw=fee,tuition_amount=int(m[1])if m else None,tuition_unit='per_academic_year'if m else None,
            enrollment_scope='四川省',remarks=remark or None,selection_eligible=not restricted,
            restriction_note='单位或在职消防救援人员限制，不作为普通备考目标'if restricted else None,
            line_type=LINE_TYPE,round=ROUND,source_url=urls['current-plans-2026.html'],source_table_row=row_no,
            source_filename='current-plans-2026.html'))
    if len(records)!=1240 or len({r['institution_code']for r in records})!=49 or sum(r['plan_count']for r in records)!=49031:raise ValueError('Current Sichuan coverage changed')
    if len({(r['institution_code'],r['major_code'])for r in records})!=1240:raise ValueError('Duplicate current plan keys')
    return records


def run(data_dir=DATA):
    records=parse_current(data_dir);root=data_dir/'sources/sichuan';urls=json.loads((root/'source-urls.json').read_text())
    (data_dir/'sichuan-adult-current-plans.json').write_text(json.dumps(records,ensure_ascii=False,indent=2)+'\n')
    old=json.loads((data_dir/'sichuan-adult-programs.json').read_text());oldkeys={(r['institution_code'],r['major_code'])for r in old};newkeys={(r['institution_code'],r['major_code'])for r in records}
    manifest=dict(province='sichuan',catalog_year=2026,release_date='2026-11-05',active_catalog_round=ROUND,coverage_note=COVERAGE,
        counts=dict(institutions=49,programs=1240,plan_count=49031,ordinary_target_excluded_records=10),
        superseded_catalogue=dict(records=1329,removed_professional_keys=len(oldkeys-newkeys),new_professional_keys=len(newkeys-oldkeys)),
        sources=[dict(path=str((root/n).relative_to(data_dir)),url=urls[n],sha256=sha256((root/n).read_bytes()).hexdigest())for n in ['current-plans-2026.html','current-plans-index-2026.html']],
        limitations=['人数为2026年第二次公布计划，非实际录取人数或2027计划','八月目录保留历史，不用于当前目标匹配','专业代号原文保留；不足6位时内部补零只用于跨版本关联'])
    (data_dir/'sichuan-current-manifest.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+'\n')
    print('Sichuan current plans:',manifest['counts'],manifest['superseded_catalogue'])


def import_current(db,data_dir=DATA):
    manifest=json.loads((data_dir/'sichuan-current-manifest.json').read_text())
    for s in manifest['sources']:
        if sha256((data_dir/s['path']).read_bytes()).hexdigest()!=s['sha256']:raise ValueError('Sichuan current source hash mismatch')
    records=json.loads((data_dir/'sichuan-adult-current-plans.json').read_text())
    if records!=parse_current(data_dir):raise ValueError('Sichuan current normalized artifact differs from source')
    province=db.query(Province).filter_by(code='sichuan').one();schools={s.code:s for s in db.query(Institution).filter_by(province_id=province.id)}
    province.note=COVERAGE;added=0;details={code:dict((s.supplemental_data or {}).get('plan_details',{}))for code,s in schools.items()}
    for r in records:
        school=schools[r['institution_code']]
        if school.name!=r['institution_name']:raise ValueError('Current school identity changed')
        key=dict(institution_id=school.id,year=2026,major_code=r['major_code'],line_type=LINE_TYPE,round=ROUND)
        plan=db.query(AdmissionPlan).filter_by(**key).one_or_none()
        if plan is None:plan=AdmissionPlan(**key);db.add(plan);added+=1
        for field in FIELDS:setattr(plan,field,r.get(field))
        plan.source=r['source_url'];details[school.code][f'2026/{ROUND}/{plan.major_code}']={f:r.get(f,True)if f=='selection_eligible'else r.get(f)for f in DETAILS}
    for code,school in schools.items():
        supplemental=school.supplemental_data or {}
        school.supplemental_data={**supplemental,'active_catalog_round':ROUND,'coverage_note':COVERAGE,'plan_details':details[code],
            'source_urls':list(dict.fromkeys([*supplemental.get('source_urls',[]),manifest['sources'][0]['url']]))}
    db.flush();return added

if __name__=='__main__':run()
