import json
from pathlib import Path
from unittest import TestCase

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

import app.models  # noqa: F401
from app.db.base import Base
from app.models.catalog import AdmissionPlan, AdmissionScore, Institution, Major, Province, ProvinceControlScore
from app.routers.institutions import read_institutions
from scripts.scrape_hebei import CONTROL_SOURCES, PLAN_SOURCES, ROOT, fee_fields, parse_controls, parse_plan
from scripts.seed import MAJORS
from scripts.seed_hebei import import_hebei

DATA = Path(__file__).resolve().parent.parent / "scraped-data"


class HebeiSourceTests(TestCase):
    def test_pdf_extraction_preserves_rows_fees_remarks_and_year_specific_identity(self):
        stored = json.loads((DATA / "hebei-adult-programs.json").read_text())
        for year, (_, url) in PLAN_SOURCES.items():
            actual = parse_plan(ROOT / f"plan-{year}.pdf", year, url)
            expected = [{k: v for k, v in row.items() if k != "institution_code"} for row in stored if row["year"] == year]
            self.assertEqual(actual, expected)
        self.assertEqual(len(stored), 1709)
        self.assertEqual(sum(p["plan_count"] for p in stored if p["year"] == 2024), 122118)
        self.assertEqual(sum(p["plan_count"] for p in stored if p["year"] == 2025), 108889)
        self.assertTrue(all(p["teaching_site"] and p["tuition_raw"] and p["source_page"] for p in stored))
        transport = next(p for p in stored if p["institution_name"] == "北京交通大学" and p["year"] == 2025)
        self.assertEqual(transport["tuition_raw"], "8000元/2.5年")
        self.assertEqual(transport["tuition_unit"], "total")
        self.assertNotIn("元", transport["teaching_site"])
        self.assertIn("职工报考", transport["remarks"])
        changed = [p for p in stored if p["institution_name"] == "河北医科大学"]
        self.assertEqual({p["institution_code"] for p in changed}, {"147"})
        self.assertEqual({p["institution_code_raw"] for p in changed if p["year"] == 2024}, {"146"})
        self.assertEqual(fee_fields("1852.8元/年"), {"tuition_raw": "1852.8元/年", "tuition_amount": None, "tuition_unit": "per_academic_year"})

    def test_html_control_groups_reconcile_without_inventing_missing_2023_special_lines(self):
        actual = []
        for year, url in CONTROL_SOURCES.items():
            filename = "controls-2023-university.html" if year == 2023 else f"controls-{year}.html"
            actual.extend(parse_controls((ROOT / filename).read_text(), year, url))
        self.assertEqual(actual, json.loads((DATA / "hebei-adult-control-scores.json").read_text()))
        self.assertEqual(len(actual), 45)
        self.assertEqual(sum(row["round"] == "统考生" for row in actual), 27)
        self.assertEqual(sum(row["round"] == "农民工考生" for row in actual), 18)
        self.assertEqual([r["score"] for r in actual if r["year"] == 2025 and r["category_name"] == "文史类"], [103, 102])


class HebeiImportTests(TestCase):
    def setUp(self):
        self.engine = create_engine("sqlite://")
        Base.metadata.create_all(self.engine)
        self.db = sessionmaker(bind=self.engine)()
        province = Province(code="other", name="其他省份")
        self.db.add(province)
        self.db.flush()
        self.other = Institution(code="146", name="保留的同码院校", province_id=province.id)
        self.db.add(self.other)
        for record in MAJORS: self.db.add(Major(**{field: record[field] for field in ("code", "name", "category")}))
        self.db.commit()

    def tearDown(self):
        self.db.close()
        self.engine.dispose()

    def test_scoped_repeatable_import_preserves_groups_fees_and_other_provinces(self):
        self.assertEqual(import_hebei(self.db), {"institutions_added": 87, "plans_added": 1709, "controls_added": 45})
        self.db.commit()
        self.assertEqual(import_hebei(self.db), {"institutions_added": 0, "plans_added": 0, "controls_added": 0})
        self.assertEqual(self.other.name, "保留的同码院校")
        self.assertEqual(self.other.plans, [])
        self.assertEqual(self.db.query(Major).count(), 66)
        self.assertEqual(self.db.query(AdmissionScore).count(), 0)
        self.assertEqual(self.db.query(ProvinceControlScore).count(), 45)
        self.assertEqual(self.db.query(AdmissionPlan).filter_by(tuition_unit="total").count(), 104)
        self.assertEqual(self.db.query(AdmissionPlan).filter_by(tuition_unit="per_academic_year").count(), 1597)

    def test_api_does_not_mix_cross_year_schools_subject_categories_or_control_groups(self):
        import_hebei(self.db)
        schools = read_institutions(province="hebei", major=None, db=self.db, _user=None)
        self.assertEqual(len(schools), 87)
        self.assertEqual(sum(bool(s.majors) for s in schools), 77)
        self.assertEqual(sum(len(s.majors) for s in schools), 475)
        self.assertTrue(all(s.active_catalog_year == 2025 and s.scores == [] and len(s.control_scores) == 45 for s in schools))
        self.assertTrue(all(s.source.provider == "河北省教育考试院" for s in schools))
        medical = next(s for s in schools if s.code == "147")
        foreign = next(s for s in schools if s.code == "146")
        self.assertEqual(medical.name, "河北医科大学")
        self.assertEqual(foreign.name, "河北外国语学院")
        self.assertEqual({p.institution_code_raw for p in medical.plans if p.year == 2024}, {"146"})
        self.assertTrue(all("yingyong-xinli" not in s.majors for s in schools))
        self.assertTrue(any(p.major_name == "应用心理学" for s in schools for p in s.plans))
        retired = next(s for s in schools if s.name == "渤海大学")
        dalian = next(s for s in schools if s.name == "大连海事大学")
        self.assertEqual(retired.code, "2024-306")
        self.assertEqual(retired.majors, [])
        self.assertEqual(dalian.code, "306")
        self.assertTrue(all(p.teaching_site and p.tuition_raw and p.source_page for s in schools for p in s.plans))
