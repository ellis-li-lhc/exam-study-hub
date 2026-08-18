import json
from pathlib import Path
from unittest import TestCase

from scripts.scrape_zhejiang_programs import (
    internal_major_code,
    parse_charter_links,
    parse_programs,
)


DATA_FILE = (
    Path(__file__).resolve().parent.parent
    / "scraped-data"
    / "zhejiang-adult-program-catalog-2025.json"
)


class ZhejiangProgramCatalogTest(TestCase):
    def test_parses_official_pdf_index_with_nested_icon(self):
        page = (
            '<a href="/download/013.pdf"><img src="pdf.png">'
            '013 浙江国际海运职业技术学院.pdf</a>'
        )
        self.assertEqual(
            parse_charter_links(page, "https://www.zjzs.net/index.html"),
            [{
                "institution_code": "013",
                "institution_name": "浙江国际海运职业技术学院",
                "source_url": "https://www.zjzs.net/download/013.pdf",
            }],
        )

    def test_parses_common_multi_level_and_inline_category_layouts(self):
        common = (
            "高起专：文史类：工商企业管理；"
            "专升本：经管类：工商管理、会计学；理工类：计算机科学与技术；"
        )
        self.assertEqual(parse_programs(common, "999"), [
            ("专升本经管类", "工商管理"),
            ("专升本经管类", "会计学"),
            ("专升本理工类", "计算机科学与技术"),
        ])

        inline = "专升本：学前教育（教育类）、化学工程与工艺（理工类）"
        self.assertEqual(parse_programs(inline, "998"), [
            ("专升本教育学类", "学前教育"),
            ("专升本理工类", "化学工程与工艺"),
        ])

        parenthesized = (
            "高中起点专科：文史类（工商企业管理）；"
            "专科起点本科：经管类（电子商务、金融工程）、"
            "教育学类（小学教育）"
        )
        self.assertEqual(parse_programs(parenthesized, "997"), [
            ("专升本经管类", "电子商务"),
            ("专升本经管类", "金融工程"),
            ("专升本教育学类", "小学教育"),
        ])

    def test_generated_catalog_is_complete_traceable_and_non_speculative(self):
        records = json.loads(DATA_FILE.read_text(encoding="utf-8"))
        expected_keys = {
            "province",
            "year",
            "level",
            "institution_code",
            "institution_name",
            "major_code",
            "major_name",
            "category_code",
            "category_name",
            "plan_count",
            "line_type",
            "round",
            "source_url",
        }

        self.assertEqual(len(records), 541)
        self.assertEqual(len({record["institution_code"] for record in records}), 47)
        self.assertTrue(all(set(record) == expected_keys for record in records))
        self.assertTrue(all(record["province"] == "zhejiang" for record in records))
        self.assertTrue(all(record["year"] == 2025 for record in records))
        self.assertTrue(all(record["level"] == "专升本" for record in records))
        self.assertTrue(all(record["plan_count"] is None for record in records))
        self.assertTrue(all(record["line_type"] == "招生专业目录" for record in records))
        self.assertTrue(all(record["round"] == "2025招生章程" for record in records))
        self.assertTrue(all(record["major_code"].startswith("charter-") for record in records))
        self.assertTrue(all("zjzs.net" in record["source_url"] for record in records))

        pairs = {
            (record["institution_code"], record["major_name"])
            for record in records
        }
        self.assertEqual(len(pairs), len(records))
        self.assertIn(("138", "软件工程"), pairs)
        self.assertIn(("450", "汉语言文学"), pairs)
        self.assertNotIn(("418", "工商企业管理"), pairs)

    def test_internal_major_code_is_stable_and_explicitly_synthetic(self):
        first = internal_major_code("专升本理工类", "计算机科学与技术")
        second = internal_major_code("专升本理工类", "计算机科学与技术")
        self.assertEqual(first, second)
        self.assertRegex(first, r"^charter-[0-9a-f]{10}$")
