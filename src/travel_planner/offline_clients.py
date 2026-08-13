"""Offline clients that never call external APIs."""

from __future__ import annotations

import json

from .models import Place


class OfflineLlmClient:
    def complete(self, prompt: str, *, json_mode: bool = False) -> str:
        if not json_mode:
            return _rich_offline_report(prompt)
        if json_mode:
            return json.dumps(
                {
                    "recommended_city": "강릉",
                    "recommended_cities": ["강릉", "속초"],
                    "weather": "가을 초입의 선선한 날씨를 기준으로 여행 계획을 세웠습니다.",
                    "events": ["지역 문화 행사 후보", "계절 산책 프로그램 후보"],
                    "reason": "해안 산책과 지역 문화 공간을 함께 즐길 수 있는 여행지입니다. 실제 날씨와 행사 일정은 출발 전 다시 확인해야 합니다.",
                },
                ensure_ascii=False,
            )


class OfflinePlaceClient:
    def search_restaurants(self, city: str, limit: int = 5) -> list[Place]:
        return _demo_places(city, limit)
        return [
            Place(f"{city} 추천 식당 1", f"{city}시 주요 관광지 인근", "음식점 > 한식", "", 128.0, 37.0),
            Place(f"{city} 추천 카페 2", f"{city}시 주요 관광지 인근", "음식점 > 카페", "", 128.1, 37.1),
        ][:limit]


def _demo_places(city: str, limit: int) -> list[Place]:
    """Return clearly labelled offline examples with visible place details."""

    places_by_city = {
        "강릉": [
            Place("강릉 바다식당", "강원특별자치도 강릉시 해안로", "음식점 > 한식", "", 128.91, 37.78),
            Place("강릉 커피정원", "강원특별자치도 강릉시 경포로", "음식점 > 카페", "", 128.90, 37.80),
            Place("강릉 초당순두부길", "강원특별자치도 강릉시 초당동", "음식점 > 한식", "", 128.90, 37.79),
        ],
        "속초": [
            Place("속초 중앙시장 먹거리", "강원특별자치도 속초시 중앙로", "음식점 > 분식", "", 128.59, 38.20),
            Place("속초 항구회관", "강원특별자치도 속초시 항구로", "음식점 > 해산물", "", 128.60, 38.20),
            Place("속초 설악카페", "강원특별자치도 속초시 설악산로", "음식점 > 카페", "", 128.48, 38.17),
        ],
    }
    return places_by_city.get(
        city,
        [
            Place(f"{city} 지역 식당", f"{city} 주요 관광지 인근", "음식점 > 한식"),
            Place(f"{city} 지역 카페", f"{city} 주요 관광지 인근", "음식점 > 카페"),
        ],
    )[:limit]


def _rich_offline_report(prompt: str) -> str:
    """Create a complete offline report from the production report payload."""

    try:
        payload = json.loads(prompt[prompt.rfind("\n{") + 1 :])
    except (TypeError, ValueError, json.JSONDecodeError):
        payload = {}

    recommendation = payload.get("recommendation", {}) if isinstance(payload, dict) else {}
    restaurants = payload.get("restaurants_by_city", {}) if isinstance(payload, dict) else {}
    cities = recommendation.get("recommended_cities", []) if isinstance(recommendation, dict) else []
    if not cities and isinstance(recommendation, dict):
        cities = [recommendation.get("recommended_city", "강릉")]
    city_text = ", ".join(str(city) for city in cities if city) or "강릉, 속초"
    weather = str(recommendation.get("weather", "가을 여행을 위한 날씨 가이드입니다."))
    reason = str(recommendation.get("reason", "해안 산책과 지역 문화 공간을 함께 즐길 수 있습니다."))
    events = recommendation.get("events", []) if isinstance(recommendation, dict) else []

    lines = [
        "# 국내 여행 추천 리포트",
        "",
        "## 추천 지역",
        city_text,
        "",
        "## 추천 이유",
        reason,
        "",
        "## 여행 시기 날씨 가이드",
        weather,
        "",
        "> 이 날씨 정보는 여행 계획을 위한 계절 참고 가이드입니다. 실제 출발 전에는 기상청 등 공식 예보를 확인하세요.",
        "",
        "## 행사/계절 참고",
    ]
    lines.extend([f"- {event}" for event in events] or ["- 지역 행사 정보는 출발 전 공식 채널에서 확인하세요."])
    lines.extend(["", "## 맛집 및 장소 검색 결과"])

    if isinstance(restaurants, dict):
        for city, places in restaurants.items():
            lines.append(f"### {city}")
            if not isinstance(places, list) or not places:
                lines.append("- 검색 결과가 없습니다.")
                continue
            for place in places:
                if not isinstance(place, dict):
                    continue
                name = str(place.get("name", "이름 없음"))
                category = str(place.get("category", "분류 정보 없음"))
                address = str(place.get("address", "주소 정보 없음"))
                lines.append(f"- **{name}** — {category} · {address}")

    lines.extend(
        [
            "",
            "## 1일 일정 제안",
            "- 오전: 추천 지역의 해안·시장·산책 공간 중 한 곳을 선택합니다.",
            "- 오후: 날씨와 이동 시간을 고려해 문화 공간 또는 카페를 방문합니다.",
            "- 저녁: 위 검색 결과 중 운영 시간과 위치를 확인한 뒤 식당을 선택합니다.",
            "",
            "## 참고 사항",
            "- 출발 전에는 기상청 등 공식 예보와 장소 운영 정보를 확인하세요.",
        ]
    )
    return "\n".join(lines)
