# 실행·검증 로그

## API 키 없는 데모 실행

아래 명령은 실제 OpenAI·Kakao API를 호출하지 않고 결과 파일 구조와 전체 흐름을 검증합니다.

```text
PS> python -m travel_planner --date "2026-10-10" --demo --refresh
[demo] 외부 API를 호출하지 않는 안전한 예시 데이터를 사용합니다.
[1/3] 1차 추천 생성 완료(LLM)
  - recommended_city: 강릉
[2/3] 맛집 검색 완료(지도/장소 API)
  - 맛집 4곳 검색 완료 (0건이어도 리포트 생성 계속)
[3/3] 최종 리포트 생성 완료(LLM)
완료! results/2026-10-10_raw.json 및 results/2026-10-10_travel_plan.md를 확인하세요.
```

## 테스트 실행

```text
PS> python -m unittest discover -s tests -v
Ran 6 tests
OK
```

## 보안 점검

- 실제 API 키는 `.env` 또는 현재 터미널 환경변수에만 둡니다.
- `.env`와 실행 결과 JSON·Markdown은 `.gitignore`로 제외됩니다.
- 제출용 문서·로그에는 키 값 대신 환경변수 이름만 기록합니다.
