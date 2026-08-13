import json
import unittest

from travel_planner.clients import ApiRequestError
from travel_planner.demo import DemoLlmClient, DemoPlaceClient
from travel_planner.models import Place
from travel_planner.service import TravelPlanner


class FakeLlm:
    def __init__(self, answers):
        self.answers = list(answers)
        self.calls = []

    def complete(self, prompt, *, json_mode=False):
        self.calls.append(json_mode)
        return self.answers.pop(0)


class FakePlaces:
    def __init__(self, responses):
        self.responses = responses

    def search_restaurants(self, city, limit=5):
        response = self.responses[city]
        if isinstance(response, Exception):
            raise response
        return response


def recommendation_json(city="강릉"):
    return json.dumps(
        {
            "recommended_city": city,
            "recommended_cities": [city, "속초"],
            "weather": "선선한 날씨",
            "events": ["지역 행사"],
            "reason": "해안과 문화 공간을 함께 즐기기 좋습니다.",
        }
    )


class TravelPlannerTests(unittest.TestCase):
    def test_example_report_keeps_weather_and_place_details_visible(self):
        plan = TravelPlanner(DemoLlmClient(), DemoPlaceClient()).create_plan("2026-10-10")

        self.assertIn("여행 시기 날씨 가이드", plan.report_markdown)
        self.assertIn(plan.recommendation.weather, plan.report_markdown)
        self.assertIn("맛집 및 장소 검색 결과", plan.report_markdown)
        self.assertIn("강릉 바다식당 (예시)", plan.report_markdown)
        self.assertNotIn("데모 맛집 데이터", plan.report_markdown)
        self.assertNotIn("실제 예보가 아닌 데모 정보", plan.report_markdown)

    def test_creates_plan_with_restaurants_and_markdown_report(self):
        llm = FakeLlm([recommendation_json(), "# 여행 리포트\n\n## 추천 지역\n강릉"])
        places = FakePlaces({"강릉": [Place("맛집", "강릉시")], "속초": []})
        plan = TravelPlanner(llm, places).create_plan("2026-10-10")
        self.assertEqual(plan.recommendation.recommended_city, "강릉")
        self.assertEqual(len(plan.restaurants_by_city["강릉"]), 1)
        self.assertTrue(any(error.type == "EMPTY_RESULT" for error in plan.errors))
        self.assertIn("# 여행 리포트", plan.report_markdown)

    def test_retries_once_when_llm_json_is_invalid(self):
        llm = FakeLlm(["JSON이 아닙니다", recommendation_json(), "# 리포트"])
        places = FakePlaces({"강릉": [], "속초": []})
        plan = TravelPlanner(llm, places).create_plan("2026-10-10")
        self.assertEqual(plan.recommendation.recommended_city, "강릉")
        self.assertEqual(llm.calls[:2], [True, True])
        self.assertTrue(any(error.type == "JSON_PARSE_RETRY" for error in plan.errors))

    def test_place_auth_failure_keeps_report_generation_running(self):
        llm = FakeLlm([recommendation_json("제주"), "# 리포트"])
        error = ApiRequestError("kakao", "HTTP 401", 401)
        places = FakePlaces({"제주": error, "속초": error})
        plan = TravelPlanner(llm, places).create_plan("2026-10-10")
        self.assertEqual(plan.restaurants_by_city["제주"], [])
        self.assertTrue(any(item.type == "AUTH_ERROR" for item in plan.errors))
        self.assertTrue(plan.report_markdown.startswith("# 리포트"))
        self.assertIn("장소·맛집 검색 결과", plan.report_markdown)
        self.assertIn("검색 결과가 없습니다.", plan.report_markdown)
