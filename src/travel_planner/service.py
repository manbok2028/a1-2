"""Orchestrate structured LLM recommendations, place search, and report generation."""

from __future__ import annotations

import json
from dataclasses import dataclass, field

from .clients import ApiRequestError
from .input_processing import normalize_city_names
from .models import ErrorRecord, Place, Recommendation, SchemaError


@dataclass
class TravelPlan:
    date: str
    recommendation: Recommendation
    restaurants_by_city: dict[str, list[Place]]
    errors: list[ErrorRecord]
    report_markdown: str
    requested_cities: list[str] = field(default_factory=list)

    def raw_data(self) -> dict[str, object]:
        return {
            "date": self.date,
            "recommendation": self.recommendation.to_dict(),
            "restaurants_by_city": {
                city: [place.to_dict() for place in places] for city, places in self.restaurants_by_city.items()
            },
            "errors": [error.to_dict() for error in self.errors],
            "requested_cities": self.requested_cities,
        }


class TravelPlanner:
    """Run the three-step API workflow with bounded retries and graceful place failures."""

    def __init__(self, llm_client, place_client) -> None:
        self.llm_client = llm_client
        self.place_client = place_client

    def create_plan(self, travel_date: str, preferred_cities: list[str] | None = None, progress=None) -> TravelPlan:
        requested_cities = normalize_city_names(preferred_cities or [])
        errors: list[ErrorRecord] = []
        recommendation = self._recommend(travel_date, requested_cities, errors)
        if progress is not None:
            progress("recommendation", recommendation)
        restaurants_by_city: dict[str, list[Place]] = {}
        for city in normalize_city_names([*requested_cities, *recommendation.cities]):
            try:
                restaurants_by_city[city] = self.place_client.search_restaurants(city, limit=5)
                if not restaurants_by_city[city]:
                    errors.append(ErrorRecord("place_search", "EMPTY_RESULT", f"0 results for query={city} 맛집"))
            except ApiRequestError as error:
                restaurants_by_city[city] = []
                errors.append(ErrorRecord("place_search", error.category, str(error)))
        if progress is not None:
            progress("place_search", restaurants_by_city)
        report = self._generate_report(travel_date, recommendation, restaurants_by_city, errors)
        if progress is not None:
            progress("report", report)
        return TravelPlan(travel_date, recommendation, restaurants_by_city, errors, report, requested_cities)

    def _recommend(self, travel_date: str, requested_cities: list[str], errors: list[ErrorRecord]) -> Recommendation:
        prompt = _recommendation_prompt(travel_date, requested_cities)
        for attempt in range(2):
            try:
                text = self.llm_client.complete(prompt, json_mode=True)
                return Recommendation.from_dict(_parse_json_text(text))
            except (SchemaError, json.JSONDecodeError) as error:
                if attempt == 0:
                    errors.append(ErrorRecord("recommendation", "JSON_PARSE_RETRY", str(error)))
                    prompt = _repair_prompt(travel_date, requested_cities)
                    continue
                errors.append(ErrorRecord("recommendation", "JSON_PARSE_ERROR", str(error)))
                raise SchemaError("LLM JSON parsing failed after one retry") from error
            except ApiRequestError as error:
                errors.append(ErrorRecord("recommendation", error.category, str(error)))
                raise
        raise AssertionError("unreachable")

    def _generate_report(self, travel_date: str, recommendation: Recommendation, restaurants: dict[str, list[Place]], errors: list[ErrorRecord]) -> str:
        prompt = _report_prompt(travel_date, recommendation, restaurants, errors)
        try:
            report = self.llm_client.complete(prompt)
            if report.strip():
                return report.strip()
            raise ApiRequestError("openai", "Empty report response")
        except ApiRequestError as error:
            errors.append(ErrorRecord("report_generation", error.category, str(error)))
            return render_fallback_report(travel_date, recommendation, restaurants, errors)


def _parse_json_text(text: str) -> dict[str, object]:
    cleaned = text.strip()
    if cleaned.startswith("```"):
        cleaned = cleaned.split("\n", maxsplit=1)[1] if "\n" in cleaned else ""
        if cleaned.rstrip().endswith("```"):
            cleaned = cleaned.rstrip()[:-3]
    data = json.loads(cleaned)
    if not isinstance(data, dict):
        raise SchemaError("LLM JSON root must be an object")
    return data


def _recommendation_prompt(travel_date: str, requested_cities: list[str]) -> str:
    requested = ", ".join(requested_cities) if requested_cities else "없음"
    return f"""사용자의 국내 여행 날짜는 {travel_date}입니다. 실제 예보 확정 정보가 아니라 일반적인 계절성 추천을 제공합니다.
사용자가 우선 검토해 달라고 입력한 지역: {requested}. 입력 지역이 있으면 추천 후보에 우선 포함하세요.
반드시 JSON 객체만 반환하세요. Markdown, 코드 펜스, 설명 문장을 절대 넣지 마세요.
필수 스키마:
{{
  \"recommended_city\": \"도시 1개\",
  \"recommended_cities\": [\"도시 1개 이상, 최대 3개\"],
  \"weather\": \"해당 시기 일반적 날씨 요약\",
  \"events\": [\"행사/축제 후보 1~3개\"],
  \"reason\": \"추천 근거 2~4문장\"
}}"""


def _repair_prompt(travel_date: str, requested_cities: list[str]) -> str:
    requested = ", ".join(requested_cities) if requested_cities else "없음"
    return f"""날짜 {travel_date}의 국내 여행 추천을 다시 작성하세요. 사용자 요청 지역은 {requested}입니다. 아래 필수 키를 가진 JSON 객체만 반환하세요.
recommended_city(string), recommended_cities(array of string), weather(string), events(array of string), reason(string)."""


def _report_prompt(travel_date: str, recommendation: Recommendation, restaurants: dict[str, list[Place]], errors: list[ErrorRecord]) -> str:
    payload = {
        "date": travel_date,
        "requested_cities": recommendation.cities,
        "recommendation": recommendation.to_dict(),
        "restaurants_by_city": {city: [place.to_dict() for place in places] for city, places in restaurants.items()},
        "errors": [error.to_dict() for error in errors],
    }
    instructions = (
        "다음 JSON 데이터를 바탕으로 한국어 Markdown 여행 리포트를 작성하세요. 다음 제목을 모두 포함하세요.\n"
        "# 날짜 국내 여행 추천 리포트\n## 추천 지역\n## 추천 이유\n## 날씨 요약\n## 행사/축제\n"
        "## 맛집 추천\n## 1일 일정 제안\n## 오류 요약(errors).\n"
        "맛집이 없으면 반드시 '데이터 없음'이라고 쓰세요. 입력 데이터에 없는 사실은 단정하지 마세요.\n\n"
    )
    return instructions + json.dumps(payload, ensure_ascii=False, indent=2)


def render_fallback_report(travel_date: str, recommendation: Recommendation, restaurants: dict[str, list[Place]], errors: list[ErrorRecord]) -> str:
    """Create a readable report when final LLM generation fails."""
    lines = [
        f"# {travel_date} 국내 여행 추천 리포트",
        "",
        "## 추천 지역",
        ", ".join(recommendation.cities),
        "",
        "## 추천 이유",
        recommendation.reason,
        "",
        "## 날씨 요약",
        recommendation.weather,
        "",
        "## 행사/축제",
        "",
        "## 맛집 추천",
    ]
    lines.extend([f"- {event}" for event in recommendation.events] or ["- 데이터 없음"])
    for city, places in restaurants.items():
        lines.append(f"### {city}")
        if not places:
            lines.append("- 데이터 없음")
        for place in places:
            lines.append(f"- **{place.name}** — {place.address} ({place.category or '분류 정보 없음'})")
    lines.extend(["", "## 1일 일정 제안", "- 오전: 지역 대표 산책·관광지 방문", "- 오후: 행사 또는 실내 문화 공간 방문", "- 저녁: 검색된 맛집 중 이동 동선을 고려해 선택", "", "## 오류 요약(errors)"])
    lines.extend([f"- [{error.step}/{error.type}] {error.message}" for error in errors] or ["- 없음"])
    return "\n".join(lines)
