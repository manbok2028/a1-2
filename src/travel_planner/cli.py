"""Command-line entry point for the domestic travel planner."""

from __future__ import annotations

import argparse
from datetime import datetime
from pathlib import Path

from .clients import ApiRequestError, KakaoLocalClient, OpenAIClient
from .config import ConfigurationError, get_settings, load_dotenv
from .offline_clients import OfflineLlmClient, OfflinePlaceClient
from .input_processing import parse_city_preferences
from .service import TravelPlanner
from .storage import load_cached_plan, save_plan


PROJECT_ROOT = Path(__file__).resolve().parents[2]
RESULTS_DIR = PROJECT_ROOT / "results"


def parse_date(value: str) -> str:
    try:
        return datetime.strptime(value, "%Y-%m-%d").date().isoformat()
    except ValueError as error:
        raise argparse.ArgumentTypeError("날짜는 YYYY-MM-DD 형식이어야 합니다. 예: 2026-10-10") from error


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="LLM + Kakao Local 기반 국내 여행 추천 프로그램")
    parser.add_argument("-date", "--date", required=True, type=parse_date, help="여행 날짜 (YYYY-MM-DD)")
    parser.add_argument("--refresh", action="store_true", help="같은 날짜의 캐시가 있어도 API를 다시 호출합니다.")
    parser.add_argument("--demo", action="store_true", help="API 키 없이 안전한 데모 데이터를 생성합니다. 실제 API 호출은 하지 않습니다.")
    parser.add_argument(
        "--cities",
        metavar="TEXT",
        help="선호 지역 자유 입력. 예: '강눙, 속초시 그리고 부산 맛집' (오타·별칭 보정, 복수 지역 추출)",
    )
    return parser


def main(argv: list[str] | None = None) -> None:
    args = build_parser().parse_args(argv)
    city_input = parse_city_preferences(args.cities) if args.cities else None
    if city_input is not None and not city_input.cities:
        build_parser().error("--cities에서 인식 가능한 국내 지역을 찾지 못했습니다. 예: 강릉, 속초")
    if city_input is not None:
        print(f"[input] 검색 지역: {', '.join(city_input.cities)}")
        if city_input.corrections:
            print(f"[input] 보정: {', '.join(city_input.corrections)}")
        if city_input.ignored_terms:
            print(f"[input] 지역으로 사용하지 않은 단어: {', '.join(city_input.ignored_terms)}")
    if not args.refresh:
        cached = load_cached_plan(RESULTS_DIR, args.date)
        if cached is not None:
            raw_path, report_path = save_plan(RESULTS_DIR, cached)
            print("[cache] 같은 날짜의 결과를 사용했습니다. 외부 API 호출을 건너뜁니다.")
            print(f"완료! {raw_path} 및 {report_path}를 확인하세요.")
            return

    if args.demo:
        planner = TravelPlanner(OfflineLlmClient(), OfflinePlaceClient())
        print("[demo] 외부 API를 호출하지 않는 안전한 예시 데이터를 사용합니다.")
    else:
        load_dotenv(PROJECT_ROOT / ".env")
        try:
            settings = get_settings()
        except ConfigurationError as error:
            print(f"설정 오류: {error}")
            raise SystemExit(2) from error
        planner = TravelPlanner(
            OpenAIClient(settings.openai_api_key, settings.openai_base_url, settings.openai_model),
            KakaoLocalClient(settings.kakao_rest_api_key),
        )

    def show_progress(step, value) -> None:
        if step == "recommendation":
            print("[1/3] 1차 추천 생성 완료(LLM)")
            print(f"  - recommended_city: {value.recommended_city}")
        elif step == "place_search":
            count = sum(len(places) for places in value.values())
            print("[2/3] 맛집 검색 완료(지도/장소 API)")
            print(f"  - 맛집 {count}곳 검색 완료 (0건이어도 리포트 생성 계속)")
        elif step == "report":
            print("[3/3] 최종 리포트 생성 완료(LLM)")

    try:
        plan = planner.create_plan(
            args.date,
            preferred_cities=city_input.cities if city_input is not None else None,
            progress=show_progress,
        )
    except (ApiRequestError, ValueError) as error:
        print(f"오류: 1차 LLM 추천을 완료하지 못했습니다. {error}")
        raise SystemExit(1) from error
    raw_path, report_path = save_plan(RESULTS_DIR, plan)
    print(f"완료! {raw_path} 및 {report_path}를 확인하세요.")
