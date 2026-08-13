# Korea Travel Planner · Python 응용 API 활용

> 여행 날짜와 선호 지역을 입력하면 **LLM 추천 → Kakao Local 장소 검색 → Markdown/JSON 리포트 저장**을 차례로 수행하는 국내 여행지 추천 CLI 프로그램입니다.

[![Python](https://img.shields.io/badge/Python-3.10%2B-3776AB?logo=python&logoColor=white)](https://www.python.org/)
![LLM](https://img.shields.io/badge/LLM-Gemini-4285F4?logo=google&logoColor=white)
![Kakao](https://img.shields.io/badge/Places-Kakao%20Local-FFCD00?logo=kakaotalk&logoColor=000000)
![Interface](https://img.shields.io/badge/Interface-CLI-1769AA)

## 프로젝트 한눈에 보기

- 공개 소개 페이지: [manbok2028.github.io/a1-2](https://manbok2028.github.io/a1-2/)
- 저장소: [github.com/manbok2028/a1-2](https://github.com/manbok2028/a1-2)
- 대상 미션: **Python 응용: API 활용 국내 여행지 추천 프로그램 개발**
- 핵심 가치: 여러 API의 결과를 연결하고, 실패·비용·결과 저장까지 고려한 실사용형 CLI 파이프라인을 학습한다.

## 어떤 일을 하나요?

```text
여행 날짜 / 선호 지역 입력
        ↓
[1] Gemini API: 추천 지역·날씨/계절 가이드·행사·추천 이유를 JSON으로 생성
        ↓
[2] Kakao Local API: 각 추천 지역의 맛집·장소를 검색
        ↓
[3] Gemini API: 수집 결과를 읽기 쉬운 Markdown 여행 리포트로 작성
        ↓
results/<날짜>_raw.json + results/<날짜>_travel_plan.md 저장
```

리포트에는 추천 지역, 추천 이유, 여행 시기 참고, 행사/계절 참고, 지역별 맛집·장소, 1일 일정, 오류 요약이 포함됩니다. 원본 JSON도 함께 남겨 후속 처리나 검증에 사용할 수 있습니다.

## 핵심 기능

| 기능 | 설명 |
|---|---|
| LLM 기반 여행지 추천 | 날짜와 선택 지역을 바탕으로 구조화된 JSON 추천을 받습니다. |
| 지역별 장소·맛집 검색 | Kakao Local API에서 상호명, 분류, 주소, 장소 URL, 좌표를 수집합니다. |
| Markdown + JSON 결과 저장 | 사람이 읽는 리포트와 기계가 읽는 원본 데이터를 함께 저장합니다. |
| 데모 모드 | `--demo`로 외부 API 호출 없이 전체 실행 흐름을 검증합니다. |
| 날짜별 캐시 | 같은 날짜의 결과가 있으면 API 재호출을 피합니다. 필요 시 `--refresh`로 갱신합니다. |
| 복수 도시·별칭 보정 | `--cities`에서 복수 지역을 추출하고, 자주 틀리는 지역명을 보정합니다. |
| 오류 복구 | 장소 검색 오류나 0건 결과가 있어도 오류를 기록하고 리포트 생성은 계속합니다. |

## 빠른 시작

### 1. 저장소를 내려받고 설치하기

```powershell
git clone https://github.com/manbok2028/a1-2.git
cd a1-2
python -m pip install --no-deps .
```

### 2. API 키 없이 데모 실행하기

처음에는 아래 명령으로 전체 구조를 안전하게 확인하는 것을 권장합니다. 외부 API를 호출하지 않으며 학습용 예시 데이터로 결과 파일을 만듭니다.

```powershell
python -m travel_planner --date "2026-10-11" --demo --refresh
```

완료 후 아래 두 파일을 확인합니다.

```text
results/2026-10-11_raw.json
results/2026-10-11_travel_plan.md
```

> 데모의 장소명·주소·날씨/행사 정보는 **학습용 예시**입니다. 실제 영업·날씨 정보로 사용하면 안 됩니다.

### 3. 실제 API로 실행하기

프로젝트 루트에서 `.env.example`을 복사하여 `.env`를 만듭니다.

```powershell
Copy-Item .env.example .env
```

`.env` 파일에는 본인이 발급한 실제 키만 넣습니다. 따옴표, 설명 문구, 공백을 넣지 않습니다.

```text
GEMINI_API_KEY=실제_Gemini_API_키
KAKAO_REST_API_KEY=실제_카카오_REST_API_키
```

그 다음 실제 API를 호출합니다.

```powershell
python -m travel_planner --date "2026-10-10" --refresh
```

PowerShell에서 해당 창에만 일시적으로 키를 설정할 수도 있습니다.

```powershell
$env:GEMINI_API_KEY="실제_Gemini_API_키"
$env:KAKAO_REST_API_KEY="실제_카카오_REST_API_키"
python -m travel_planner --date "2026-10-10" --refresh
```

## CLI 사용법

```text
python -m travel_planner --date YYYY-MM-DD [--cities "지역 입력"] [--days 1~14] [--interests "관심사"] [--demo] [--refresh]
```

| 옵션 | 역할 |
|---|---|
| `--date` | 필수. `YYYY-MM-DD` 형식의 여행 날짜입니다. |
| `--cities` | 선택. 선호 지역을 자연어로 입력합니다. 복수 도시와 별칭 보정을 지원합니다. |
| `--days` | 선택. 여행 일수입니다. 1일부터 14일까지 지정하며 기본값은 1일입니다. |
| `--interests` | 선택. 관심사를 쉼표로 입력합니다. 예: `맛집,바다,전시` |
| `--demo` | 외부 API를 호출하지 않는 명시적 오프라인 예시 모드입니다. |
| `--refresh` | 기존 날짜 결과가 있어도 캐시를 무시하고 새로 실행합니다. |

복수 지역 입력 예시입니다.

```powershell
python -m travel_planner --date "2026-10-11" --cities "강릉, 속초 그리고 부산 맛집" --demo --refresh
```

여행 일수와 관심사를 함께 입력하면 LLM이 일정 구성에 반영합니다.

```powershell
python -m travel_planner --date "2026-10-11" --cities "강릉, 속초" --days 2 --interests "맛집,바다,전시" --refresh
```

프로그램은 지역명만 추려 중복 없이 처리하고, 알려진 별칭/오타는 보정합니다. 지역이 아닌 단어는 장소 검색 입력에 섞이지 않도록 분리합니다.

## 결과 파일 구조

| 파일 | 포함 내용 |
|---|---|
| `results/<date>_raw.json` | 추천 JSON, 지역별 장소/맛집 목록, 오류 요약, 요청 지역 |
| `results/<date>_travel_plan.md` | 추천 근거, 여행 시기·행사 참고, 장소/맛집, 1일 일정, 오류 요약 |

예시 리포트는 [results/2026-10-11_travel_plan.md](results/2026-10-11_travel_plan.md)에서 확인할 수 있습니다.

## 오류 처리와 비용 관리

| 상황 | 처리 방식 |
|---|---|
| API 키가 없음 | 실제 요청 전 종료하고 설정 방법을 안내합니다. |
| 날짜 형식 오류 | `argparse`가 사용법과 올바른 날짜 형식을 알려 줍니다. |
| LLM JSON 형식 오류 | 필수 필드를 검증하고 JSON 전용 보정 요청을 **최대 1회** 시도합니다. |
| Kakao 인증/네트워크/쿼터 오류 | `errors`에 기록합니다. 장소 목록은 비어도 최종 리포트는 계속 생성합니다. |
| 장소 검색 결과 0건 | `EMPTY_RESULT`로 기록하고 프로그램을 중단하지 않습니다. |
| 최종 리포트 생성 오류 | 이미 수집한 구조화 데이터를 사용해 대체 Markdown 리포트를 만듭니다. |
| 동일 날짜 재실행 | JSON과 Markdown이 모두 있으면 캐시를 사용해 비용과 시간을 줄입니다. |

## API 키 보안

- 실제 키는 `.env` 또는 운영 환경 변수에만 둡니다.
- `.env`는 `.gitignore`에 포함되어 GitHub에 커밋되지 않습니다.
- README, 코드, 결과 JSON/Markdown, 스크린샷에 실제 키를 적지 않습니다.
- 키 유출이 의심되면 발급 사이트에서 즉시 폐기하고 새 키를 발급합니다.
- 실제 여행 전에는 날씨·행사·영업 정보의 공식 출처를 다시 확인해야 합니다.

## 프로젝트 구조

```text
a1-2/
├─ src/travel_planner/
│  ├─ cli.py               # argparse 입력, 진행 메시지, 캐시 확인
│  ├─ config.py            # .env/환경 변수 로드와 키 검증
│  ├─ clients.py           # Gemini API POST, Kakao Local API GET
│  ├─ input_processing.py  # 지역 입력 추출·별칭 보정
│  ├─ service.py           # 3단계 파이프라인과 오류 복구
│  ├─ models.py            # 추천·장소·오류 데이터 모델
│  ├─ storage.py           # JSON/Markdown 저장과 캐시 로드
│  └─ offline_clients.py   # 외부 API를 호출하지 않는 오프라인 예시 클라이언트
├─ tests/                  # unittest 기반 자동 테스트
├─ results/                # 실행 결과 JSON과 Markdown
├─ docs/                   # API 설계, 평가 안내, GitHub Pages 소개
├─ evidence/               # 실행·검증 로그
├─ .env.example            # 키 이름만 담긴 예시 파일
└─ pyproject.toml          # 패키지와 CLI 진입점 설정
```

## 테스트

```powershell
python -m unittest discover -s tests -v
```

테스트는 날짜 검증, JSON 재시도, 장소 API 오류 처리, 결과 저장/캐시, 복수 지역 추출, 데모 리포트의 날씨·장소 표시를 외부 API 호출 없이 확인합니다.

## 문서와 평가 자료

- [API 설계·보안·오류 처리 정책](docs/api-design-and-security.md)
- [미션 적합성 및 제출 체크리스트](docs/mission-compliance.md)
- [동료 평가 안내서](docs/peer-review-guide.md)
- [동료 평가 2분 설명서](docs/peer-review-briefing.md)
- [실행·검증 명령 로그](evidence/command-logs.md)
- [GitHub Pages 프로젝트 소개](https://manbok2028.github.io/a1-2/)

## 학습 포인트

이 프로젝트는 단순 API 호출 예제가 아니라, 사용자 입력을 검증하고 여러 API 결과를 연결하며, 오류와 비용을 관리하고, 재사용 가능한 결과물을 남기는 과정을 다룹니다. `cli.py`는 입력/출력, `clients.py`는 HTTP 통신, `service.py`는 파이프라인, `storage.py`는 결과와 캐시를 책임지도록 모듈을 분리했습니다.
