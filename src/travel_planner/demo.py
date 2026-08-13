"""Explicit offline demonstration clients. They never call external APIs."""

from __future__ import annotations

import json

from .models import Place


class DemoLlmClient:
    def complete(self, prompt: str, *, json_mode: bool = False) -> str:
        if json_mode:
            return json.dumps(
                {
                    "recommended_city": "강릉",
                    "recommended_cities": ["강릉", "속초"],
                    "weather": "가을 초입의 선선한 날씨를 가정한 예시입니다.",
                    "events": ["지역 문화 행사 후보", "계절 산책 프로그램 후보"],
                    "reason": "해안 산책과 지역 문화 공간을 함께 즐길 수 있는 예시 추천입니다. 실제 날씨와 행사 일정은 출발 전 다시 확인해야 합니다.",
                },
                ensure_ascii=False,
            )
        return "# 데모 국내 여행 추천 리포트\n\n## 추천 지역\n강릉, 속초\n\n## 추천 이유\nAPI 키 없이 흐름을 확인하기 위한 데모 결과입니다.\n\n## 날씨 요약\n실제 예보가 아닌 데모 정보입니다.\n\n## 행사/축제\n- 지역 문화 행사 후보\n\n## 맛집 추천\n- 데모 맛집 데이터\n\n## 1일 일정 제안\n- 오전: 해안 산책\n- 오후: 문화 공간 방문\n- 저녁: 지역 음식 체험\n\n## 오류 요약(errors)\n- 없음"


class DemoPlaceClient:
    def search_restaurants(self, city: str, limit: int = 5) -> list[Place]:
        return _demo_places(city, limit)
        return [
            Place(f"{city} 데모 맛집 1", f"{city}시 예시로 1", "음식점 > 한식", "", 128.0, 37.0),
            Place(f"{city} 데모 맛집 2", f"{city}시 예시로 2", "음식점 > 카페", "", 128.1, 37.1),
        ][:limit]


def _demo_places(city: str, limit: int) -> list[Place]:
    """Return clearly labelled offline examples with visible place details."""

    places_by_city = {
        "강릉": [
            Place("강릉 바다식당 (데모)", "강원특별자치도 강릉시 해안로 예시", "음식점 > 한식", "", 128.91, 37.78),
            Place("강릉 커피정원 (데모)", "강원특별자치도 강릉시 경포로 예시", "음식점 > 카페", "", 128.90, 37.80),
            Place("강릉 초당순두부길 (데모)", "강원특별자치도 강릉시 초당동 예시", "음식점 > 한식", "", 128.90, 37.79),
        ],
        "속초": [
            Place("속초 중앙시장 먹거리 (데모)", "강원특별자치도 속초시 중앙로 예시", "음식점 > 분식", "", 128.59, 38.20),
            Place("속초 항구회관 (데모)", "강원특별자치도 속초시 항구로 예시", "음식점 > 해산물", "", 128.60, 38.20),
            Place("속초 설악카페 (데모)", "강원특별자치도 속초시 설악산로 예시", "음식점 > 카페", "", 128.48, 38.17),
        ],
    }
    return places_by_city.get(
        city,
        [
            Place(f"{city} 지역 식당 (데모)", f"{city} 예시 주소", "음식점 > 한식"),
            Place(f"{city} 지역 카페 (데모)", f"{city} 예시 주소", "음식점 > 카페"),
        ],
    )[:limit]
