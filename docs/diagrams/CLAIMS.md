# 다이어그램 근거표

그림의 노드와 엣지마다 한 줄씩 적는다. 교차 검토는 이 표로 한다. 경로는 레포 기준이다. 줄 번호는 `scripts/render_diagrams.sh` 와 별개로 코드가 바뀌면 다시 맞춘다.

## agent-graph — 추천 파이프라인 노드 그래프

| 그림 | 요소(노드/엣지) | 주장 | 근거 file:line | 확인 방법 |
|---|---|---|---|---|
| agent-graph | 노드 `parse_input` | 요청을 검증·정규화한다 | `map_project_agent/graph/agent_graph.py:106`, `map_project_agent/nodes/agent_nodes.py:622` | 코드 읽기 |
| agent-graph | 노드 `fetch_weather` | hub `/v1/weather` 를 부른다 | `map_project_agent/graph/agent_graph.py:107`, `map_project_agent/nodes/agent_nodes.py:774`, `map_project_agent/clients/agent_clients.py:142` | 코드 읽기 |
| agent-graph | 노드 `plan_strategy` | 일차별 전략을 계산으로 세운다(외부 호출 없음) | `map_project_agent/graph/agent_graph.py:108`, `map_project_agent/nodes/agent_nodes.py:858` | 코드 읽기 |
| agent-graph | 노드 `load_given_places` | stage=route 에서 고른 장소의 출처를 hub 검색으로 확인한다 | `map_project_agent/graph/agent_graph.py:109`, `map_project_agent/nodes/agent_nodes.py:687,712` | 코드 읽기 |
| agent-graph | 노드 `search_places` | hub `/v1/places` 를 부른다 | `map_project_agent/graph/agent_graph.py:110`, `map_project_agent/nodes/agent_nodes.py:981`, `map_project_agent/clients/agent_clients.py:177` | 코드 읽기 |
| agent-graph | 노드 `rules_filter` | hub 이동수단 반경 필터(좌표는 봉투로) | `map_project_agent/graph/agent_graph.py:111`, `map_project_agent/nodes/agent_nodes.py:1218`, `map_project_agent/clients/agent_clients.py:214` | 코드 읽기, `tests/test_location_seal.py` 의 반경 필터 봉투 검사 |
| agent-graph | 노드 `score_and_rank` | hub 실내 가점 + 테마 가점 | `map_project_agent/graph/agent_graph.py:112`, `map_project_agent/nodes/agent_nodes.py:1289`, `map_project_agent/clients/agent_clients.py:247` | 코드 읽기 |
| agent-graph | 노드 `recommend_places` | LLM 으로 장소를 고르고, 켜져 있으면 후기로 보강한다 | `map_project_agent/graph/agent_graph.py:113`, `map_project_agent/nodes/agent_nodes.py:1410,1716,1724` | 코드 읽기 |
| agent-graph | 노드 `recommend_route` | 방문 순서·구간을 좌표로 계산한다(모델 호출 없음) | `map_project_agent/graph/agent_graph.py:114,25`, `map_project_agent/nodes/agent_nodes.py:1794` | 코드 읽기, 노드 안에 `call_structured` 없음 |
| agent-graph | 노드 `build_timeline` | hub 체류시간으로 방문 시각을 만든다 | `map_project_agent/graph/agent_graph.py:115`, `map_project_agent/nodes/agent_nodes.py:2139`, `map_project_agent/clients/agent_clients.py:268` | 코드 읽기 |
| agent-graph | 노드 `fit_time_budget` | 하루 시간을 넘기면 결정적으로 줄인다 | `map_project_agent/graph/agent_graph.py:116`, `map_project_agent/nodes/agent_nodes.py:2207` | 코드 읽기 |
| agent-graph | 노드 `llm_reason` | LLM 으로 추천 이유를 만들고 실패하면 생략한다 | `map_project_agent/graph/agent_graph.py:117`, `map_project_agent/nodes/agent_nodes.py:1918,1963` | 코드 읽기 |
| agent-graph | 노드 `build_payload` | 완료 페이로드를 조립한다 | `map_project_agent/graph/agent_graph.py:118`, `map_project_agent/nodes/agent_nodes.py:2407` | 코드 읽기 |
| agent-graph | 노드 `publish_done` | Redis Streams `agent:jobs:done` 에 봉투로 발행한다 | `map_project_agent/graph/agent_graph.py:119`, `map_project_agent/nodes/agent_nodes.py:2554`, `map_project_agent/clients/agent_clients.py:383`, `map_project_agent/agent_settings.py:297` | 코드 읽기 |
| agent-graph | 엣지 START → parse_input | 시작 | `map_project_agent/graph/agent_graph.py:121` | `build_graph().get_graph().edges` |
| agent-graph | 엣지 parse_input → fetch_weather | 오류가 없을 때 | `map_project_agent/graph/agent_graph.py:124` | 같음 |
| agent-graph | 엣지 fetch_weather → plan_strategy "기본" | stage 가 route 가 아닐 때 | `map_project_agent/graph/agent_graph.py:83,132` | 같음 |
| agent-graph | 엣지 fetch_weather → load_given_places "stage=route" | stage=route 일 때 | `map_project_agent/graph/agent_graph.py:88,133` | 같음 |
| agent-graph | 엣지 plan_strategy → search_places | 단순 엣지 | `map_project_agent/graph/agent_graph.py:138` | 같음 |
| agent-graph | 엣지 search_places → rules_filter → score_and_rank → recommend_places | 단순 엣지 3개 | `map_project_agent/graph/agent_graph.py:151,152,153` | 같음 |
| agent-graph | 엣지 recommend_places → recommend_route | 오류가 없을 때 | `map_project_agent/graph/agent_graph.py:156` | 같음 |
| agent-graph | 엣지 load_given_places → recommend_route | 오류가 없을 때 | `map_project_agent/graph/agent_graph.py:142` | 같음 |
| agent-graph | 엣지 recommend_route → build_timeline | 오류가 없을 때 | `map_project_agent/graph/agent_graph.py:166` | 같음 |
| agent-graph | 엣지 build_timeline → fit_time_budget | 단순 엣지 | `map_project_agent/graph/agent_graph.py:173` | 같음 |
| agent-graph | 엣지 fit_time_budget → llm_reason "초기·재탐색" | 오류가 없고 stage 가 route 가 아닐 때 | `map_project_agent/graph/agent_graph.py:92,178` | 같음 |
| agent-graph | 엣지 fit_time_budget → build_payload "stage=route"(파선) | 오류이거나 stage=route 면 설명을 건너뛴다 | `map_project_agent/graph/agent_graph.py:94` | 같음 |
| agent-graph | 엣지 llm_reason → build_payload | 단순 엣지 | `map_project_agent/graph/agent_graph.py:182` | 같음 |
| agent-graph | 엣지 build_payload → publish_done → END | 단순 엣지 | `map_project_agent/graph/agent_graph.py:183,184` | 같음 |
| agent-graph | 점선 5개(parse_input·fetch_weather·load_given_places·recommend_places·recommend_route → build_payload) "오류" | `state["error"]` 가 서면 단축 | `map_project_agent/graph/agent_graph.py:74` | 같음(조건부 엣지 5개) |

## recommend-request — 추천 요청 시퀀스

| 그림 | 요소(노드/엣지) | 주장 | 근거 file:line | 확인 방법 |
|---|---|---|---|---|
| recommend-request | 레인 BFF | 추천을 맡기는 쪽은 user 서비스(BFF)다 | `map_project_agent/agent_settings.py:160` | user 레포 컨슈머와 교차 확인 |
| recommend-request | BFF → agent API `POST /v1/recommend (X-Internal-Token)` | 내부 토큰 헤더로 부른다 | `map_project_agent/main.py:599,606` | `tests/test_output_validation.py` |
| recommend-request | agent API 자기 호출 "토큰 검증 · job_id 발급 · 잡 시작" | 검증 뒤 uuid 를 만들고 백그라운드 태스크로 돌린다 | `map_project_agent/main.py:627,633,634` | 코드 읽기 |
| recommend-request | agent API → BFF `202 Accepted + job_id` | 즉시 202 로 job_id 만 돌려준다 | `map_project_agent/main.py:601,646` | 코드 읽기 |
| recommend-request | LangGraph → Redis `XADD agent:jobs:status (stage)` | 노드마다 진행 이벤트를 발행한다 | `map_project_agent/nodes/agent_nodes.py:606`, `map_project_agent/clients/agent_clients.py:409` | `tests/test_status_events.py` |
| recommend-request | LangGraph → hub `GET /v1/weather` |  | `map_project_agent/clients/agent_clients.py:142` | 코드 읽기 |
| recommend-request | LangGraph → hub `GET /v1/places (테마별)` | 테마마다 따로 부르고 합친다 | `map_project_agent/clients/agent_clients.py:177` | 코드 읽기 |
| recommend-request | LangGraph → hub `POST 반경 필터` | `/v1/rules/filter/mobility-radius`, 좌표는 봉투(`loc`)로 | `map_project_agent/clients/agent_clients.py:214,232` | `tests/test_location_seal.py` |
| recommend-request | LangGraph → hub `POST 실내 가점` | `/v1/rules/score/indoor-bonus` | `map_project_agent/clients/agent_clients.py:247` | 코드 읽기 |
| recommend-request | LangGraph → hub `GET /v1/reviews (후기 보강이 켜졌을 때, 상위 후보만)` | `REVIEWS_ENRICH_ENABLED`(기본 꺼짐)이고 grounded 일 때 | `map_project_agent/nodes/agent_nodes.py:1716`, `map_project_agent/clients/agent_clients.py:203` | 코드 읽기 |
| recommend-request | LangGraph → LLM "장소 선정 (구조화 출력)" | 기본 제공자는 합성(fake), gemini 는 고를 때만 | `map_project_agent/nodes/agent_nodes.py:1724`, `map_project_agent/llm/fake_client.py:76` | `tests/test_fake_llm.py` |
| recommend-request | LangGraph → hub `GET /v1/places (선정 장소 출처 확인)` | 고른 장소를 다시 검색해 실제 출처를 확인한다 | `map_project_agent/nodes/agent_nodes.py:712` | 코드 읽기 |
| recommend-request | LangGraph 자기 호출 "방문 순서·구간 계산 (모델 호출 없음)" |  | `map_project_agent/nodes/agent_nodes.py:1794` | 코드 읽기 |
| recommend-request | LangGraph → hub `POST 체류시간` | `/v1/rules/estimate/dwell` | `map_project_agent/clients/agent_clients.py:268` | 코드 읽기 |
| recommend-request | LangGraph → LLM "추천 이유 (실패 시 생략)" |  | `map_project_agent/nodes/agent_nodes.py:1963` | 코드 읽기 |
| recommend-request | LangGraph → Redis `XADD agent:jobs:done (job_id · status · payload)` | payload 는 늘 봉투 | `map_project_agent/clients/agent_clients.py:383` | `tests/test_location_seal.py` |
| recommend-request | BFF → Redis "컨슈머 그룹으로 결과 읽기" | 결과는 Streams 로만 나간다 | `map_project_agent/agent_settings.py:160`, `eval/collect.py:13` | user 레포 컨슈머와 교차 확인 |
| recommend-request | 레인 Redis Streams "DB2" | 발행 DB 기본값 2 | `map_project_agent/agent_settings.py:295` | 코드 읽기 |
