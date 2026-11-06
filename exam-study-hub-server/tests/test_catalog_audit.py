"""Audit regressions: corrected curriculum, current round and retained historical source data."""
import json
from pathlib import Path
import unittest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import app.models
from app.db.base import Base
from app.models.catalog import Major,MajorSubject
from scripts.repair_major_subjects import repair
from scripts.scrape_hunan_jiangxi import plain
from scripts.seed import MAJORS
from scripts.sichuan_current_catalog import DATA,parse_current

class AuditTests(unittest.TestCase):
    def test_official_crosswalk_and_current_beijing_detail_confirm_high_math_two(self):
        text=plain((DATA/'sources/quality-audit/moe-subject-crosswalk-2017.html').read_text())
        text=text.split('四、经济学',1)[1].split('五、',1)[0]
        self.assertIn('应用心理学',text);self.assertIn('信息管理与信息系统',text);self.assertIn('高数（二）',text)
        from scripts.scrape_beijing_guangxi import beijing_fields
        for code in ['28270','38284']:
            d=beijing_fields(DATA/f'sources/beijing/detail-2026-{code}.html')
            self.assertIn('高等数学(二)',d['统考科目'])

    def test_major_repair_is_scoped_and_idempotent(self):
        engine=create_engine('sqlite://');Base.metadata.create_all(engine)
        with sessionmaker(bind=engine)()as db:
            for code,name,cat,subject in [('yingyong-xinli','应用心理学','教育学类','教育理论'),('xinxi-guanli','信息管理与信息系统','理工类','高等数学（一）'),('other','已有专业','法学类','民法')]:
                m=Major(code=code,name=name,category=cat);m.subjects=[MajorSubject(subject=s)for s in ['政治','英语',subject]];db.add(m)
            db.commit();ids={m.code:m.id for m in db.query(Major)}
            self.assertEqual(len(repair(db)),2);db.commit();self.assertEqual(repair(db),[])
            self.assertEqual({m.code:m.id for m in db.query(Major)},ids)
            for m in db.query(Major):
                if m.code=='other':self.assertEqual(m.category,'法学类');continue
                self.assertEqual(m.category,'经济管理类');self.assertEqual([s.subject for s in m.subjects],['政治','英语','高等数学（二）'])
        engine.dispose()

    def test_current_sichuan_plan_count_and_superseded_professional_keys(self):
        current=parse_current();stored=json.loads((DATA/'sichuan-adult-current-plans.json').read_text());self.assertEqual(current,stored)
        old=json.loads((DATA/'sichuan-adult-programs.json').read_text())
        oldkeys={(r['institution_code'],r['major_code'])for r in old};newkeys={(r['institution_code'],r['major_code'])for r in current}
        self.assertEqual(len(oldkeys-newkeys),89);self.assertEqual(newkeys-oldkeys,set())
        self.assertEqual(sum(r['plan_count']for r in current),49031);self.assertEqual(sum(not r['selection_eligible']for r in current),10)
        self.assertTrue(all(r['line_type']=='招生专业计划'and r['plan_count']>0 for r in current))
        self.assertTrue(all(r['line_type']=='招生专业目录'and r['plan_count']is None for r in old))

if __name__=='__main__':unittest.main()
