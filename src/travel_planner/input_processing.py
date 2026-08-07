"""Normalize optional Korean travel-region input before it reaches an API query.

The program intentionally keeps this rule set small and explicit. It corrects
common city/region aliases, extracts more than one known region from free text,
and leaves unrelated words out of the place-search query.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Iterable


# This transparent table is safer than silently guessing a user's location.
CITY_ALIASES = {
    "강눙": "강릉",
    "강릉시": "강릉",
    "속초시": "속초",
    "서울시": "서울",
    "부산시": "부산",
    "대구시": "대구",
    "인천시": "인천",
    "광주시": "광주",
    "대전시": "대전",
    "울산시": "울산",
    "세종시": "세종",
    "제주도": "제주",
    "제주특별자치도": "제주",
    "강원도": "강원",
    "경기도": "경기",
    "전라남도": "전남",
    "전라북도": "전북",
    "경상남도": "경남",
    "경상북도": "경북",
    "충청남도": "충남",
    "충청북도": "충북",
}

KNOWN_REGIONS = (
    "서울", "부산", "대구", "인천", "광주", "대전", "울산", "세종", "수원", "강릉", "속초", "춘천",
    "제주", "전주", "여수", "경주", "포항", "안동", "청주", "천안", "군산", "목포", "통영", "거제",
    "강원", "경기", "전남", "전북", "경남", "경북", "충남", "충북",
)

_LOCATION_PATTERN = re.compile(
    "|".join(re.escape(value) for value in sorted((*CITY_ALIASES, *KNOWN_REGIONS), key=len, reverse=True))
)
_TERM_SEPARATOR = re.compile(r"[,/·|]+|\s+(?:그리고|및|또는|이랑|하고)\s+|\s+(?:과|와|랑)\s+|\s+")
_NOISE_TERMS = {"여행", "맛집", "추천", "가족", "데이트", "1박", "2일", "당일치기", "국내"}


@dataclass(frozen=True)
class CityInput:
    """The auditable outcome of parsing a free-text city preference."""

    cities: list[str]
    corrections: list[str]
    ignored_terms: list[str]


def normalize_city_names(candidates: Iterable[str]) -> list[str]:
    """Trim aliases and duplicates while keeping the first specified order."""

    normalized: list[str] = []
    for candidate in candidates:
        city = CITY_ALIASES.get(candidate.strip(), candidate.strip())
        if city and city not in normalized:
            normalized.append(city)
    return normalized


def parse_city_preferences(text: str) -> CityInput:
    """Extract regions from a multi-term preference such as ``강눙, 속초시 맛집``."""

    cities: list[str] = []
    corrections: list[str] = []
    for match in _LOCATION_PATTERN.finditer(text):
        source = match.group(0)
        city = CITY_ALIASES.get(source, source)
        if source != city:
            corrections.append(f"{source} -> {city}")
        if city not in cities:
            cities.append(city)

    remainder = _LOCATION_PATTERN.sub(" ", text)
    ignored_terms = [
        term.strip()
        for term in _TERM_SEPARATOR.split(remainder)
        if term.strip() and term.strip() not in _NOISE_TERMS
    ]
    return CityInput(cities=cities, corrections=corrections, ignored_terms=ignored_terms)
