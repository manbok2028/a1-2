# 동료 평가 설명서 · 국내 여행지 추천 프로그램 (약 2분)

## 동료 평가자에게 말할 내용

안녕하세요. 저는 사용자가 여행 날짜와 원하는 지역을 입력하면, 국내 여행지·맛집·여행 계획을 정리해 주는 **국내 여행지 추천 CLI 프로그램**을 만들었습니다. 이 과제의 핵심은 단순히 API를 한 번 호출하는 것이 아니라, Python 프로그램이 여러 API의 결과를 연결하고 실패 상황까지 관리하는 흐름을 구현하는 것이었습니다.

프로그램은 세 단계로 동작합니다. 먼저 Gemini API에 여행 날짜와 사용자의 지역 선호를 보내 추천 도시, 날씨 고려 사항, 행사와 추천 이유를 구조화된 JSON으로 받습니다. 다음으로 그 추천 도시를 Kakao Local API에 전달해 실제 장소·맛집을 검색합니다. 마지막으로 수집한 정보를 다시 Gemini API에 보내 사람이 읽기 쉬운 Markdown 여행 계획으로 만들고, 원본 JSON과 Markdown을 `results/` 폴더에 저장합니다.

사용 방법은 `python -m travel_planner --date "2026-10-10"`처럼 날짜를 넣는 것입니다. 여러 지역을 원하면 `--cities` 옵션을 사용할 수 있습니다. 예를 들어 “강눙, 속초시 그리고 부산 맛집”처럼 입력해도 지역명 오타를 보정하고, 지역이 아닌 단어는 검색어에서 분리해 처리하도록 만들었습니다. 이것이 보너스 기능인 복수 지역 추천과 고급 입력 처리입니다.

또 하나의 보너스 기능은 날짜별 캐시입니다. 이미 같은 날짜의 JSON과 Markdown 결과가 있으면 API를 다시 호출하지 않아 비용과 시간을 줄입니다. 최신 결과가 필요할 때만 `--refresh`를 붙여 새로 호출합니다. 키가 없거나 과금 없이 구조를 확인하고 싶을 때는 `--demo` 모드로 실행할 수 있으며, 이 모드는 실제 외부 API를 호출하지 않습니다.

안정성도 고려했습니다. 날짜 형식, 필수 API 키, LLM JSON 형식을 검사하고, JSON 형식이 맞지 않으면 한 번만 재시도합니다. Kakao API 오류나 맛집 검색 결과가 0건이어도 프로그램 전체를 중단하지 않고 오류 내용을 JSON에 남긴 뒤 여행 리포트를 계속 생성합니다. API 키는 코드에 넣지 않고 `.env`와 환경 변수로만 관리합니다.

코드는 역할별로 나눴습니다. `cli.py`는 사용자 입력과 진행 메시지, `clients.py`는 HTTP API 호출, `service.py`는 세 단계 흐름, `storage.py`는 JSON·Markdown 저장과 캐시, `input_processing.py`는 지역명 보정과 추출을 맡습니다. 단위 테스트로 날짜 검증, API 오류 처리, 리포트 생성, 캐시, 복수 지역 처리까지 확인했습니다. 이 프로젝트를 통해 API 호출 자체보다 입력 검증, 결과 저장, 오류 대응, 비용 관리가 실제 프로그램 품질에 중요하다는 점을 배웠습니다. 감사합니다.

## 평가자가 직접 확인할 순서

1. 저장소를 내려받고 `python -m pip install --no-deps .`를 실행한다.
2. 키 없이 안전하게 확인하려면 아래 명령을 실행한다.

   ```powershell
   python -m travel_planner --date "2026-10-10" --cities "강눙, 속초시 그리고 부산 맛집" --demo --refresh
   ```

3. 콘솔의 3단계 진행 메시지와 `results/`의 JSON·Markdown 파일을 확인한다.
4. 같은 날짜로 다시 실행해 캐시 사용 안내를 확인하고, `--refresh`로 재생성을 비교한다.
5. `python -m unittest discover -s tests -v`로 단위 테스트를 실행한다.

## 확인 링크

- GitHub: https://github.com/manbok2028/a1-2
- API·보안 설계: [docs/api-design-and-security.md](api-design-and-security.md)
- 미션 적합성: [docs/mission-compliance.md](mission-compliance.md)
- 명령 실행 증빙: [evidence/command-logs.md](../evidence/command-logs.md)
