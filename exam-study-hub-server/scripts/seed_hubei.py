"""Idempotent scoped Hubei import; category collections never become major plans."""
import json
from pathlib import Path
from app.db.session import SessionLocal
from app.models.catalog import AdmissionPlan, Institution, Province, ProvinceControlScore

DATA = Path(__file__).resolve().parent.parent/'scraped-data'
NOTE = '已接入5所院校2026专升本简章85条专业、2023—2025省控线24条和2024—2025院校科类征集25条；非全省完整目录，暂无院校录取线'
FIELDS = ('major_name','level','category_code','category_name','plan_count','study_form','teaching_site','tuition_amount','tuition_unit','tuition_raw','enrollment_scope')
DETAILS = ('major_code_raw','study_duration_raw','foreign_language','national_major_code','category_name_raw','discipline_raw','category_source_url','source_table_row','major_name_raw')


def import_hubei(db, data_dir=DATA):
    def read(name):
        records = json.loads((data_dir/name).read_text())
        if any(r['province'] != 'hubei' for r in records): raise ValueError('湖北文件包含其他省份')
        return records
    schools = read('hubei-institutions.json')
    plans = read('hubei-adult-programs.json')
    controls = read('hubei-adult-control-scores.json')
    collections = read('hubei-adult-category-collection-plans.json')
    keys = [(r['institution_code'],r['year'],r['major_code'],r['line_type'],r['round']) for r in plans]
    if len(keys) != len(set(keys)): raise ValueError('湖北目录重复')
    if any(r['level'] != '专升本' or r['line_type'] != '招生专业目录' or r['plan_count'] is not None or not r['category_name'] for r in plans):
        raise ValueError('湖北目录口径不符')
    if any(r['granularity'] != 'institution_category' or r['major_name'] is not None or r['level'] != '专升本' for r in collections):
        raise ValueError('湖北征集计划不得分配到具体专业')
    province = db.query(Province).filter_by(code='hubei').one_or_none()
    if province is None:
        province = Province(code='hubei',name='湖北');db.add(province);db.flush()
    province.note = NOTE
    counts = dict(institutions_added=0,plans_added=0,controls_added=0)
    instances = {}
    for record in schools:
        school = db.query(Institution).filter_by(province_id=province.id,code=record['institution_code']).one_or_none()
        if school is None:
            school = Institution(province_id=province.id,code=record['institution_code']);db.add(school);counts['institutions_added'] += 1
        school.name, school.city = record['institution_name'], record['city']
        school.supplemental_data = {**(school.supplemental_data or {}),'active_catalog_year':2026,
            'coverage_note':NOTE,'identity_basis':record['identity_basis'],'city_source_url':record['city_source_url'],
            'source_codes_by_year':record['official_codes_by_year'],'plan_details':{},
            'category_collection_plans':[r for r in collections if r['institution_code']==record['institution_code']]}
        instances[school.code] = school
    db.flush()
    details = {code:{} for code in instances}
    for record in plans:
        school = instances[record['institution_code']]
        if school.name != record['institution_name']: raise ValueError('湖北院校身份不符')
        key = dict(institution_id=school.id,**{k:record[k] for k in ('year','major_code','line_type','round')})
        plan = db.query(AdmissionPlan).filter_by(**key).one_or_none()
        if plan is None: plan = AdmissionPlan(**key);db.add(plan);counts['plans_added'] += 1
        for field in FIELDS: setattr(plan,field,record.get(field))
        plan.source = record['source_url']
        details[school.code][f'{plan.year}/{plan.round}/{plan.major_code}'] = {f:record.get(f) for f in DETAILS}
    for code,school in instances.items():school.supplemental_data = {**school.supplemental_data,'plan_details':details[code]}
    for record in controls:
        if record['level']!='专升本' or record['line_type']!='省控线':raise ValueError('湖北省控线口径不符')
        key = dict(province_id=province.id,**{k:record[k] for k in ('year','level','category_name','line_type','round')})
        line = db.query(ProvinceControlScore).filter_by(**key).one_or_none()
        if line is None:line=ProvinceControlScore(**key);db.add(line);counts['controls_added'] += 1
        line.category_code,line.score,line.source = record['category_code'],record['score'],record['source_url']
    db.flush()
    return counts


def run():
    with SessionLocal.begin() as db: counts=import_hubei(db)
    print('湖北数据导入完成：'+json.dumps(counts,ensure_ascii=False))


if __name__=='__main__':run()
