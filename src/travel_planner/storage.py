"""Result-file persistence and cache loading."""

from __future__ import annotations

import json
from pathlib import Path

from .models import ErrorRecord, Place, Recommendation
from .service import TravelPlan


def result_paths(results_dir: Path, travel_date: str) -> tuple[Path, Path]:
    return results_dir / f"{travel_date}_raw.json", results_dir / f"{travel_date}_travel_plan.md"


def save_plan(results_dir: Path, plan: TravelPlan) -> tuple[Path, Path]:
    results_dir.mkdir(parents=True, exist_ok=True)
    raw_path, report_path = result_paths(results_dir, plan.date)
    raw_path.write_text(json.dumps(plan.raw_data(), ensure_ascii=False, indent=2), encoding="utf-8")
    report_path.write_text(plan.report_markdown, encoding="utf-8")
    return raw_path, report_path


def load_cached_plan(results_dir: Path, travel_date: str) -> TravelPlan | None:
    raw_path, report_path = result_paths(results_dir, travel_date)
    if not raw_path.exists() or not report_path.exists():
        return None
    try:
        raw = json.loads(raw_path.read_text(encoding="utf-8"))
        recommendation = Recommendation.from_dict(raw["recommendation"])
        restaurants = {
            str(city): [Place.from_dict(item) for item in items]
            for city, items in raw["restaurants_by_city"].items()
            if isinstance(items, list)
        }
        errors = [ErrorRecord(**item) for item in raw.get("errors", []) if isinstance(item, dict)]
        return TravelPlan(
            travel_date,
            recommendation,
            restaurants,
            errors,
            report_path.read_text(encoding="utf-8"),
            [str(city) for city in raw.get("requested_cities", []) if isinstance(city, str)],
            int(raw.get("trip_days", 1)),
            [str(interest) for interest in raw.get("interests", []) if isinstance(interest, str)],
        )
    except (OSError, KeyError, TypeError, ValueError, json.JSONDecodeError):
        return None
