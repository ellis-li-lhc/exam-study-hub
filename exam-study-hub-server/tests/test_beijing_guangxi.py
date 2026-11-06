"""Primary-source completeness, source-specific codes/fees, and live import/API contracts."""
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
from scripts.scrape_beijing_guangxi import DATA, html, parse_catalogue, school_identities, parse_controls, beijing_fields
from scripts.seed_beijing_guangxi import import_beijing_guangxi
from scripts.seed import MAJORS


def read(code,suffix):return json.loads((DATA/f'{code}-{suffix}.json').read_text())

class SourceTests(unittest.TestCase):
    def test_complete_primary_catalogues_and_hash_bound_replay(self):
        for code in ['beijing','guangxi']:
            root=DATA/'sources'/code;urls=json.loads((root/'source-urls.json').read_text());rows=parse_catalogue(code,root,urls)
            self.assertEqual(rows,read(code,'adult-programs'))
            self.assertEqual(school_identities(code,rows,root,urls),read(code,'institutions'))
            self.assertEqual(parse_controls(code,root,urls),read(code,'adult-control-scores'))
            for s in read(code,'manifest')['sources']:
                self.assertEqual(sha256((DATA/s['path']).read_bytes()).hexdigest(),s['sha256'])
        root=DATA/'sources/beijing';index=html(root/'catalog-2026.html')
        self.assertEqual(len(re.findall(r"gospecialty\('\d+','\d+'\)",index)),287)
        self.assertEqual(len(list(root.glob('detail-2026-*.html'))),287)
        self.assertEqual(beijing_fields(root/'detail-get-example-2026.html'),beijing_fields(root/'detail-2026-00170.html'))
        bj=read('beijing','adult-programs');self.assertEqual(bj[0]['major_code'],'00170')
        self.assertTrue(all('examId=6311'in r['source_url']and r['foreign_language']=='英语'for r in bj))
        self.assertEqual(Counter(r['category_code']for r in bj),{'11':14,'12':38,'13':91,'14':113,'15':8,'16':12,'17':5,'18':6})

    def test_fees_addresses_and_source_identity_codes_are_not_conflated(self):
        bj=read('beijing','adult-programs');gx=read('guangxi','adult-programs')
        self.assertTrue(all(r['tuition_raw']is None and r['tuition_amount']is None for r in bj))
        missing=next(r for r in gx if r['institution_name']=='中南林业科技大学'and r['major_name']=='林学')
        self.assertIsNone(missing['tuition_raw']);self.assertIn('罗文大道33号',missing['teaching_site'])
        semester=next(r for r in gx if r['tuition_raw']=='900元/学期');self.assertIsNone(semester['tuition_amount'])
        total=next(r for r in gx if r['tuition_raw']=='4720元/2.5年');self.assertIsNone(total['tuition_unit'])
        unspecified=next(r for r in gx if r['tuition_raw']=='4800');self.assertIsNone(unspecified['tuition_amount']);self.assertIn('不可当作年学费',unspecified['remarks'])
        annual=next(r for r in gx if r['tuition_raw']=='3500元/学年/人');self.assertEqual(annual['tuition_amount'],3500)
        for name,code,national in [('广西警察学院','11547','13520'),('广西职业师范学院','50869','14684')]:
            s=next(r for r in read('guangxi','institutions')if r['institution_name']==name)
            self.assertEqual(s['institution_code'],code);self.assertTrue(s['national_institution_code'].endswith(national))
        # Parentheses in a school name must start a new school rather than inherit the preceding one.
        for name,code in [('中国地质大学(武汉)','10491'),('中国矿业大学(北京)','11413'),('中国地质大学(北京)','11415')]:
            rows=[r for r in gx if r['institution_name']==name];self.assertTrue(rows)
            self.assertTrue(all(r['institution_code']==code for r in rows))
        self.assertTrue(all(r['level']=='专升本'and r['plan_count']is None for r in bj+gx))

    def test_restricted_intakes_and_year_category_control_scores(self):
        for code,count in [('beijing',10),('guangxi',9)]:
            rows=read(code,'adult-programs');self.assertEqual(sum(not r['selection_eligible']for r in rows),count)
            for r in rows:
                if re.search('委托培养|只招|仅招|不面向社会|直属单位',r['remarks']):self.assertFalse(r['selection_eligible'])
        mixed=[r for r in read('beijing','adult-programs')if r['enrollment_scope'].startswith('直属与社会')]
        self.assertEqual(len(mixed),3);self.assertTrue(all(r['selection_eligible']for r in mixed))
        expected={'beijing':{2024:[226,144,152,153,197,164,185,192],2025:[193,128,136,135,176,159,155,191]},
                  'guangxi':{2024:[171,114,114,105,149,142,151,138],2025:[142,104,104,100,139,138,114,125]}}
        for code,years in expected.items():
            controls=read(code,'adult-control-scores');self.assertEqual(len(controls),16)
            for year,values in years.items():self.assertEqual([r['score']for r in controls if r['year']==year],values)
        # Pending Yunnan raw files cannot advertise an unsupported three-subject province.
        self.assertFalse((DATA/'yunnan-manifest.json').exists())

class IntegrationTests(unittest.TestCase):
    def setUp(self):
        self.engine=create_engine('sqlite://');Base.metadata.create_all(self.engine);self.db=sessionmaker(bind=self.engine)()
        p=Province(code='other',name='其他省份');self.db.add(p);self.db.flush()
        self.other=Institution(province_id=p.id,code='001',name='已有同编码院校');self.db.add(self.other)
        for r in MAJORS:self.db.add(Major(**{k:r[k]for k in ('code','name','category')}))
        self.db.commit()
    def tearDown(self):self.db.close();self.engine.dispose()

    def test_scoped_repeatable_import_and_strict_supported_target_matching(self):
        counts=import_beijing_guangxi(self.db);self.db.commit()
        self.assertEqual(counts,{'beijing':dict(institutions_added=45,plans_added=287,controls_added=16),'guangxi':dict(institutions_added=55,plans_added=569,controls_added=16)})
        self.assertTrue(all(v==0 for c in import_beijing_guangxi(self.db).values()for v in c.values()))
        self.assertEqual(self.other.name,'已有同编码院校');self.assertEqual(self.db.query(AdmissionPlan).count(),856)
        self.assertEqual(self.db.query(AdmissionScore).count(),0)
        majors={m.code:m for m in self.db.query(Major)}
        for code,count,restricted in [('beijing',45,10),('guangxi',55,9)]:
            schools=read_institutions(province=code,major=None,db=self.db,_user=None)
            self.assertEqual(len(schools),count);self.assertEqual(sum(p.selection_eligible is False for s in schools for p in s.plans),restricted)
            for s in schools:
                self.assertEqual(s.scores,[]);self.assertEqual(len(s.control_scores),16)
                for major_code in s.majors:
                    m=majors[major_code]
                    self.assertTrue(any(p.major_name==m.name and p.category_name==m.category and p.selection_eligible is not False for p in s.plans))
            law=read_institutions(province=code,major='faxue',db=self.db,_user=None)
            self.assertGreater(len(law),1)
            self.assertTrue(all('faxue'in s.majors for s in law))
            self.assertFalse(any(s.name=='中国消防救援学院'for s in law))

if __name__=='__main__':unittest.main()
