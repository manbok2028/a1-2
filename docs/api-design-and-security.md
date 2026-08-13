# API 설계·보안·오류 처리 정책

## 요청과 응답 구조

| 단계 | 제공자 | HTTP 방식 | 입력 | 응답 활용 |
|---|---|---|---|---|
| 1차 추천 | Gemini API | POST | 여행 날짜와 JSON 스키마 프롬프트 | `recommended_city`, 날씨, 행사, 이유 |
| 맛집 검색 | Kakao Local | GET | `recommended_city + 맛집` 쿼리 | 이름, 주소, 분류, URL, 좌표 |
| 최종 리포트 | Gemini API | POST | 1차 추천 JSON + 맛집 목록 + errors | Markdown 여행 리포트 |

GET은 이미 있는 정보를 조건으로 조회할 때 URL 쿼리와 함께 사용하고, POST는 LLM처럼 긴 프롬프트와 생성 옵션을 JSON 본문으로 전달할 때 사용합니다.

## 구조화된 LLM 출력과 재시도

1차 추천 프롬프트는 `recommended_city`, `weather`, `events`, `reason`을 필수 키로 하는 JSON 객체만 반환하도록 요구합니다. 프로그램은 문자열을 JSON으로 파싱하고 타입·빈값을 검사합니다. 파싱 또는 스키마 검증에 실패하면 ‘필수 키만 JSON으로 반환’하는 보정 프롬프트로 **최대 1회** 재요청합니다. 무한 재시도는 비용과 지연을 키우므로 허용하지 않습니다.

`recommended_cities`는 선택 보너스 필드입니다. 기본 도시와 최대 3개의 도시를 순서대로 처리해 각 도시별 맛집을 검색합니다.

## 오류 처리 원칙

| 오류 | 감지 방법 | 처리 |
|---|---|---|
| 인증 실패 | HTTP 401/403 | `AUTH_ERROR` 기록, Kakao 단계는 빈 목록으로 계속 |
| 쿼터 초과 | HTTP 429 | `QUOTA_ERROR` 기록, Kakao 단계는 빈 목록으로 계속 |
| 네트워크 오류 | `URLError` | `NETWORK_ERROR` 기록, Kakao 단계는 빈 목록으로 계속 |
| 응답 파싱 오류 | JSON 파싱·스키마 예외 | LLM 추천은 1회 재시도, 그 뒤에는 종료 |
| 검색 0건 | 빈 장소 목록 | `EMPTY_RESULT` 기록, Markdown에 데이터 없음 표기 |

## API 키 보안

키는 `.env` 또는 환경변수에서만 읽습니다. `.env`는 `.gitignore`에 포함되어 있고, `.env.example`에는 빈 변수명만 제공합니다. 이를 지키면 저장소 공유 시 키 노출을 막고, 키를 교체해도 코드를 수정할 필요가 없으며, 과금·쿼터 사고 위험을 줄일 수 있습니다.

## 결과 캐싱 정책

같은 날짜의 원본 JSON과 Markdown 리포트가 모두 있으면 API 호출을 생략합니다. 이 방식은 비용·시간을 줄이는 간단한 캐싱입니다. 날씨·행사 후보를 새로 받고 싶을 때는 `--refresh`를 사용합니다. 캐시 파일이 손상되었거나 둘 중 하나가 없으면 정상 API 흐름을 다시 실행합니다.

## 요청 예시와 플러그형 클라이언트

민감한 실제 키는 아래 예시에 넣지 않습니다.

```text
GET https://dapi.kakao.com/v2/local/search/keyword.json?query=강릉+맛집&size=5
Authorization: KakaoAK ${KAKAO_REST_API_KEY}
```

```json
POST /v1/chat/completions
{
  "contents": [{"role": "user", "parts": [{"text": "날짜와 JSON 스키마를 포함한 추천 프롬프트"}]}],
  "generationConfig": {"responseMimeType": "application/json"}
}
```

`TravelPlanner`는 LLM과 장소 검색 클라이언트를 생성자에서 주입받습니다. 기본 실행은 `GeminiClient`와 `KakaoLocalClient`를 사용하고, `--demo`는 같은 인터페이스의 `OfflineLlmClient`와 `OfflinePlaceClient`를 교체합니다. 기본 모델은 `gemini-3.5-flash`이며, 필요하면 `GEMINI_MODEL` 환경 변수로 바꿀 수 있습니다.

## 사용자 지역 입력 보정

`--cities`는 자유 입력을 받되, LLM에게 위치를 추측시키지 않습니다. `input_processing.py`의 명시적 별칭표로 `강눙 → 강릉`, `제주도 → 제주`, `속초시 → 속초`를 보정하고, 한 문장 안의 여러 지역을 순서대로 추출합니다. 지역 외 단어는 Kakao 검색 쿼리에 전달하지 않습니다. 인식한 지역은 1차 추천 프롬프트의 우선 후보이면서 도시별 맛집 검색 대상이 됩니다.

## 재시도·오류 로그의 계약

스키마 파싱 첫 실패 뒤의 보정 프롬프트는 날짜·사용자 요청 지역을 유지하고, `JSON 객체만 반환`하도록 요구를 짧게 강화합니다. 두 번째 실패는 종료합니다. 장소 API는 자동 재시도하지 않습니다. 동일 요청을 반복해 쿼터를 소모하거나 중복 결과를 만들지 않기 위해서이며, 실패한 도시는 빈 목록과 오류 레코드로 남긴 뒤 리포트는 계속 만듭니다.

오류 레코드 스키마는 **v1**이며 모든 결과 JSON에서 아래 최소 필드를 사용합니다.

```json
{"step": "place_search", "type": "AUTH_ERROR", "message": "HTTP 401"}
```

운영 환경에서는 `.env` 대신 배포 플랫폼의 Secret/환경변수 관리 기능에 `GEMINI_API_KEY`, `KAKAO_REST_API_KEY`를 등록합니다. CI에는 실제 키·실제 API 결과를 넣지 않고 `--demo`와 단위 테스트만 실행합니다.
