"""Typed data models for the travel recommendation pipeline."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any

from .input_processing import normalize_city_names


class SchemaError(ValueError):
    """Raised when the LLM does not return the required JSON schema."""


@dataclass
class Recommendation:
    recommended_city: str
    weather: str
    events: list[str]
    reason: str
    recommended_cities: list[str] = field(default_factory=list)

    @property
    def cities(self) -> list[str]:
        """Return unique cities, keeping the required primary city first."""
        return normalize_city_names([self.recommended_city, *self.recommended_cities])

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "Recommendation":
        required_strings = ("recommended_city", "weather", "reason")
        if any(not isinstance(data.get(key), str) or not data[key].strip() for key in required_strings):
            raise SchemaError("recommended_city, weather, reason must be non-empty strings")
        events = data.get("events")
        if not isinstance(events, list) or not all(isinstance(event, str) for event in events):
            raise SchemaError("events must be an array of strings")
        cities = data.get("recommended_cities", [])
        if not isinstance(cities, list) or not all(isinstance(city, str) for city in cities):
            raise SchemaError("recommended_cities must be an array of strings when provided")
        return cls(
            recommended_city=data["recommended_city"].strip(),
            weather=data["weather"].strip(),
            events=[event.strip() for event in events if event.strip()],
            reason=data["reason"].strip(),
            recommended_cities=[city.strip() for city in cities if city.strip()],
        )

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class Place:
    name: str
    address: str
    category: str = ""
    url: str = ""
    x: float | None = None
    y: float | None = None

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "Place":
        return cls(
            name=str(data.get("name", "")),
            address=str(data.get("address", "")),
            category=str(data.get("category", "")),
            url=str(data.get("url", "")),
            x=_optional_float(data.get("x")),
            y=_optional_float(data.get("y")),
        )

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class ErrorRecord:
    step: str
    type: str
    message: str

    def to_dict(self) -> dict[str, str]:
        return asdict(self)


def _optional_float(value: object) -> float | None:
    if value in (None, ""):
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None
