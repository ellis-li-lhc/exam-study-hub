import json
from pathlib import Path
from unittest import TestCase

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

import app.models  # noqa: F401
from app.db.base import Base
from app.models.catalog import AdmissionPlan, AdmissionScore, Institution, Major, Province, ProvinceControlScore
from app.routers.institutions import read_institutions
from scripts.scrape_shanghai import CONTROLS, SOURCES, parse_catalog, parse_controls, tuition_fields
from scripts.seed import MAJORS
from scripts.seed_shanghai import import_shanghai

DATA = Path(__file__).resolve().parent.parent / "scraped-data"


class ShanghaiSourceTests(TestCase):
    def test_complete_pdf_rows_school_totals_and_page_boundary(self):
        actual = []
        for filename, url, year, round_name, line_type in SOURCES:
            plans, totals = parse_catalog(DATA / "sources/shanghai" / filename, year, round_name, line_type, url)
            actual.extend(plans)
        self.assertEqual(actual, json.loads((DATA / "shanghai-adult-programs.json").read_text()))
        self.assertEqual(len(actual), 679)
        dianji = [p for p in actual if p["year"] == 2025 and p["round"] == "主批次" and p["institution_code"] == "930"]
        self.assertEqual(len(dianji), 28)
        self.assertEqual(sum(p["plan_count"] for p in dianji), 2282)
        self.assertTrue(all(p["institution_name"] == "上海电机学院" for p in dianji))
        self.assertTrue(all(p["teaching_site"] or p["plan_count"] == 0 for p in actual))
        self.assertTrue(all(p["plan_count"] is None for p in actual if p["year"] == 2026))

    def test_control_parser_excludes_high_school_levels(self):
        actual = []
        for year, url in CONTROLS.items():
            actual.extend(parse_controls((DATA / f"sources/shanghai/controls-{year}.html").read_text(), year, url))
        self.assertEqual(actual, json.loads((DATA / "shanghai-adult-control-scores.json").read_text()))
        self.assertEqual(len(actual), 24)
        self.assertEqual([r["score"] for r in actual if r["year"] == 2025], [150, 131, 115, 113, 153, 152, 143, 154])


class ShanghaiImportTests(TestCase):
    def setUp(self):
        self.engine = create_engine("sqlite://")
        Base.metadata.create_all(self.engine)
        self.db = sessionmaker(bind=self.engine)()
        other = Province(code="other", name="其他省份")
        self.db.add(other)
        self.db.flush()
        self.other_school = Institution(code="901", name="保留的其他省院校", province_id=other.id)
        self.db.add(self.other_school)
        for record in MAJORS:
            self.db.add(Major(**{key: record[key] for key in ("code", "name", "category")}))
        self.db.commit()

    def tearDown(self):
        self.db.close()
        self.engine.dispose()

    def test_scoped_import_is_idempotent_and_preserves_major_and_other_provinces(self):
        self.assertEqual(import_shanghai(self.db), {"institutions_added": 40, "plans_added": 679, "controls_added": 24})
        self.db.commit()
        self.assertEqual(import_shanghai(self.db), {"institutions_added": 0, "plans_added": 0, "controls_added": 0})
        self.assertEqual(self.db.query(Major).count(), 66)
        self.assertEqual(self.db.query(Institution).count(), 41)
        self.assertEqual(self.other_school.name, "保留的其他省院校")
        self.assertEqual(self.other_school.plans, [])
        self.assertEqual(self.db.query(AdmissionScore).count(), 0)
        self.assertEqual(self.db.query(ProvinceControlScore).count(), 24)
        credit = self.db.query(AdmissionPlan).filter_by(tuition_unit="per_credit").all()
        self.assertEqual(len(credit), 235)
        self.assertTrue(all(p.tuition_amount is None and "元/学分" in p.tuition_raw for p in credit))
        self.assertTrue(any("96元/学分" == p.tuition_raw for p in credit))
        self.assertEqual(tuition_fields("93.8元/学分"), {
            "tuition_raw": "93.8元/学分", "tuition_amount": None, "tuition_unit": "per_credit",
        })

    def test_api_separates_controls_and_uses_current_catalog_and_supported_language(self):
        import_shanghai(self.db)
        schools = read_institutions(province="shanghai", major=None, db=self.db, _user=None)
        self.assertEqual(len(schools), 40)
        self.assertEqual(sum(bool(s.majors) for s in schools), 31)
        self.assertTrue(all(s.scores == [] and len(s.control_scores) == 24 for s in schools))
        self.assertTrue(all(s.source.provider == "上海市教育考试院" for s in schools))
        fudan = next(s for s in schools if s.code == "901")
        self.assertEqual(fudan.majors, [])  # 2026 only 护理学; 2025 computing is history.
        self.assertTrue(any(p.major_name == "计算机科学与技术" and p.year == 2025 for p in fudan.plans))
        self.assertTrue(all("riyu" not in s.majors for s in schools))
        tongji = next(s for s in schools if s.code == "902")
        self.assertEqual(tongji.active_catalog_year, 2026)
        current = [p for p in tongji.plans if p.year == 2026]
        self.assertTrue(all(p.plan_count is None and p.study_duration_raw == "三年" and p.foreign_language == "英语" for p in current))
        self.assertTrue(all(p.teaching_site and p.source_url for p in current))
        computers = read_institutions(province="shanghai", major="jisuanji", db=self.db, _user=None)
        self.assertNotIn("901", [s.code for s in computers])
