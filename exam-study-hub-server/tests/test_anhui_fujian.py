"""Complete public pages, source semantics and province-scoped live-contract imports."""
from collections import Counter
from hashlib import sha256
import json
import re
import unittest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import app.models
from app.db.base import Base
from app.models.catalog import AdmissionPlan, AdmissionScore, Institution, Major, Province
from app.routers.institutions import read_institutions
from scripts.scrape_anhui_fujian import DATA, parse_catalogue, parse_controls, school_identities
from scripts.seed_anhui_fujian import import_anhui_fujian
from scripts.seed import MAJORS


def read(code,suffix):return json.loads((DATA/f'{code}-{suffix}.json').read_text())

class SourceTests(unittest.TestCase):
    def test_all_pages_and_archived_hashes_reproduce_artifacts(self):
        for code in ['anhui','fujian']:
            root=DATA/'sources'/code;urls=json.loads((root/'source-urls.json').read_text());manifest=read(code,'manifest')
            rows=parse_catalogue(code,root,urls)
            self.assertEqual(rows,read(code,'adult-programs'))
            self.assertEqual(school_identities(code,rows,root,urls),read(code,'institutions'))
            self.assertEqual(parse_controls(code,root,urls),read(code,'adult-control-scores'))
            self.assertEqual({r['source_query_page']for r in rows},set(range(1,38))if code=='anhui'else set(range(13,26)))
            for source in manifest['sources']:
                self.assertEqual(sha256((DATA/source['path']).read_bytes()).hexdigest(),source['sha256'])
            requests=json.loads((root/'source-requests.json').read_text());self.assertEqual(len(requests),37 if code=='anhui'else 25)
            self.assertTrue(all(r['method']=='POST'for r in requests.values()))
        # Independent count metadata from each official query, not a derived manifest.
        ah=next(p.read_text(errors='replace') for p in (DATA/'sources/anhui').glob('catalog-2026-*.html') if 'dataTotal' in p.read_text(errors='replace'))
        self.assertEqual(re.search(r"dataTotal:\s*'([\d,]+)'",ah)[1],'1,104')
        fj=(DATA/'sources/fujian/catalog-2026-001.html').read_text()
        self.assertIn('_RECORDCOUNT=965',fj);self.assertIn('_PAGECOUNT=25',fj)

    def test_source_codes_levels_locations_and_unknown_fees_are_preserved(self):
        for code,count,schools in [('anhui',1104,71),('fujian',468,40)]:
            rows=read(code,'adult-programs');self.assertEqual(len(rows),count)
            self.assertEqual(len({r['institution_code']for r in rows}),schools)
            self.assertTrue(all(r['major_code']==r['major_code_raw']and r['plan_count']is None and r['level']=='专升本'for r in rows))
            self.assertEqual(len({(r['institution_code'],r['major_code'])for r in rows}),count)
        fj=read('fujian','adult-programs')
        unspecified=next(r for r in fj if r['tuition_raw']=='1680元')
        self.assertIsNone(unspecified['tuition_amount']);self.assertIsNone(unspecified['tuition_unit'])
        self.assertIn('不可当作年学费',unspecified['remarks'])
        annual=next(r for r in fj if r['tuition_raw']=='2944元/年')
        self.assertEqual(annual['tuition_amount'],2944);self.assertEqual(annual['tuition_unit'],'per_academic_year')
        for code,school,city in [('anhui','安徽开放大学','合肥'),('fujian','福建开放大学','福州'),('fujian','福建教育学院','福州')]:
            record=next(r for r in read(code,'institutions')if r['institution_name']==school)
            self.assertEqual(record['city'],city);self.assertTrue(record['city_source_url'])

    def test_restricted_projects_cannot_become_ordinary_targets(self):
        ah=read('anhui','adult-programs');fj=read('fujian','adult-programs')
        self.assertEqual(sum(not r['selection_eligible']for r in ah),21)
        self.assertEqual(sum(not r['selection_eligible']for r in fj),10)
        mixed=[r for r in ah if '社会招生或'in (r['remarks']or'')]
        self.assertTrue(mixed);self.assertTrue(all(r['selection_eligible']for r in mixed))
        special=[r for r in fj if '不面向社会招生'in (r['remarks']or'')]
        self.assertTrue(special);self.assertTrue(all(not r['selection_eligible']for r in special))
        self.assertEqual(len({(r['institution_code'],r['major_name_raw'])for r in ah}),485)
        self.assertEqual(len({(r['institution_code'],r['major_name_raw'])for r in fj}),242)

    def test_controls_exclude_high_school_levels_and_institution_scores(self):
        ah=read('anhui','adult-control-scores');fj=read('fujian','adult-control-scores')
        self.assertEqual(Counter(r['year']for r in ah),{2024:8,2025:8})
        self.assertEqual({r['category_code']:r['score']for r in fj},{'11':151,'12':109,'13':100,'14':100,'15':100,'16':160,'17':104,'18':160})
        self.assertTrue(all(r['level']=='专升本'and r['line_type']=='省控线'for r in ah+fj))

class IntegrationTests(unittest.TestCase):
    def setUp(self):
        self.engine=create_engine('sqlite://');Base.metadata.create_all(self.engine);self.db=sessionmaker(bind=self.engine)()
        p=Province(code='other',name='已有省份');self.db.add(p);self.db.flush()
        self.other=Institution(province_id=p.id,code='101',name='已有同编码院校');self.db.add(self.other)
        for r in MAJORS:self.db.add(Major(**{k:r[k]for k in ('code','name','category')}))
        self.db.commit()
    def tearDown(self):self.db.close();self.engine.dispose()

    def test_idempotency_scope_and_api_course_eligibility(self):
        counts=import_anhui_fujian(self.db);self.db.commit()
        self.assertEqual(counts,{'anhui':dict(institutions_added=71,plans_added=1104,controls_added=16),'fujian':dict(institutions_added=40,plans_added=468,controls_added=8)})
        self.assertTrue(all(v==0 for c in import_anhui_fujian(self.db).values()for v in c.values()))
        self.assertEqual(self.other.name,'已有同编码院校');self.assertEqual(self.db.query(Major).count(),66)
        self.assertEqual(self.db.query(AdmissionScore).count(),0)
        self.assertEqual(self.db.query(AdmissionPlan).count(),1572)
        majors={m.code:m for m in self.db.query(Major)}
        for code,school_count,plan_count,controls in [('anhui',71,1104,16),('fujian',40,468,8)]:
            records=read_institutions(province=code,major=None,db=self.db,_user=None)
            self.assertEqual(len(records),school_count);self.assertEqual(sum(len(s.plans)for s in records),plan_count)
            self.assertEqual(sum(p.selection_eligible is False for s in records for p in s.plans),21 if code=='anhui'else 10)
            for school in records:
                self.assertEqual(school.scores,[]);self.assertEqual(len(school.control_scores),controls)
                self.assertEqual(school.active_catalog_year,2026)
                for major_code in school.majors:
                    major=majors[major_code]
                    self.assertTrue(any(p.major_name==major.name and p.category_name==major.category and p.selection_eligible is not False for p in school.plans))
            law=read_institutions(province=code,major='faxue',db=self.db,_user=None)
            self.assertGreater(len(law),3)

if __name__=='__main__':unittest.main()
