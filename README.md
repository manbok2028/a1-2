# Korea Travel Planner · Python 응용 API 활용

![Python](https://img.shields.io/badge/Python-3.10%2B-3776AB?logo=python&logoColor=white)
![OpenAI](https://img.shields.io/badge/LLM-OpenAI_compatible-412991?logo=openai&logoColor=white)
![Kakao](https://img.shields.io/badge/Places-Kakao_Local-FFCD00?logo=kakaotalk&logoColor=000000)
![CLI](https://img.shields.io/badge/UI-CLI-4B8BBE)

사용자가 입력한 여행 날짜를 바탕으로 **LLM(OpenAI 계열 API)** 이 국내 추천 지역·계절성 날씨·행사 후보를 JSON으로 만들고, **Kakao Local API**가 지역별 맛집을 검색한 뒤, LLM이 최종 Markdown 여행 리포트를 생성하는 CLI 프로그램입니다.

> 제출 요약: 필수 기능과 보너스(복수 지역 추천, 날짜별 결과 캐싱)를 구현했습니다. API 키는 코드·README·결과 파일에 포함하지 않습니다.

## 처리 흐름

```text
-date YYYY-MM-DD
       │
       ▼
[1] LLM 1차 추천 JSON ──► recommended_city / weather / events / reason
       │
       ▼
[2] Kakao Local 맛집 검색 ──► 도시별 맛집 목록 (실패·0건이어도 계속)
       │
       ▼
[3] LLM Markdown 리포트 ──► results/<date>_raw.json + <date>_travel_plan.md
```

## 빠른 실행

### 1. 설치

```powershell
git clone https://github.com/manbok2028/a1-2.git
cd a1-2
python -m pip install --no-deps .
```

### 2. API 키 설정

`.env.example`을 복사해 `.env`를 만들고 실제 키를 입력합니다. `.env`는 `.gitignore`에 포함되어 GitHub에 올라가지 않습니다.

```powershell
Copy-Item .env.example .env
```

`.env` 예시입니다. `YOUR_KEY` 부분을 실제 값으로 바꾸되, 키 값 자체는 절대 커밋하거나 공유하지 않습니다.

```text
OPENAI_API_KEY=YOUR_KEY
KAKAO_REST_API_KEY=YOUR_KEY
```

현재 PowerShell 세션에서만 설정하려면 다음처럼 사용합니다.

```powershell
$env:OPENAI_API_KEY="YOUR_KEY"
$env:KAKAO_REST_API_KEY="YOUR_KEY"
```

### 3. 실제 API 실행

```powershell
python -m travel_planner --date "2026-10-10"
```

날짜 형식이 잘못되면 `argparse`가 사용법을 출력하고 종료합니다. API 키가 없으면 프로그램은 API를 호출하지 않고 설정 방법을 안내하며 종료합니다.

### 4. 키 없이 구조 확인하기

`--demo`는 **실제 API를 호출하지 않는 명시적 데모 모드**입니다. 결과 파일 구조·CLI 흐름·캐싱을 안전하게 확인할 때만 사용합니다.

```powershell
python -m travel_planner --date "2026-10-10" --demo --refresh
```

## 결과물

실행하면 `results/` 폴더에 아래 두 파일이 생성됩니다. 개인 API 키와 실제 개인 정보는 저장하지 않습니다.

| 파일 | 포함 내용 |
|---|---|
| `<date>_raw.json` | 1차 추천 JSON, 도시별 맛집 목록, 오류 요약(`errors`) |
| `<date>_travel_plan.md` | 추천 지역·이유·날씨·행사·맛집·1일 일정·오류 요약 |

같은 날짜로 다시 실행하면 기본적으로 캐시된 두 결과 파일을 사용해 외부 API 호출을 건너뜁니다. 새로 호출하려면 `--refresh`를 붙입니다. 이는 보너스 ‘결과 캐싱’ 기능입니다.

## 에러 처리 정책

| 상황 | 동작 |
|---|---|
| API 키 없음 | 즉시 종료하고 환경변수·`.env` 설정 방법 출력 |
| LLM JSON 파싱 실패 | JSON 전용 재요청을 최대 1회 수행 |
| Kakao 인증·네트워크·쿼터 오류 | `errors`에 기록하고 맛집을 `데이터 없음` 처리한 뒤 리포트 생성 계속 |
| 맛집 0건 | 중단하지 않고 `EMPTY_RESULT`를 기록한 뒤 리포트 생성 계속 |
| 최종 LLM 리포트 오류 | 오류를 기록하고 구조화된 데이터로 Markdown 대체 리포트 생성 |

## REST API 학습 포인트

- **GET**: Kakao Local 맛집 검색처럼 URL 쿼리로 조회하는 요청에 사용합니다.
- **POST**: LLM에 프롬프트와 생성 옵션을 JSON 본문으로 보내는 요청에 사용합니다.
- **구조화된 출력**: 1차 LLM 응답은 JSON 스키마를 검사한 뒤 `recommended_city`를 다음 Kakao 검색의 입력으로 연결합니다.
- **보안**: 키를 환경변수·`.env`로 분리하면 코드 공유·키 교체·과금 사고 예방에 유리합니다.

## 테스트

```powershell
python -m pip install --no-deps .
python -m unittest discover -s tests -v
```

테스트는 LLM JSON 재시도, 장소 API 인증 오류 후 리포트 지속, 결과 저장·캐싱, 날짜 검증을 외부 API 호출 없이 확인합니다.

## 문서와 평가 자료

- [미션 적합성 및 체크리스트](docs/mission-compliance.md)
- [API 설계·보안·오류 처리 정책](docs/api-design-and-security.md)
- [동료 평가 안내서](docs/peer-review-guide.md)
- [데모 실행 및 Git 명령 로그](evidence/command-logs.md)

## 프로젝트 구조

```text
src/travel_planner/
├─ cli.py        # argparse CLI, 진행 로그, 캐시 정책
├─ config.py     # .env/환경변수와 키 검증
├─ clients.py    # OpenAI 호환 API POST, Kakao Local GET
├─ service.py    # 3단계 오케스트레이션과 오류 정책
├─ models.py     # 추천·장소·오류 데이터 모델
├─ storage.py    # JSON/Markdown 저장과 캐시 로딩
└─ demo.py       # API 키 없는 명시적 데모 클라이언트
tests/           # 외부 API 없이 실행되는 unittest
results/         # 실행 결과 저장 위치
docs/            # 설계·평가 문서
evidence/        # 텍스트 실행 증빙
```
