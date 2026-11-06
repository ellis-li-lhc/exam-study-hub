"""Check source-level boundaries before Hubei data is considered for import."""
import json
import unittest
from collections import Counter

from scripts.scrape_hubei import ROOT, catalogues, expand, normalize_records, parse_collections, parse_controls


class HubeiScrapeTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.urls = json.loads((ROOT / 'source-urls.json').read_text())

    def test_controls_do_not_include_other_education_levels(self):
        for year, ordinary in [(2023, 113), (2024, 125), (2025, 124)]:
            rows = parse_controls(year, self.urls[f'controls-{year}.html'])
            self.assertEqual({r['category_code'] for r in rows}, {str(n) for n in range(11, 19)})
            self.assertTrue(all(r['score'] == (105 if r['category_code'] == '12' else ordinary) for r in rows))

    def test_collection_scope_and_totals(self):
        for year, count, people in [(2024, 9, 376), (2025, 16, 592)]:
            rows = parse_collections(year, self.urls[f'collection-{year}.pdf'])
            self.assertEqual(len(rows), count)
            self.assertEqual(sum(r['plan_count'] for r in rows), people)
            self.assertTrue(all(r['major_name'] is None and r['granularity'] == 'institution_category' for r in rows))
            self.assertEqual(len({(r['institution_code_raw'], r['category_code']) for r in rows}), count)

    def test_catalogue_boundaries_and_uncertainty(self):
        rows = catalogues(self.urls)
        self.assertEqual(Counter(r['institution_name'] for r in rows), {
            '湖北中医药大学': 12, '湖北医药学院': 10, '华中农业大学': 23,
            '湖北大学': 21, '湖北工程学院': 19})
        self.assertTrue(all(r['level'] == '专升本' and r['plan_count'] is None for r in rows))
        for row in rows:
            if row['institution_name'] == '华中农业大学':
                self.assertIn('湖北', row['enrollment_scope'])
                self.assertIsNone(row['tuition_amount'])
            if row['institution_name'] == '湖北医药学院':
                self.assertIsNone(row['category_name_raw'])
            if row['institution_name'] == '湖北工程学院':
                self.assertIsNone(row['category_name_raw'])
                self.assertIsNotNone(row['discipline_raw'])
        psychology = next(r for r in rows if r['major_name'] == '应用心理学')
        self.assertEqual(psychology['category_name_raw'], '经济管理类')

    def test_normalized_artifacts_match_sources_and_preserve_unknown_codes(self):
        rows = catalogues(self.urls)
        collections = [r for year in [2024,2025] for r in parse_collections(year,self.urls[f'collection-{year}.pdf'])]
        schools = json.loads((ROOT.parent.parent/'hubei-institutions.json').read_text())
        normalize_records(rows,collections,schools)
        self.assertEqual(rows,json.loads((ROOT.parent.parent/'hubei-adult-programs.json').read_text()))
        self.assertTrue(all(r['category_name'] and r['institution_code'] for r in rows))
        new_major = next(r for r in rows if r['major_name']=='人工智能')
        self.assertEqual(new_major['category_name'],'理工类')
        self.assertIsNone(new_major['major_code_raw'])
        self.assertIsNone(new_major['national_major_code'])
        medicine = next(r for r in rows if r['institution_name']=='湖北医药学院' and r['major_name']=='药学')
        self.assertIsNone(medicine['category_name_raw'])
        self.assertEqual(medicine['category_name'],'经济管理类')

    def test_span_expansion_does_not_guess_blank_cells(self):
        table = [[({'rowspan': '2'}, '专升本'), ({}, '护理学')], [({}, '')]]
        self.assertEqual(list(expand(table)), [['专升本', '护理学'], ['专升本', '']])



from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import app.models
from app.db.base import Base
from app.models.catalog import Province, Institution, Major, AdmissionPlan, AdmissionScore, ProvinceControlScore
from app.routers.institutions import read_institutions
from scripts.seed import MAJORS
from scripts.seed_hubei import import_hubei, DATA


class HubeiIntegrationTests(unittest.TestCase):
    def setUp(self):
        self.engine=create_engine('sqlite://')
        Base.metadata.create_all(self.engine)
        self.db=sessionmaker(bind=self.engine)()
        other=Province(code='other',name='保留省份');self.db.add(other);self.db.flush()
        self.other=Institution(code='4142010512',name='保留同编号院校',province_id=other.id);self.db.add(self.other)
        for row in MAJORS:self.db.add(Major(**{f:row[f] for f in ('code','name','category')}))
        self.db.commit()

    def tearDown(self):
        self.db.close();self.engine.dispose()

    def test_idempotency_scope_and_collection_granularity(self):
        self.assertEqual(import_hubei(self.db),dict(institutions_added=9,plans_added=85,controls_added=24))
        self.db.commit()
        self.assertEqual(import_hubei(self.db),dict(institutions_added=0,plans_added=0,controls_added=0))
        self.assertEqual(self.other.name,'保留同编号院校')
        self.assertEqual(self.db.query(Major).count(),66)
        self.assertEqual(self.db.query(AdmissionPlan).count(),85)
        self.assertEqual(self.db.query(AdmissionScore).count(),0)
        self.assertEqual(self.db.query(ProvinceControlScore).count(),24)
        self.assertTrue(all(p.plan_count is None for p in self.db.query(AdmissionPlan)))
        records=read_institutions(province='hubei',major=None,db=self.db,_user=None)
        self.assertEqual(len(records),9)
        self.assertEqual(sum(len(s.category_collection_plans) for s in records),25)
        self.assertEqual(sum(p.plan_count for s in records for p in s.category_collection_plans),968)
        self.assertEqual(sum(bool(s.majors) for s in records),5)
        for s in records:
            self.assertEqual(s.scores,[])
            self.assertEqual(len(s.control_scores),24)
            if not s.plans:self.assertEqual(s.majors,[])
        engineering=next(s for s in records if s.name=='湖北工程学院')
        self.assertIn('yingyong-xinli',engineering.majors)
        self.assertTrue(any(p.major_name == '应用心理学' and p.category_name == '经济管理类' for p in engineering.plans))
        self.assertEqual(next(p for p in engineering.plans if p.major_name=='应用心理学').category_name,'经济管理类')
        self.assertTrue(any(p.major_code_raw is None and p.major_code.startswith('catalog-') for p in engineering.plans))
        medicine=next(s for s in records if s.name=='湖北医药学院')
        self.assertEqual(next(p for p in medicine.plans if p.major_name=='药学').category_name,'经济管理类')
        self.assertEqual(next(p for p in medicine.plans if p.major_name=='护理学').tuition_amount,2600)
        self.assertTrue(all(s.city for s in records))

    def test_supported_curricula_match_official_categories(self):
        import_hubei(self.db)
        majors={m.code:m for m in self.db.query(Major)}
        records=read_institutions(province='hubei',major=None,db=self.db,_user=None)
        pairs=0
        for school in records:
            for code in school.majors:
                major=majors[code]
                self.assertTrue(any(p.major_name==major.name and p.category_name==major.category for p in school.plans))
                filtered=read_institutions(province='hubei',major=code,db=self.db,_user=None)
                self.assertIn(school.code,[r.code for r in filtered]);pairs+=1
        self.assertGreater(pairs,30)


if __name__ == '__main__':
    unittest.main()
