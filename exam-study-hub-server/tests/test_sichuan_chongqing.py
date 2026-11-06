"""Image provenance, query completeness, admissions semantics and scoped API import."""
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
from scripts.scrape_sichuan_chongqing import DATA, parse_catalogue, parse_controls, school_identities
from scripts.seed_sichuan_chongqing import import_sichuan_chongqing
from scripts.seed import MAJORS


def read(code,suffix):return json.loads((DATA/f'{code}-{suffix}.json').read_text())

class SourceTests(unittest.TestCase):
    def test_archived_sources_reproduce_all_records_and_identities(self):
        for code in ['sichuan','chongqing']:
            root=DATA/'sources'/code;urls=json.loads((root/'source-urls.json').read_text())
            rows=parse_catalogue(code,root,urls)
            self.assertEqual(rows,read(code,'adult-programs'))
            self.assertEqual(school_identities(code,rows,root,urls),read(code,'institutions'))
            self.assertEqual(parse_controls(code,root,urls),read(code,'adult-control-scores'))
            for s in read(code,'manifest')['sources']:
                self.assertEqual(sha256((DATA/s['path']).read_bytes()).hexdigest(),s['sha256'])
        sc=DATA/'sources/sichuan';review=json.loads((sc/'catalog-reviewed-2026.json').read_text())
        self.assertEqual(set(review['physical_rows_per_page']),{str(i)for i in range(1,56)})
        self.assertEqual(sum(review['physical_rows_per_page'].values()),1329)
        self.assertEqual(Counter(str(r['page'])for r in review['rows']),review['physical_rows_per_page'])
        html=(sc/'catalog-2026.html').read_text();urls=json.loads((sc/'source-urls.json').read_text())
        images=[u for name,u in urls.items()if re.fullmatch(r'catalog-2026-\d{3}\.png',name)]
        self.assertEqual(len(images),55)
        self.assertTrue(all(u.rsplit('/',1)[-1]in html for u in images))
        self.assertFalse(review['optional_pending_cells'])
        self.assertTrue(all(r['cells'][9]and r['cells'][10]for r in review['rows']))
        self.assertEqual(len(review['manual_review']),111)

    def test_source_codes_and_catalogue_counts_not_enrolment_numbers(self):
        sc=read('sichuan','adult-programs');cq=read('chongqing','adult-programs')
        for rows,count,schools in [(sc,1329,49),(cq,472,36)]:
            self.assertEqual(len(rows),count);self.assertEqual(len({r['institution_code']for r in rows}),schools)
            self.assertEqual(len({(r['institution_code'],r['major_code'])for r in rows}),count)
            self.assertTrue(all(r['level']=='专升本'and r['plan_count']is None and r['major_code']==r['major_code_raw']for r in rows))
        self.assertEqual(sc[0]['major_code'],'010501')
        self.assertEqual(sc[0]['tuition_amount'],3000)
        self.assertEqual(next(r for r in sc if r['major_code']=='030521')['major_name'],'机械设计制造及其自动化')
        self.assertEqual({r['foreign_language']for r in cq},{'英语'})
        self.assertTrue(any(r['major_code']=='01'for r in cq))
        self.assertEqual(len({(r['institution_code'],r['major_name'])for r in sc}),406)
        self.assertEqual(len({(r['institution_code'],r['major_name'])for r in cq}),250)
        raw=json.loads((DATA/'sources/chongqing/catalog-zsb-2026.json').read_text())['data']
        self.assertTrue(any(r['jhs']for r in raw))
        self.assertTrue(all(r['teaching_site']is None for r in cq))
        unspecified=next(r for r in cq if r['tuition_raw']=='2800')
        self.assertIsNone(unspecified['tuition_amount']);self.assertIsNone(unspecified['tuition_unit'])
        self.assertIn('未注明计费周期',unspecified['remarks'])
        for rows in [sc,cq]:
            total_fee=next(r for r in rows if r['tuition_raw']=='总学费7200元')
            self.assertIsNone(total_fee['tuition_amount'])
        annual=next(r for r in cq if r['tuition_raw']=='2550（元/生·年）')
        self.assertEqual(annual['tuition_amount'],2550)

    def test_restrictions_and_controls_keep_their_meaning(self):
        sc=read('sichuan','adult-programs');cq=read('chongqing','adult-programs')
        self.assertEqual(sum(not r['selection_eligible']for r in sc),10)
        self.assertEqual(sum(not r['selection_eligible']for r in cq),12)
        for r in sc+cq:
            if re.search(r'仅招收|只招收|直属单位|委托培养',r['remarks']or''):self.assertFalse(r['selection_eligible'])
        self.assertTrue(all(r['selection_eligible']for r in cq if '重庆开放大学及其基层办学单位'in r['remarks']))
        self.assertTrue(all(r['selection_eligible']for r in cq if r['remarks'].startswith('直属与社会')))
        expected={'sichuan':{2024:[198,140,121,121,178,170,147,146],2025:[162,130,105,110,153,162,126,134]},
                  'chongqing':{2024:[202,156,133,136,189,150,123,153],2025:[182,160,118,122,160,158,122,136]}}
        for code,years in expected.items():
            lines=read(code,'adult-control-scores');self.assertEqual(len(lines),16)
            for year,values in years.items():
                self.assertEqual([r['score']for r in lines if r['year']==year],values)
            self.assertTrue(all(r['level']=='专升本'and r['line_type']=='省控线'for r in lines))

class IntegrationTests(unittest.TestCase):
    def setUp(self):
        self.engine=create_engine('sqlite://');Base.metadata.create_all(self.engine);self.db=sessionmaker(bind=self.engine)()
        p=Province(code='other',name='其他省份');self.db.add(p);self.db.flush()
        self.other=Institution(province_id=p.id,code='10635',name='已有院校');self.db.add(self.other)
        for r in MAJORS:self.db.add(Major(**{k:r[k]for k in ('code','name','category')}))
        self.db.commit()
    def tearDown(self):self.db.close();self.engine.dispose()

    def test_repeat_import_and_live_api_category_target_contract(self):
        counts=import_sichuan_chongqing(self.db);self.db.commit()
        self.assertEqual(counts,{'sichuan':dict(institutions_added=49,plans_added=2569,controls_added=16),'chongqing':dict(institutions_added=36,plans_added=472,controls_added=16)})
        self.assertTrue(all(v==0 for c in import_sichuan_chongqing(self.db).values()for v in c.values()))
        self.assertEqual(self.other.name,'已有院校');self.assertEqual(self.db.query(AdmissionPlan).count(),3041)
        self.assertEqual(self.db.query(AdmissionScore).count(),0)
        majors={m.code:m for m in self.db.query(Major)}
        for code,count,restricted in [('sichuan',49,20),('chongqing',36,12)]:
            schools=read_institutions(province=code,major=None,db=self.db,_user=None)
            self.assertEqual(len(schools),count)
            self.assertEqual(sum(p.selection_eligible is False for s in schools for p in s.plans),restricted)
            for s in schools:
                self.assertEqual(len(s.control_scores),16);self.assertEqual(s.scores,[])
                for major_code in s.majors:
                    m=majors[major_code]
                    self.assertTrue(any(p.major_name==m.name and p.category_name==m.category and p.selection_eligible is not False for p in s.plans))
            law=read_institutions(province=code,major='faxue',db=self.db,_user=None)
            self.assertGreater(len(law),3)
            self.assertTrue(all('faxue'in s.majors for s in law))
            self.assertFalse(any(s.name=='中国消防救援学院'for s in law))

if __name__=='__main__':unittest.main()
