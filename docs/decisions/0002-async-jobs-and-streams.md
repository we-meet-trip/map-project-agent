# 0002. 추천은 202 와 job_id 로 받고 결과는 Redis Streams 로 낸다

## 맥락

추천 1건은 hub 왕복 여러 번과 LLM 호출 최대 3회로 수십 초가 걸린다. HTTP 요청을 그동안 붙잡아 두면 BFF 의 연결·타임아웃 관리가 어려워진다.

## 선택지

1. 동기 응답
2. 202 + job_id 를 주고 결과를 조회 API 로 꺼내 가게 한다
3. 202 + job_id 를 주고 결과를 Redis Streams 로 발행한다

## 결정

세 번째. agent 는 결과를 저장하지 않고(stateless) `agent:jobs:done` 에 발행하며, BFF 가 컨슈머 그룹으로 읽는다. 진행 상황은 `agent:jobs:status` 로 낸다.

## 결과

agent 에는 잡 조회 경로가 없다. 발행 DB 번호를 BFF 와 맞춰야 하고(어긋나면 결과가 닿지 않는다), 결과 본문은 좌표 봉투로 감싼다.

## 관련 커밋

[`57ffd16`](https://github.com/we-meet-trip/map-project-agent/commit/57ffd161ac93d970e331e0c1c0b8696558076aca)
