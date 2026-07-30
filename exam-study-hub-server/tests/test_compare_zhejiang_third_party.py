import json
from pathlib import Path
from unittest import TestCase

from scripts.compare_zhejiang_third_party import (
    normalize_institution,
    normalize_major,
    parse_official_institutions,
    parse_official_program_sample,
)


DATA_DIR = Path(__file__).resolve().parent.parent / "scraped-data" / "third-party"


class ZhejiangThirdPartyComparisonTest(TestCase):
    def test_normalizes_historical_names_without_hiding_source_values(self):
        self.assertEqual(normalize_institution("嘉兴学院"), "嘉兴大学")
        self.assertEqual(normalize_institution("浙江科技学院"), "浙江科技大学")
        self.assertEqual(normalize_major("浙江计算机科学与技术专业"), "计算机科学与技术")

    def test_parses_official_baselines(self):
        institutions = parse_official_institutions(
            '<a href="a.pdf">450 浙江理工大学.pdf</a>'
            '<a href="b.pdf">402 嘉兴大学.pdf</a>'
        )
        self.assertEqual(institutions, {"402": "嘉兴大学", "450": "浙江理工大学"})

        header = ["层次", "学习形式", "学制", "教学点", "专业名称", "学校代码", "专业代码", "科类名称", "备注"]
        row = ["专升本", "非脱产", "2.5", "教学点", "计算机科学与技术", "450", "434", "理工类", ""]
        page = "<table><tr>" + "".join(f"<td>{value}</td>" for value in header) + "</tr><tr>" + "".join(f"<td>{value}</td>" for value in row) + "</tr></table>"
        self.assertEqual(parse_official_program_sample(page), {("专升本", "计算机科学与技术")})

    def test_generated_report_is_quarantined_and_traceable(self):
        report = json.loads(
            (DATA_DIR / "zhejiang-comparison-report.json").read_text(encoding="utf-8")
        )
        self.assertEqual(report["import_recommendation"], "quarantine")
        self.assertEqual(report["official_baseline"]["institution_count"], 92)
        self.assertIn("source_url", report["official_program_sample_check"])
        self.assertGreater(report["sources"]["zj-ck.com"]["record_count"], 0)
        self.assertGreater(report["sources"]["zjck.org.cn"]["record_count"], 0)
