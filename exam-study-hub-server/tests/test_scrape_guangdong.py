import json
import unittest
from pathlib import Path

from scripts.scrape_guangdong import GROUP_TO_CATEGORY, parse_control_scores


DATA_DIR = Path(__file__).resolve().parent.parent / "scraped-data"


class GuangdongScraperTests(unittest.TestCase):
    def test_generated_data_counts_and_identity(self):
        plans = json.loads((DATA_DIR / "guangdong-adult-program-plan-2025.json").read_text(encoding="utf-8"))
        scores = json.loads((DATA_DIR / "guangdong-adult-scores.json").read_text(encoding="utf-8"))
        controls = json.loads((DATA_DIR / "guangdong-adult-control-scores.json").read_text(encoding="utf-8"))

        self.assertEqual(len(plans), 746)
        self.assertEqual(len(scores), 199)
        self.assertEqual(len(controls), 9)
        self.assertEqual(len({item["institution_code"] for item in plans}), 79)
        self.assertEqual(len({item["institution_code"] for item in scores}), 79)
        self.assertTrue(all(item["province"] == "guangdong" for item in plans + scores + controls))
        self.assertTrue(all(item["category_name"] in GROUP_TO_CATEGORY.values() for item in plans + scores))
        self.assertNotIn("广东省教育考试院", "".join(item["institution_name"] for item in plans + scores))

    def test_control_score_parser_handles_spaced_digits(self):
        html = b"""
        <h1>2025</h1><p>\xe4\xb8\x93\xe7\xa7\x91\xe5\x8d\x87\xe6\x9c\xac\xe7\xa7\x91</p>
        <p>\xe6\x96\x87\xe5\x8f\xb2\xe3\x80\x81\xe4\xb8\xad\xe5\x8c\xbb\xe7\xb1\xbb\xef\xbc\x8c\xe6\xb3\x95\xe5\xad\xa6\xe7\xb1\xbb\xef\xbc\x8c\xe6\x95\x99\xe8\x82\xb2\xe7\xb1\xbb\xef\xbc\x8c\xe5\x8c\xbb\xe5\xad\xa6\xe7\xb1\xbb\xef\xbc\x8c\xe5\x86\x9c\xe5\xad\xa6\xe7\xb1\xbb\xef\xbc\x9a1 2 0\xe5\x88\x86</p>
        <p>\xe8\x89\xba\xe6\x9c\xaf\xe7\xb1\xbb\xef\xbc\x8c\xe4\xbd\x93\xe8\x82\xb2\xe7\xb1\xbb\xef\xbc\x9a1 1 5\xe5\x88\x86</p>
        <p>\xe7\x90\x86\xe5\xb7\xa5\xe3\x80\x81\xe7\xbb\x8f\xe7\xae\xa1\xe7\xb1\xbb\xef\xbc\x9a1 0 0\xe5\x88\x86</p>
        <p>\xe9\xab\x98\xe4\xb8\xad\xe8\xb5\xb7\xe7\x82\xb9\xe6\x9c\xac\xe7\xa7\x91</p>
        """
        records = parse_control_scores(html)
        self.assertEqual(len(records), 9)
        by_name = {item["category_name"]: item["score"] for item in records}
        self.assertEqual(by_name["专升本文史中医类"], 120)
        self.assertEqual(by_name["专升本艺术类"], 115)
        self.assertEqual(by_name["专升本经管类"], 100)


if __name__ == "__main__":
    unittest.main()
