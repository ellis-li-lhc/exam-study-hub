import json
from pathlib import Path
from unittest import TestCase

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

import app.models  # noqa: F401
from app.db.base import Base
from app.models.catalog import AdmissionPlan, AdmissionScore, Institution, Major, Province, ProvinceControlScore
from app.routers.institutions import read_institutions
from scripts.seed_guangdong_supplements import import_guangdong_supplements

DATA = Path(__file__).resolve().parent.parent / "scraped-data"


class GuangdongSupplementTests(TestCase):
    def setUp(self):
        self.engine = create_engine("sqlite://")
        Base.metadata.create_all(self.engine)
        self.db = sessionmaker(bind=self.engine)()
        self.province = Province(code="guangdong", name="广东")
        self.db.add(self.province)
        self.db.flush()
        plans = json.loads((DATA / "guangdong-adult-program-plan-2025.json").read_text())
        schools = {}
        for record in plans:
            code = record["institution_code"]
            if code not in schools:
                school = Institution(code=code, name=record["institution_name"], province_id=self.province.id)
                self.db.add(school)
                self.db.flush()
                schools[code] = school
            self.db.add(AdmissionPlan(
                institution_id=schools[code].id,
                **{key: record[key] for key in ("year", "major_code", "major_name", "level", "category_code", "category_name", "plan_count", "line_type", "round")},
                source=record["source_url"],
            ))
        self.db.add(Major(code="gongshang-guanli", name="工商管理", category="经济管理类"))
        for record in json.loads((DATA / "guangdong-adult-scores.json").read_text()):
            self.db.add(AdmissionScore(
                institution_id=schools[record["institution_code"]].id,
                **{key: record[key] for key in ("year", "category_code", "category_name", "score", "line_type", "round")},
                source=record["source_url"],
            ))
        for record in json.loads((DATA / "guangdong-adult-control-scores.json").read_text()):
            self.db.add(ProvinceControlScore(
                province_id=self.province.id,
                **{key: record[key] for key in ("year", "level", "category_code", "category_name", "score", "line_type", "round")},
                source=record["source_url"],
            ))
        self.db.commit()

    def tearDown(self):
        self.db.close()
        self.engine.dispose()

    def test_import_is_repeatable_and_preserves_main_batch_and_majors(self):
        counts = import_guangdong_supplements(self.db)
        self.assertEqual(counts, {"scores_added": 374, "controls_added": 18, "plans_added": 95, "institutions_updated": 31})
        self.assertEqual(self.db.query(AdmissionScore).count(), 573)
        self.assertEqual(self.db.query(ProvinceControlScore).count(), 27)
        self.assertEqual(self.db.query(AdmissionPlan).count(), 841)
        main = self.db.query(AdmissionPlan).filter_by(round="第一批专科起点本科").all()
        self.assertEqual(len(main), 746)
        self.assertTrue(all(row.teaching_site is None and row.tuition_amount is None for row in main))
        self.assertEqual(self.db.query(Major).count(), 1)
        self.db.commit()
        self.assertEqual(import_guangdong_supplements(self.db), {key: 0 for key in counts})
        self.assertEqual(self.db.query(AdmissionPlan).count(), 841)

    def test_api_keeps_fee_units_batch_sources_and_review_status(self):
        import_guangdong_supplements(self.db)
        schools = read_institutions(province="guangdong", major=None, db=self.db, _user=None)
        self.assertEqual(len(schools), 79)
        collections = [p for school in schools for p in school.plans if p.round == "征集志愿"]
        self.assertEqual(len(collections), 95)
        self.assertEqual(sum(p.tuition_unit == "total" for p in collections), 8)
        self.assertEqual(sum(p.tuition_unit == "per_academic_year" for p in collections), 80)
        self.assertTrue(all(p.teaching_site and p.source_url for p in collections))
        self.assertTrue(all(p.tuition_amount is None for p in collections if p.tuition_unit is None))
        self.assertTrue(all(school.duration is None for school in schools))
        facts = [f for s in schools for f in (s.supplemental_data or {}).get("facts", [])]
        self.assertEqual(len(facts), 12)
        self.assertTrue(all(f["review_status"] == "verified_text" for f in facts))
        documents = [d for s in schools for d in (s.supplemental_data or {}).get("documents", [])]
        self.assertEqual(len(documents), 52)
        self.assertTrue(all("raw_file" not in d and "db_institution_id" not in d for d in documents))
        computer_school = next(s for s in schools if s.code == "10184")
        self.assertTrue(any(score.category_code.endswith("103") for score in computer_school.scores))
