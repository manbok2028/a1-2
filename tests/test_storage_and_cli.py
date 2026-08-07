import tempfile
import unittest
from pathlib import Path

from travel_planner.cli import parse_date
from travel_planner.models import ErrorRecord, Place, Recommendation
from travel_planner.service import TravelPlan
from travel_planner.storage import load_cached_plan, save_plan


class StorageAndCliTests(unittest.TestCase):
    def test_parse_date_accepts_iso_date(self):
        self.assertEqual(parse_date("2026-10-10"), "2026-10-10")

    def test_parse_date_rejects_invalid_date(self):
        with self.assertRaises(Exception):
            parse_date("2026/10/10")

    def test_save_and_load_cache_round_trip(self):
        plan = TravelPlan(
            "2026-10-10",
            Recommendation("강릉", "선선함", ["행사"], "추천 이유", ["강릉", "속초"]),
            {"강릉": [Place("맛집", "강릉시")]},
            [ErrorRecord("place_search", "EMPTY_RESULT", "0 results")],
            "# 리포트",
        )
        with tempfile.TemporaryDirectory() as temp_dir:
            results = Path(temp_dir)
            raw_path, report_path = save_plan(results, plan)
            loaded = load_cached_plan(results, "2026-10-10")
        self.assertTrue(raw_path.name.endswith("_raw.json"))
        self.assertTrue(report_path.name.endswith("_travel_plan.md"))
        self.assertIsNotNone(loaded)
        self.assertEqual(loaded.recommendation.recommended_city, "강릉")
        self.assertEqual(loaded.report_markdown, "# 리포트")
