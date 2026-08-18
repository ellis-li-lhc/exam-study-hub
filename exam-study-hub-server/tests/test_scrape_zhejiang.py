import json
from pathlib import Path
from unittest import TestCase

from scripts.scrape_zhejiang import CATEGORY_NAME_MAP, parse_control_scores


DATA_FILE = Path(__file__).resolve().parent.parent / "scraped-data" / "zhejiang-adult-control-scores.json"


class ZhejiangScrapedDataTest(TestCase):
    def test_parser_maps_official_categories_to_project_names(self):
        rows = "".join(
            f"<tr><td><span>{category}</span></td><td>{100 + index}</td></tr>"
            for index, category in enumerate(CATEGORY_NAME_MAP)
        )
        records = parse_control_scores(rows, {"year": 2025, "url": "https://example.test/source"})

        self.assertEqual(len(records), 8)
        self.assertEqual(records[0]["category_name"], "专升本文史中医类")
        self.assertEqual(records[-1]["category_name"], "专升本医学类")
        self.assertTrue(all(record["province"] == "zhejiang" for record in records))

    def test_generated_data_matches_existing_control_score_contract(self):
        records = json.loads(DATA_FILE.read_text(encoding="utf-8"))
        expected_keys = {
            "province",
            "year",
            "level",
            "institution_code",
            "institution_name",
            "category_code",
            "category_name",
            "score",
            "line_type",
            "round",
            "source_url",
            "fetch_url",
        }

        self.assertEqual(len(records), 64)
        self.assertEqual(
            {record["year"] for record in records},
            set(range(2018, 2026)),
        )
        self.assertTrue(all(set(record) == expected_keys for record in records))
        self.assertTrue(all(record["line_type"] == "省控线" for record in records))
        scores_2025 = {
            record["category_name"]: record["score"]
            for record in records
            if record["year"] == 2025
        }
        self.assertEqual(scores_2025, {
            "专升本文史中医类": 156,
            "专升本艺术类": 115,
            "专升本理工类": 110,
            "专升本经管类": 110,
            "专升本法学类": 130,
            "专升本教育学类": 110,
            "专升本农学类": 130,
            "专升本医学类": 110,
        })
        scores_2018 = {
            record["category_name"]: record["score"]
            for record in records
            if record["year"] == 2018
        }
        self.assertEqual(scores_2018, {
            "专升本文史中医类": 167,
            "专升本艺术类": 121,
            "专升本理工类": 120,
            "专升本经管类": 120,
            "专升本法学类": 137,
            "专升本教育学类": 131,
            "专升本农学类": 145,
            "专升本医学类": 138,
        })
