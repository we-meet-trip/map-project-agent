# 결정 기록

MADR 형식(맥락·선택지·결정·결과)으로 적는다.

| 번호 | 결정 |
|---|---|
| [0001](0001-grounded-selection.md) | 실측 후보 안에서만 장소를 고른다 |
| [0002](0002-async-jobs-and-streams.md) | 추천은 202 와 job_id 로 받고 결과는 Redis Streams 로 낸다 |
| [0003](0003-summary-pipeline.md) | 블로그 후기 요약을 추천 그래프에서 떼어 낸다 |
| [0004](0004-route-by-computation.md) | 방문 순서와 구간은 모델이 아니라 계산으로 정한다 |
| [0005](0005-location-envelope.md) | 서비스 사이 좌표는 봉투로만 오가고 열쇠는 필수다 |
| [0006](0006-migration-separated.md) | 체크포인트 마이그레이션을 런타임과 다른 계정·과정으로 돌린다 |
| [0007](0007-default-model.md) | 기본 Gemini 모델을 gemini-3.8-flash 로 둔다 |
| [0008](0008-training-capture-off.md) | 학습 수집은 기본으로 끈다 |
| [0009](0009-deterministic-eval.md) | 평가는 LLM 이 아니라 결정적 채점기로 한다 |
| [0010](0010-llm-budget-and-retry.md) | LLM 호출에 요청당 예산과 한도기를 두고 429 는 재시도하지 않는다 |
| [0011](0011-synthetic-llm-default.md) | 기본 LLM 제공자를 결정적 합성 제공자로 둔다 |
| [0012](0012-third-party-content-opt-in.md) | 제3자 본문을 모델로 보내는 기능과 실행 기록 전송은 기본으로 끈다 |
