"""Read-only audit of the nine provinces added in this import batch.

Checks archived-source hashes, normalized artifacts versus the live database,
all source keys/fields, control scores, collections and supported target eligibility.
"""
from collections import Counter
from hashlib import sha256
import json
from pathlib import Path
from app.db.session import SessionLocal
from app.models.catalog import AdmissionPlan, AdmissionScore, Institution, Major, Province, ProvinceControlScore
from app.routers.institutions import read_institutions
from scripts.adult_catalog_import import DATA, FIELDS, DETAILS

PROVINCES=['hubei','hunan','jiangxi','anhui','fujian','sichuan','chongqing','beijing','guangxi']


def audit(db):
    errors=[];summaries=[];checked_sources=set();warnings=[]
    majors={m.name:m for m in db.query(Major)}
    def read(code,suffix):return json.loads((DATA/f'{code}-{suffix}.json').read_text())
    for code in PROVINCES:
        manifest=read(code,'manifest');records=read(code,'adult-programs');schools=read(code,'institutions');controls=read(code,'adult-control-scores');collections=read(code,'adult-category-collection-plans')
        sources=manifest['sources']
        if code=='sichuan':records+=read(code,'adult-current-plans');sources+=read(code,'current-manifest')['sources']
        for source in sources:
            key=source['path'],source['sha256']
            if key in checked_sources:continue
            if sha256((DATA/source['path']).read_bytes()).hexdigest()!=source['sha256']:errors.append(f"Source hash differs: {source['path']}")
            checked_sources.add(key)
        province=db.query(Province).filter_by(code=code).one();instances={s.code:s for s in db.query(Institution).filter_by(province_id=province.id)}
        if len(instances)!=len(schools):errors.append(f'{code}: school count differs')
        for row in schools:
            school=instances.get(row['institution_code'])
            if school is None or school.name!=row['institution_name']or school.city!=row['city']:errors.append(f"{code}: identity differs for {row['institution_code']}")
        def key(r):return r['institution_code'],r['year'],r['major_code'],r['line_type'],r['round']
        expected={key(r):r for r in records}
        if len(expected)!=len(records):errors.append(f'{code}: duplicated normalized professional keys')
        plans=db.query(AdmissionPlan).join(Institution).filter(Institution.province_id==province.id).all()
        actual={(p.institution.code,p.year,p.major_code,p.line_type,p.round):p for p in plans}
        if actual.keys()!=expected.keys():errors.append(f'{code}: database professional keys differ')
        for k,r in expected.items():
            p=actual.get(k)
            if p is None:continue
            for field in FIELDS:
                if getattr(p,field)!=r.get(field):errors.append(f'{code}/{k}: field {field} differs')
            if p.source!=r['source_url']:errors.append(f'{code}/{k}: source differs')
            school=instances[r['institution_code']];details=(school.supplemental_data or{}).get('plan_details',{}).get(f"{r['year']}/{r['round']}/{r['major_code']}",{})
            for f in DETAILS:
                if f in r and details.get(f)!=r[f]:errors.append(f'{code}/{k}: detail {f} differs')
            if r['level']!='专升本':errors.append(f'{code}/{k}: wrong education level')
            if r['line_type']=='招生专业目录'and r['plan_count']is not None:errors.append(f'{code}/{k}: catalogue has invented count')
            if r['tuition_amount']is not None and r['tuition_unit']!='per_academic_year':errors.append(f'{code}/{k}: unexpected billing unit')
        live_controls=db.query(ProvinceControlScore).filter_by(province_id=province.id).all()
        expected_controls={(r['year'],r['level'],r['category_name'],r['line_type'],r['round']):(r['category_code'],r['score'],r['source_url'])for r in controls}
        actual_controls={(r.year,r.level,r.category_name,r.line_type,r.round):(r.category_code,r.score,r.source)for r in live_controls}
        if actual_controls!=expected_controls:errors.append(f'{code}: database control-score fields differ')
        if db.query(AdmissionScore).join(Institution).filter(Institution.province_id==province.id).count():errors.append(f'{code}: unexpected institution admission scores')
        for s in instances.values():
            want=[r for r in collections if r['institution_code']==s.code]
            if (s.supplemental_data or{}).get('category_collection_plans',[])!=want:errors.append(f'{code}/{s.code}: collection granularity differs')
        api=read_institutions(province=code,major=None,db=db,_user=None);variant=Counter()
        for s in api:
            rows=[r for r in records if r['institution_code']==s.code and r.get('selection_eligible')is not False]
            if s.active_catalog_round:rows=[r for r in rows if r['round']==s.active_catalog_round]
            eligible=set()
            for r in rows:
                m=majors.get(r['major_name']);cat={'文史类':'文史中医类','中医类':'文史中医类'}.get(r.get('category_name'),r.get('category_name'))
                if m and m.category==cat:eligible.add(m.code)
                elif m:variant[r['major_name'],cat]+=1
            if set(s.majors)!=eligible:errors.append(f'{code}/{s.code}: target majors differ from verified current eligible catalogue')
        if variant:warnings.append(dict(province=code,type='unsupported_category_variant',rows=sum(variant.values()),variants=[dict(name=k[0],category=k[1],records=v)for k,v in variant.items()]))
        summaries.append(dict(province=code,institutions=len(schools),professional_records=len(records),controls=len(controls),collections=len(collections),restricted_records=sum(r.get('selection_eligible')is False for r in records),current_round=next((s.active_catalog_round for s in api if s.active_catalog_round),None)))
    quality_root=DATA/'sources/quality-audit'
    quality_manifest=json.loads((quality_root/'source-manifest.json').read_text())
    for source in quality_manifest['sources']:
        path=quality_root/source['path']
        if sha256(path.read_bytes()).hexdigest()!=source['sha256']:errors.append('Subject crosswalk source hash differs')
        checked_sources.add((str(path.relative_to(DATA)),source['sha256']))
    return dict(passed=not errors,provinces=summaries,source_files_checked=len(checked_sources),errors=errors,category_scope_notes=warnings,
        totals={k:sum(r[k]for r in summaries)for k in ['institutions','professional_records','controls','collections','restricted_records']})


def run():
    with SessionLocal()as db:report=audit(db)
    print(json.dumps(report,ensure_ascii=False,indent=2))
    if not report['passed']:raise SystemExit(1)

if __name__=='__main__':run()
