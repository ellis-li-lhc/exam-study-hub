"""Prove source boundaries, import scope and actual selectable curricula."""
from collections import Counter
from hashlib import sha256
import json
import unittest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import app.models
from app.db.base import Base
from app.models.catalog import AdmissionPlan, AdmissionScore, Institution, Major, Province, ProvinceControlScore
from app.routers.institutions import read_institutions
from scripts.scrape_hunan_jiangxi import DATA, hunan, jiangxi, normalize
from scripts.seed_hunan_jiangxi import import_province
from scripts.seed import MAJORS


def read(province,suffix):return json.loads((DATA/f'{province}-{suffix}.json').read_text())

class SourceTests(unittest.TestCase):
    def test_archived_sources_reproduce_both_provinces(self):
        for province,parse in [('hunan',hunan),('jiangxi',jiangxi)]:
            root=DATA/'sources'/province;urls=json.loads((root/'source-urls.json').read_text())
            plans,controls,collections,schools=parse(root,urls);normalize(province,plans,collections,schools)
            for suffix,actual in [('adult-programs',plans),('adult-control-scores',controls),('adult-category-collection-plans',collections),('institutions',schools)]:
                self.assertEqual(actual,read(province,suffix))
            for source in read(province,'manifest')['sources']:
                self.assertEqual(sha256((DATA/source['path']).read_bytes()).hexdigest(),source['sha256'])

    def test_hunan_all_pages_school_boundaries_and_study_forms(self):
        plans=read('hunan','adult-programs')
        self.assertEqual(len(plans),677)
        self.assertEqual(len({r['institution_code']for r in plans}),56)
        self.assertTrue(all(r['level']=='专升本' and r['plan_count'] is None and r['tuition_amount'] is None and r['study_duration_raw'] is None for r in plans))
        aviation=[r for r in plans if r['institution_name']=='湖南航空工业职工工学院']
        self.assertEqual({r['major_name']for r in aviation},{'机械设计制造及其自动化','电子与计算机工程'})
        steel=[r for r in plans if r['institution_name']=='涟源钢铁总厂职工大学']
        self.assertEqual(len(steel),5)
        self.assertEqual(next(r for r in steel if r['major_code']=='105')['study_form'],'脱产')
        self.assertEqual(len({r['source_url']for r in plans}),3)
        jishou=next(r for r in read('hunan','institutions')if r['institution_name']=='吉首大学')
        self.assertEqual(jishou['city'],'湘西')
        self.assertTrue(all(r['major_code']==r['major_code_raw']for r in plans))

    def test_two_hunan_collections_remain_separate_and_not_major_plans(self):
        rows=read('hunan','adult-category-collection-plans')
        self.assertEqual(Counter(r['round']for r in rows),{'第1次征集志愿':124,'第2次征集志愿':114})
        self.assertEqual(sum(r['plan_count']for r in rows if r['round']=='第1次征集志愿'),6853)
        self.assertEqual(sum(r['plan_count']for r in rows if r['round']=='第2次征集志愿'),2404)
        self.assertTrue(all(r['major_name'] is None and r['major_code'] is None and r['granularity']=='institution_category'for r in rows))
        names={r['institution_code']:r['institution_name']for r in read('hunan','institutions')}
        old=next(r for r in rows if r['institution_code']=='10543')
        self.assertEqual(old['institution_name'],'湖南理工学院')
        self.assertEqual(names['10543'],'湖南理工大学')

    def test_jiangxi_rowspans_columns_levels_fees_and_missing_codes(self):
        rows=read('jiangxi','adult-programs')
        self.assertEqual(Counter(r['institution_name']for r in rows),{'江西师范大学':24,'江西农业大学':10,'南昌航空大学':30,'赣南师范大学':21,'华东交通大学':14,'东华理工大学':20,'江西理工大学':26,'宜春学院':22,'江西中医药大学':8,'江西水利电力大学':47,'江西财经大学':10,'江西科技师范大学':16,'新余学院':25,'南昌大学':24})
        psychology=next(r for r in rows if r['major_name']=='心理学')
        self.assertEqual(psychology['category_name'],'经济管理类')
        psychology=next(r for r in rows if r['major_name']=='应用心理学')
        self.assertEqual(psychology['category_name'],'经济管理类')
        self.assertTrue(all(r['plan_count'] is None and r['level']=='专升本'for r in rows))
        for row in rows:
            if row['institution_name'] in ('江西农业大学','南昌航空大学'):
                self.assertIsNone(row['major_code_raw']);self.assertTrue(row['major_code'].startswith('catalog-'))
            if row['institution_name']=='赣南师范大学':
                self.assertIsNone(row['tuition_amount']);self.assertEqual(row['foreign_language'],'英语')
            elif row['institution_name'] in ('江西师范大学','江西农业大学','南昌航空大学'):self.assertEqual(row['tuition_amount'],2100 if row['category_code']=='12'else 1700)
        self.assertEqual(len({r['major_name']for r in rows if r['institution_name']=='南昌航空大学'}),30)

    def test_expanded_sources_keep_sites_directions_and_conflicts(self):
        rows=read('jiangxi','adult-programs')
        ecut=[r for r in rows if r['institution_name']=='东华理工大学']
        self.assertTrue(all(r['study_duration_raw'] is None and r['minimum_study_duration_raw']=='2.5年'for r in ecut))
        ncu=[r for r in rows if r['institution_name']=='南昌大学']
        self.assertEqual(len(ncu),24)
        self.assertTrue(all(r['study_duration_raw']=='3年' and r['tuition_amount']==1700 for r in ncu))
        self.assertEqual(next(r for r in ncu if r['major_name']=='网络空间安全')['teaching_site'],'校本部')
        directions=[r for r in rows if r['institution_name']=='江西财经大学'and r.get('major_direction')]
        self.assertEqual(len(directions),4)
        self.assertTrue(all(r['source_page'] in (2,3) and r['study_duration_raw']=='三年' for r in directions))
        engineering=[r for r in rows if r['institution_name']=='江西理工大学']
        self.assertEqual(len(engineering),26)
        self.assertEqual(len({r['teaching_site']for r in engineering}),7)
        self.assertEqual(len({r['major_name']for r in engineering}),12)
        water=[r for r in rows if r['institution_name']=='江西水利电力大学']
        self.assertEqual(len(water),47)
        self.assertEqual(len({r['teaching_site']for r in water}),6)
        self.assertTrue(all(not r['teaching_site_address_raw'].startswith(('山西','吉林','海南','贵州','宁夏')) for r in water))
        pending=[r for r in rows if r.get('selection_eligible')is False]
        self.assertEqual(len(pending),3)
        self.assertEqual({r['major_name']for r in pending},{'药学','应急管理','供应链管理'})
        for r in pending:
            if r['major_name']!='药学':self.assertIsNone(r['category_name'])
            self.assertTrue(r['remarks'])
        self.assertEqual(len({(r['institution_name'],r['major_name_raw'])for r in rows}),255)

    def test_controls_exclude_other_levels_and_special_projects(self):
        hn=read('hunan','adult-control-scores');jx=read('jiangxi','adult-control-scores')
        self.assertEqual(Counter(r['year']for r in hn),{2024:8,2025:8})
        self.assertEqual({r['category_code']:r['score']for r in jx},{'11':135,'12':110,'13':100,'14':100,'15':121,'16':110,'17':105,'18':150})
        self.assertTrue(all(r['round']=='统考生' and r['level']=='专升本'for r in hn+jx))


class IntegrationTests(unittest.TestCase):
    def setUp(self):
        self.engine=create_engine('sqlite://');Base.metadata.create_all(self.engine)
        self.db=sessionmaker(bind=self.engine)()
        other=Province(code='other',name='原有省份');self.db.add(other);self.db.flush()
        self.other=Institution(province_id=other.id,code='10543',name='原有院校');self.db.add(self.other)
        for r in MAJORS:self.db.add(Major(**{k:r[k]for k in ('code','name','category')}))
        self.db.commit()
    def tearDown(self):self.db.close();self.engine.dispose()

    def test_scoped_import_and_idempotency(self):
        self.assertEqual(import_province(self.db,'hunan'),dict(institutions_added=61,plans_added=677,controls_added=16))
        self.assertEqual(import_province(self.db,'jiangxi'),dict(institutions_added=14,plans_added=297,controls_added=8))
        self.db.commit()
        for p in ['hunan','jiangxi']:self.assertEqual(import_province(self.db,p),dict(institutions_added=0,plans_added=0,controls_added=0))
        self.assertEqual(self.other.name,'原有院校');self.assertEqual(self.db.query(Major).count(),66)
        self.assertEqual(self.db.query(AdmissionScore).count(),0)
        self.assertEqual(self.db.query(AdmissionPlan).count(),974)
        self.assertTrue(all(r.plan_count is None for r in self.db.query(AdmissionPlan)))

    def test_api_data_and_selectable_curricula_match_official_categories(self):
        majors={r.code:r for r in self.db.query(Major)}
        for province,expected,control_count in [('hunan',61,16),('jiangxi',14,8)]:
            import_province(self.db,province)
            rows=read_institutions(province=province,major=None,db=self.db,_user=None)
            self.assertEqual(len(rows),expected);pairs=0
            for school in rows:
                self.assertTrue(school.city);self.assertEqual(school.active_catalog_year,2026)
                self.assertEqual(school.scores,[]);self.assertEqual(len(school.control_scores),control_count)
                for code in school.majors:
                    major=majors[code]
                    self.assertTrue(any(p.major_name==major.name and p.category_name==major.category and p.selection_eligible is not False for p in school.plans))
                    filtered=read_institutions(province=province,major=code,db=self.db,_user=None)
                    self.assertIn(school.code,[r.code for r in filtered]);pairs+=1
            if province=='jiangxi':
                science=next(s for s in rows if s.name=='江西科技师范大学')
                self.assertNotIn('yaoxue',science.majors)
                self.assertFalse(next(p for p in science.plans if p.major_name=='药学').selection_eligible)
            self.assertGreater(pairs,20)
            if province=='hunan':
                self.assertEqual(sum(not s.plans for s in rows),5)
                self.assertTrue(all(not s.majors for s in rows if not s.plans))
                self.assertEqual(sum(len(s.category_collection_plans)for s in rows),238)
            else:
                self.assertEqual(sum(len(s.plans)for s in rows),297)
                for s in rows:
                    for p in s.plans:
                        if p.major_code.startswith('catalog-'):self.assertIsNone(p.major_code_raw)

if __name__=='__main__':unittest.main()
