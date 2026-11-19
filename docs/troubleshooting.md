# 트러블슈팅과 교훈

항목마다 증상 / 원인(근거) / 해결 / 검증 / 교훈 / 관련 커밋 순서로 적는다.

## T-AGENT-01 구조화 응답 JSON 이 중간에 잘려 추천 이유가 빠진다
- **증상**: 단위 테스트는 모두 통과하는데, 실제 모델로 돌리면 추천 이유 단계가 자주 생략된다.
- **원인**: Gemini 2.5 계열은 thinking 토큰이 `max_output_tokens` 를 함께 쓴다. 상한 4096 에서 thinking 이 최대 약 7000 토큰을 써 JSON 이 끊겼다(`map_project_agent/agent_settings.py` 의 `GEMINI_MAX_OUTPUT_TOKENS`·`GEMINI_THINKING_BUDGET` 설명).
- **해결**: thinking 예산을 0 으로 두는 설정(`AGENT_GEMINI_THINKING_BUDGET`)을 만들고 출력 상한을 8192 로 올렸다.
- **검증**: 같은 조건 반복 실행에서 절단 없이 이유·옷차림이 채워졌다.
- **교훈**: 대역으로 도는 단위 테스트는 모델의 출력 길이 특성을 보지 못한다. 출력 상한은 "보이는 답" 이 아니라 모델이 쓰는 토큰 전체 기준으로 잡는다.
- **관련 커밋**: [`4af4405`](https://github.com/we-meet-trip/map-project-agent/commit/4af4405391240e206bb5a1a7d63ff0fdf0b246f8)

## T-AGENT-02 잘린 응답에 교정 재시도를 걸면 같은 자리에서 또 잘린다
- **증상**: 긴 일정에서 형식 오류 → 교정 재시도 → 다시 형식 오류로 호출 예산만 소진된다.
- **원인**: 출력이 상한에 닿아 잘린 경우, 같은 프롬프트로 다시 물어도 같은 지점에서 잘린다.
- **해결**: 종료 사유가 절단이면 재시도하지 않는다. 장소 수에 따라 이유 길이 상한을 줄이고, 이유가 빠진 장소만 다시 묻는다(`map_project_agent/llm/structured_call.py`, `llm_reason`).
- **검증**: `tests/test_structured_call.py`, `tests/test_llm_reason.py`.
- **교훈**: 재시도는 원인이 바뀔 수 있을 때만 의미가 있다. 결정적인 실패에는 입력을 바꿔야 한다.
- **관련 커밋**: [`35b462c`](https://github.com/we-meet-trip/map-project-agent/commit/35b462cf26f57d3a64698bed0680b963272e4c05)

## T-AGENT-03 무료 등급 503 한 번에 잡 전체가 실패한다
- **증상**: 모델 쪽이 붐빌 때 503 "high demand" 로 추천이 통째로 실패한다.
- **원인**: 전송 계층 재시도가 없었다.
- **해결**: SDK 내장 재시도를 켜되 503·500 만 다시 시도하고 429 는 뺐다. 429 를 SDK 가 다시 보내면 자체 호출 한도기의 회계 밖에서 쿼터를 두 번 쓴다. 빈 재시도 코드 목록은 SDK 가 기본값(429 포함)으로 되돌리므로 클라이언트가 None 으로 바꿔 넘긴다. 시도별 30초, 호출 1건 100초로 재시도가 바깥 시간 제한에 잘리지 않게 맞췄다.
- **검증**: `tests/test_gemini_client.py`.
- **교훈**: 재시도와 호출 한도는 같은 자원을 센다. 두 계층이 서로의 회계를 모르게 두면 한도가 이중으로 깎인다.
- **관련 커밋**: [`4af4405`](https://github.com/we-meet-trip/map-project-agent/commit/4af4405391240e206bb5a1a7d63ff0fdf0b246f8)

## T-AGENT-04 카카오 분류 문자열 때문에 실측 추천이 0건이 된다
- **증상**: 실측 후보가 충분한데 선정 결과가 비어 실패한다.
- **원인**: 카카오 분류 `"음식점 > 카페"` 의 `>` 가 장소 스키마의 꺾쇠 금지 검증에 걸려 후보가 전부 건너뛰어졌다.
- **해결**: 분류의 `>` 를 `/` 로 정규화한 뒤 스키마를 세운다.
- **검증**: `tests/test_grounding.py::test_place_from_candidate_normalizes_kakao_category`.
- **교훈**: 인젝션 방어 규칙은 외부 데이터의 정상 표기와 충돌할 수 있다. 막기 전에 정규화할 자리를 먼저 찾는다.
- **관련 커밋**: [`4af4405`](https://github.com/we-meet-trip/map-project-agent/commit/4af4405391240e206bb5a1a7d63ff0fdf0b246f8)

## T-AGENT-05 테마를 여러 개 고르면 후보가 0건이다
- **증상**: 테마 하나는 정상인데 여러 개를 고르면 실패한다.
- **원인**: 테마 코드를 공백으로 이어 한 검색어로 보내, `food photo` 같은 조합은 검색 결과가 없었다.
- **해결**: 테마마다 한국어 검색어로 따로 조회하고 content_id 로 중복을 없앤 뒤 합친다.
- **검증**: `tests/test_grounding.py` 의 다중 테마 병합 검사.
- **교훈**: UI 가 다중 선택을 허용하면 그 조합이 실사용 경로가 된다. 검색 API 의 질의 문법을 확인하지 않고 문자열을 잇지 않는다.
- **관련 커밋**: [`01c09fa`](https://github.com/we-meet-trip/map-project-agent/commit/01c09fa6c8095f41612e62c54feadc60016d187a)

## T-AGENT-06 여러 날 여행인데 하루 분량만 추천된다
- **증상**: 기간과 상관없이 늘 대여섯 곳만 나온다.
- **원인**: 장소에 일차 개념이 없었다.
- **해결**: 장소에 `day` 를 두고, 하루 2~4곳을 일차별로 배정하게 하고, 일차 범위와 방문 순서를 서버에서 검증한다. 이후 일차별 전략과 시간축을 계산으로 세우게 바꿨다.
- **검증**: `tests/test_timeline.py`, `tests/test_graph_routing.py`.
- **교훈**: 기간처럼 결과의 크기를 정하는 입력은 프롬프트에만 맡기지 말고 스키마와 검증으로 강제한다.
- **관련 커밋**: [`38cef02`](https://github.com/we-meet-trip/map-project-agent/commit/38cef026d332711d2b1e99d6fb7f32f2136141f2), [`8088776`](https://github.com/we-meet-trip/map-project-agent/commit/8088776dfe0b626ca4abaea1e3397ff206e24597)

## T-AGENT-07 선정 프롬프트가 지나치게 커진다
- **증상**: 테마를 많이 고르면 선정 프롬프트가 수만 자로 불어난다.
- **원인**: 테마별 후보 전량이 실렸고, 직렬화 옵션이 프롬프트마다 달랐으며, 모델이 채울 수 없는 필드까지 응답 스키마로 넘겼다.
- **해결**: 후보 상한 max(40, 일수 × 12) 와 실내·실외 절반씩 층화 절단, 프롬프트 JSON 직렬화 일원화(빈 값 제거), 응답 스키마 축소.
- **검증**: `tests/test_candidate_cap.py`, `tests/test_schema_payload_size.py`, `tests/test_prompt_json.py`.
- **교훈**: 응답 스키마의 설명 문자열도 매 호출 입력에 실린다. 스키마는 모델이 실제로 채울 필드만 둔다.
- **관련 커밋**: [`258578a`](https://github.com/we-meet-trip/map-project-agent/commit/258578ad84c9af61156f388fec97a80fecfd23b3), [`e8ebad9`](https://github.com/we-meet-trip/map-project-agent/commit/e8ebad9fa7e92ef807c526097d7aaac89eedb196), [`1a8a652`](https://github.com/we-meet-trip/map-project-agent/commit/1a8a652781039b70c28ea19324f9dbfaf89f55b2)

## T-AGENT-08 데이터베이스가 한 번 재기동하면 추천이 연달아 실패한다
- **증상**: DB 재기동 직후 추천이 몇 건 연속 사유 없이 실패하다가 저절로 멎는다. 헬스체크는 계속 정상이다.
- **원인**: 연결 풀이 이미 끊긴 연결을 그대로 빌려줬다. 첫 질의가 실패해야 끊긴 것을 알게 되고, 그래프의 첫 동작이 체크포인트 읽기라 노드는 하나도 돌지 않았다.
- **해결**: 빌려줄 때 연결 상태를 확인한다(`AsyncConnectionPool.check_connection`, `map_project_agent/main.py`). 대여마다 왕복이 한 번 늘지만 추천 1건에 몇 번만 쓴다.
- **검증**: 연결을 모두 강제로 끊은 직후 연속 요청이 모두 정상이었다(고치기 전에는 모두 실패).
- **교훈**: 프로세스 생존만 보는 헬스체크는 저장소 단절을 못 잡는다. 저장소까지 묻는 준비 확인(`/health/ready`)을 따로 둔다.
- **관련 커밋**: [`c85d7a7`](https://github.com/we-meet-trip/map-project-agent/commit/c85d7a7aa1bd49f756137f6f3436c3c7580a236d)

## T-AGENT-09 고른 장소로 동선을 만들면 502 가 난다
- **증상**: 모델이 필요 없는 동선 전용 요청이 `'dict' object has no attribute 'day'` 로 실패한다.
- **원인**: 좌표 봉투를 연 값(바깥 입력)을 요청에 다시 넣을 때 검증을 건너뛰는 복사를 써서, 장소가 스키마 객체가 아닌 dict 인 채로 그래프까지 갔다. 좌표 범위·목록 상한 검증도 우회됐다.
- **해결**: 봉투를 연 뒤 요청 전체를 스키마로 다시 세우고, 실패하면 400 `invalid location` 을 준다(`map_project_agent/main.py` 의 `_resolve_places`).
- **검증**: `tests/test_location_seal.py::test_opened_places_become_schema_objects`, `::test_opened_places_out_of_range_are_refused`, `tests/test_quality_policy.py::test_sealed_places_revalidate_outer_count`.
- **교훈**: 복호화는 신뢰를 만들지 않는다. 봉투 안의 값도 바깥 입력과 같은 검증을 다시 받는다.
- **관련 커밋**: [`5228e46`](https://github.com/we-meet-trip/map-project-agent/commit/5228e46e2168d8be086ef0f297523ee27f282c72)

## T-AGENT-10 서비스 사이 좌표와 대화 상태가 평문으로 남는다
- **증상**: 요청 본문·스트림·체크포인트 테이블에 사용자가 다닐 곳의 좌표와 이름이 그대로 보인다.
- **원인**: 컨테이너 사이 통신이라 감싸지 않았고, 체크포인터는 그래프 상태를 그대로 저장했다.
- **해결**: 서비스 사이 좌표를 AES-GCM 봉투로 감싸고(만든 시각 포함, 300초 지나면 열지 않음), 체크포인트는 kid 로 열쇠를 돌릴 수 있는 봉인으로 저장 전에 감싼다. 이후 열쇠를 필수로 하고 평문 경로를 없앴다.
- **검증**: `tests/test_location_seal.py`, `tests/test_checkpoint_seal.py`.
- **교훈**: 한 경로를 감싸면 감싸지 않은 다른 경로가 남는다. 좌표가 지나가는 자리(요청·응답·스트림·저장소)를 목록으로 만들어 하나씩 지운다.
- **관련 커밋**: [`5e80dcf`](https://github.com/we-meet-trip/map-project-agent/commit/5e80dcfadc6d0ac638a3ccb15512e7876fa5c40b), [`298d06c`](https://github.com/we-meet-trip/map-project-agent/commit/298d06cc12b914417af9c96c7ba0b3b55f8345ca), [`ca65896`](https://github.com/we-meet-trip/map-project-agent/commit/ca65896107df2f30f96008705963208c8613d938), [`34d3dfc`](https://github.com/we-meet-trip/map-project-agent/commit/34d3dfc7cce162aee62899e4e20c54360a320be8)

## T-AGENT-11 런타임 권한을 줄이면 기동이 실패한다
- **증상**: 런타임 계정에서 DDL 권한을 빼자 부팅 시 체크포인터 준비가 실패한다.
- **원인**: 런타임이 기동할 때 SDK 의 `setup()`(테이블·인덱스 생성)을 불렀다.
- **해결**: 마이그레이션을 별도 모듈(`python -m map_project_agent.checkpoint_migrate`, 전용 계정)로 떼고, 런타임은 SELECT 만으로 판·테이블·인덱스·권한을 검사한다. 실패 진단은 안전한 오류 분류만 남긴다.
- **검증**: `tests/test_checkpoint_database_contract.py`.
- **교훈**: 스키마를 바꾸는 권한과 데이터를 읽고 쓰는 권한은 다른 계정으로 나눈다. 그래야 런타임 계정이 새어도 스키마는 그대로다.
- **관련 커밋**: [`27918f8`](https://github.com/we-meet-trip/map-project-agent/commit/27918f87cfe6b6c9a97cea3548d260126569fdee), [`640024d`](https://github.com/we-meet-trip/map-project-agent/commit/640024d4a977be418b92b59eb37e149fafa52456)

## T-AGENT-12 날씨 결측이 강수 확률 0% 로 보인다
- **증상**: 예보가 없는 날이 "비 올 확률 0%" 로 안내된다.
- **원인**: 결측과 0 을 구분하지 않았다.
- **해결**: 결측 날짜를 따로 들고 가며 경고로 알리고, 실내 가점에 쓰는 일별 최대 강수 확률은 0~100 의 숫자 값만으로 계산한다(결측·비정상 값은 빼고, 모두 없으면 값 없음).
- **검증**: `tests/test_forecast_missing_contract.py`, `tests/test_weather_degrade.py`.
- **교훈**: "값 없음" 과 "값이 0" 은 사용자에게 정반대의 뜻이 된다.
- **관련 커밋**: [`e8684ce`](https://github.com/we-meet-trip/map-project-agent/commit/e8684ceb929f0f336d184215551e1fa566551454)

## T-AGENT-13 시간 예산을 줄일 때 사용자가 남긴 장소가 사라진다
- **증상**: 재탐색에서 "그대로 두라" 고 한 장소가 하루 시간 초과를 줄이는 과정에서 빠진다.
- **원인**: 줄이는 규칙이 고정 장소를 구분하지 않았다.
- **해결**: 고정 장소는 줄이는 대상에서 빼고, 그래도 넘치면 성공으로 내보내지 않는다.
- **검증**: `tests/test_reexplore_keep.py`, `tests/test_timeline.py`.
- **교훈**: 사용자가 명시한 선택은 자동 조정보다 우선한다. 지킬 수 없으면 몰래 바꾸지 말고 실패로 알린다.
- **관련 커밋**: [`98d57fa`](https://github.com/we-meet-trip/map-project-agent/commit/98d57face588e5a5b1c5660c8856acb09cad448e)

## T-AGENT-14 `REDIS_URL` 에 DB 번호를 붙이면 결과가 BFF 에 닿지 않는다
- **증상**: 발행은 성공하는데 BFF 가 결과를 영원히 받지 못한다.
- **원인**: redis-py 는 URL 경로의 DB 번호(`redis://host:6379/0`)를 따로 준 `db` 인자보다 우선한다. 그래서 `MAP_PROJECT_REDIS_DB_STREAMS=2` 가 무시되고 DB0 에 발행됐다.
- **해결**: `MAP_PROJECT_REDIS_URL` 에는 DB 번호를 붙이지 않고, DB 는 `MAP_PROJECT_REDIS_DB_STREAMS`·`MAP_PROJECT_REDIS_DB_RATELIMIT` 로만 정한다(`.env.example`).
- **검증**: `redis.asyncio.from_url("redis://h:6379/0", db=2)` 의 연결 설정이 db 0 이 되는 것을 확인했다(redis-py 7.4).
- **교훈**: 같은 값을 두 곳에서 정할 수 있으면 우선순위를 문서에 적거나 한 곳만 허용한다.
- **관련 커밋**: 없음(설정 주의)

## T-AGENT-15 재배포할 때 진행 중이던 추천이 실패 통지 없이 끊긴다
- **증상**: 배포 뒤 기다리던 요청이 시간 초과까지 매달린다.
- **원인**: agent 는 종료 때 진행 중 잡을 `AGENT_SHUTDOWN_GRACE_SECONDS`(310초)까지 기다렸다가 못 끝낸 잡을 취소하고 실패를 알리는데, 컨테이너의 기본 종료 유예(10초)에 먼저 끊겼다.
- **해결**: 컨테이너 종료 유예를 agent 의 대기 시간보다 길게 둔다(compose `stop_grace_period`). 진행 중 잡이 없으면 곧바로 끝나므로 평소 배포 시간은 같다.
- **검증**: map-project-infra 의 compose 는 agent 에 `stop_grace_period: 320s` 를 둔다. 취소된 잡은 `upstream_unavailable`(retryable) 실패를 발행한다(`map_project_agent/main.py` 의 `_run_job`).
- **교훈**: 앱의 종료 절차는 그것을 감싸는 런타임의 유예 시간 안에서만 의미가 있다.
- **관련 커밋**: 없음(배포 설정)
