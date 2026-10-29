import hashlib
import json
from pathlib import Path
from unittest import TestCase

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

import app.models  # noqa: F401
from app.db.base import Base
from app.models.catalog import AdmissionPlan, AdmissionScore, Institution, Major, Province, ProvinceControlScore
from app.routers.institutions import read_institutions
from scripts.scrape_shandong import BASE, ROOT, SOURCES, parse_programs
from scripts.seed import MAJORS
from scripts.seed_shandong import import_shandong

DATA = Path(__file__).resolve().parent.parent / "scraped-data"


class ShandongSourceTests(TestCase):
    def test_all_source_rows_reconcile_and_batches_link_by_official_code(self):
        actual = []
        for filename, route, article_id, year, batch in SOURCES:
            rows, summary = parse_programs(ROOT / filename, year, batch, BASE + route)
            self.assertEqual(len(rows) + sum(summary["excluded_levels"].values()), summary["source_data_rows"])
            actual.extend(rows)
        stored = json.loads((DATA / "shandong-adult-programs.json").read_text())
        base = {r["major_code"]: r for r in actual if r["year"] == 2025 and r["line_type"] == "招生专业目录"}
        for row in actual:
            if row["line_type"] == "征集计划": row["national_major_code"] = base[row["major_code"]]["national_major_code"]
        self.assertEqual(actual, stored)
        self.assertEqual(len(actual), 2738)
        self.assertEqual(sum(r["plan_count"] for r in actual if r["round"] == "第一次征集志愿"), 8180)
        self.assertEqual(sum(r["plan_count"] for r in actual if r["round"] == "第二次征集志愿"), 7173)
        self.assertTrue(all(r["plan_count"] is None for r in actual if r["line_type"] == "招生专业目录"))
        self.assertTrue(all(r["tuition_raw"] is None and r["teaching_site"] is None for r in actual))
        self.assertTrue(any("职业本科" in r["major_name"] for r in actual))

    def test_control_transcription_is_pinned_to_visually_reviewed_images(self):
        reviewed = json.loads((DATA / "shandong-controls-reviewed.json").read_text())
        controls = json.loads((DATA / "shandong-adult-control-scores.json").read_text())
        self.assertEqual(len(controls), 29)
        for year, review in reviewed.items():
            self.assertEqual(hashlib.sha256((ROOT / f"controls-{year}.png").read_bytes()).hexdigest(), review["sha256"])
            self.assertEqual(len([r for r in controls if r["year"] == int(year)]), len(review["rows"]))
        values = {r["category_name"]: r["score"] for r in controls if r["year"] == 2025}
        self.assertEqual(values["文史类"], 130)
        self.assertEqual(values["中医类"], 120)
        self.assertNotIn("体育类", values)


class ShandongImportTests(TestCase):
    def setUp(self):
        self.engine = create_engine("sqlite://")
        Base.metadata.create_all(self.engine)
        self.db = sessionmaker(bind=self.engine)()
        other = Province(code="other", name="其他省份")
        self.db.add(other)
        self.db.flush()
        self.other = Institution(code="028", name="保留的同码院校", province_id=other.id)
        self.db.add(self.other)
        for record in MAJORS: self.db.add(Major(**{k: record[k] for k in ("code", "name", "category")}))
        self.db.commit()

    def tearDown(self):
        self.db.close()
        self.engine.dispose()

    def test_scoped_import_is_repeatable_without_fake_scores_or_major_changes(self):
        self.assertEqual(import_shandong(self.db), {"institutions_added": 89, "plans_added": 2738, "controls_added": 29})
        self.db.commit()
        self.assertEqual(import_shandong(self.db), {"institutions_added": 0, "plans_added": 0, "controls_added": 0})
        self.assertEqual(self.db.query(Institution).count(), 90)
        self.assertEqual(self.db.query(Major).count(), 66)
        self.assertEqual(self.db.query(AdmissionScore).count(), 0)
        self.assertEqual(self.other.name, "保留的同码院校")
        self.assertEqual(self.other.plans, [])
        plans = self.db.query(AdmissionPlan).all()
        self.assertTrue(all(p.tuition_amount is None and p.teaching_site is None for p in plans))
        self.assertEqual(self.db.query(ProvinceControlScore).count(), 29)

    def test_api_matches_current_catalog_and_keeps_restrictions_and_old_names(self):
        import_shandong(self.db)
        schools = read_institutions(province="shandong", major=None, db=self.db, _user=None)
        self.assertEqual(len(schools), 89)
        self.assertEqual(sum(bool(s.majors) for s in schools), 76)
        self.assertTrue(all(s.active_catalog_year == 2026 and s.scores == [] and len(s.control_scores) == 29 for s in schools))
        self.assertTrue(all(s.source.provider == "山东省教育招生考试院" and s.city for s in schools))
        self.assertTrue(all(p.level == "专升本" for p in self.db.query(AdmissionPlan)))
        old_only = next(s for s in schools if s.code == "214")
        self.assertEqual(old_only.majors, [])
        renamed = next(s for s in schools if s.code == "114")
        self.assertEqual(renamed.name, "山东医药大学")
        police = next(s for s in schools if s.code == "110")
        self.assertTrue(any(p.remarks and "民警" in p.remarks and p.enrollment_scope == "直属与委培" for p in police.plans))
        medical = next(s for s in schools if s.code == "111")
        tcm = [p for p in medical.plans if p.year == 2026 and p.major_name == "中医学"]
        self.assertTrue(tcm and all(p.category_name == "中医类" for p in tcm))
        vocational = next(s for s in schools if s.code == "006")
        self.assertEqual(vocational.majors, [])
        self.assertTrue(any("职业本科" in p.major_name for p in vocational.plans))
