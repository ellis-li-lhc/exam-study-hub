"""Validated, province-scoped import of archived adult professional catalogues."""
import json
from hashlib import sha256
from pathlib import Path
from app.models.catalog import AdmissionPlan, Institution, Province, ProvinceControlScore

DATA=Path(__file__).resolve().parent.parent/'scraped-data'
FIELDS=('major_name','level','category_code','category_name','plan_count','study_form','teaching_site','tuition_amount','tuition_unit','tuition_raw','enrollment_scope')
DETAILS=('major_code_raw','study_duration_raw','foreign_language','category_name_raw','discipline_raw','source_table_row','source_table_column','source_paragraph','institution_code_raw','exam_subjects_raw','minimum_study_duration_raw','remarks','major_direction','selection_eligible','category_source_url','teaching_site_address_raw','source_page','source_query_page','source_filename','restriction_note')


def import_catalog(db,province_code,province_name,coverage_note,data_dir=DATA):
    name,note=province_name,coverage_note
    manifest=json.loads((data_dir/f'{province_code}-manifest.json').read_text())
    for source in manifest['sources']:
        if sha256((data_dir/source['path']).read_bytes()).hexdigest()!=source['sha256']:raise ValueError('原始来源校验失败，请重新运行抓取脚本')
    def read(suffix):
        rows=json.loads((data_dir/f'{province_code}-{suffix}.json').read_text())
        if any(r['province']!=province_code for r in rows):raise ValueError('数据文件混入其他省份')
        return rows
    schools=read('institutions');plans=read('adult-programs');controls=read('adult-control-scores');collections=read('adult-category-collection-plans')
    actual=dict(institutions=len(schools),programs=len(plans),controls=len(controls),category_collections=len(collections))
    if actual!=manifest['counts']:raise ValueError('数据条数与清单不符')
    school_codes={r['institution_code'] for r in schools}
    if len(school_codes)!=len(schools):raise ValueError('院校编码重复')
    keys=[(r['institution_code'],r['year'],r['major_code'],r['line_type'],r['round']) for r in plans]
    if len(keys)!=len(set(keys)):raise ValueError('专业目录重复')
    if any(r['institution_code'] not in school_codes or r['level']!='专升本' or r['line_type']!='招生专业目录' or r['plan_count'] is not None or (not r['category_name'] and r.get('selection_eligible') is not False) for r in plans):raise ValueError('专业目录口径不符')
    collection_keys=[(r['institution_code'],r['year'],r['category_code'],r['round'],r['study_form'])for r in collections]
    if len(collection_keys)!=len(set(collection_keys)):raise ValueError('科类征集重复')
    if any(r['institution_code'] not in school_codes or r['granularity']!='institution_category' or r['major_name'] is not None or r['level']!='专升本' for r in collections):raise ValueError('科类征集不能变成专业计划')
    province=db.query(Province).filter_by(code=province_code).one_or_none()
    if province is None:province=Province(code=province_code,name=name);db.add(province);db.flush()
    province.note=note
    counts=dict(institutions_added=0,plans_added=0,controls_added=0);instances={}
    for record in schools:
        code=record['institution_code'];school=db.query(Institution).filter_by(province_id=province.id,code=code).one_or_none()
        if school is None:school=Institution(province_id=province.id,code=code);db.add(school);counts['institutions_added']+=1
        school.name,school.city=record['institution_name'],record['city']
        school.supplemental_data={**(school.supplemental_data or {}),'active_catalog_year':2026,'coverage_note':note,
            'identity_basis':record['identity_basis'],'city_source_url':record['city_source_url'],'source_urls':record['source_urls'],
            'category_collection_plans':[r for r in collections if r['institution_code']==code],'plan_details':{}}
        instances[code]=school
    db.flush();details={code:{} for code in instances}
    for record in plans:
        school=instances[record['institution_code']]
        if school.name!=record['institution_name']:raise ValueError('目录院校身份不符')
        key=dict(institution_id=school.id,**{k:record[k]for k in ('year','major_code','line_type','round')})
        plan=db.query(AdmissionPlan).filter_by(**key).one_or_none()
        if plan is None:plan=AdmissionPlan(**key);db.add(plan);counts['plans_added']+=1
        for field in FIELDS:setattr(plan,field,record.get(field))
        plan.source=record['source_url']
        details[school.code][f'{plan.year}/{plan.round}/{plan.major_code}']={f:record.get(f,True)if f=='selection_eligible'else record.get(f)for f in DETAILS}
    for code,school in instances.items():school.supplemental_data={**school.supplemental_data,'plan_details':details[code]}
    for record in controls:
        if record['level']!='专升本' or record['line_type']!='省控线' or record['round']!='统考生':raise ValueError('省控线口径不符')
        key=dict(province_id=province.id,**{k:record[k]for k in ('year','level','category_name','line_type','round')})
        line=db.query(ProvinceControlScore).filter_by(**key).one_or_none()
        if line is None:line=ProvinceControlScore(**key);db.add(line);counts['controls_added']+=1
        line.category_code,line.score,line.source=record['category_code'],record['score'],record['source_url']
    db.flush();return counts
