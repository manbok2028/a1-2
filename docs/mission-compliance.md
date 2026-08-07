# Python 응용: API 활용 국내 여행지 추천 프로그램 · 미션 적합성

| 요구사항 | 상태 | 구현 근거 |
|---|---|---|
| `argparse` CLI와 필수 `-date` | 완료 | `cli.py`의 `build_parser()`와 `parse_date()` |
| 날짜 형식 검증 | 완료 | `YYYY-MM-DD` 외 형식은 `ArgumentTypeError` |
| LLM 1차 추천 JSON | 완료 | `service.py`의 `Recommendation.from_dict()` 스키마 검증 |
| Kakao Local 맛집 검색 | 완료 | `clients.py`의 `KakaoLocalClient.search_restaurants()` |
| 장소 최소 필드 | 완료 | `Place(name, address, category, url, x, y)` |
| 최종 Markdown 리포트 | 완료 | LLM 생성과 실패 시 대체 Markdown 생성 |
| API 키 환경변수·`.env` | 완료 | `config.py`, `.env.example`, `.gitignore` |
| LLM JSON 재시도 1회 | 완료 | `_recommend()`의 최대 2회 루프 |
| 장소 API 실패·0건 지속 | 완료 | 오류 기록 후 빈 목록으로 리포트 생성 |
| JSON + Markdown 결과 저장 | 완료 | `storage.py`의 `save_plan()` |
| 보너스: 복수 도시 | 완료 | `recommended_cities` 반복 검색 |
| 보너스: 결과 캐싱 | 완료 | `load_cached_plan()`, `--refresh` |
| 고급 입력 보정·복수 지역 추출 | 완료 | `input_processing.py`, `--cities`, 단위 테스트 |
| 테스트·CI | 완료 | `tests/`, `.github/workflows/quality.yml` |

## 제출 전 확인

1. 실제 API 키를 `.env` 또는 환경변수로 설정한다.
2. `python -m travel_planner --date "YYYY-MM-DD" --refresh`를 실행한다.
3. `results/`에 생성된 JSON과 Markdown 파일을 확인한다.
4. API 키가 결과 파일·README·Git 이력에 포함되지 않았는지 확인한다.
