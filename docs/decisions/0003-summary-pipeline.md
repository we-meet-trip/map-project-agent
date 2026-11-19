# 0003. 블로그 후기 요약을 추천 그래프에서 떼어 낸다

## 맥락

요약은 장소를 눌렀을 때 필요한 정보인데, 추천 그래프 안에서 만들면 일정 생성 시간과 LLM 예산을 함께 잡아먹었다.

## 선택지

1. 추천 그래프의 노드로 둔다
2. 별도 그래프와 엔드포인트(단건·묶음), 별도 예산으로 둔다

## 결정

두 번째. `/v1/reviews/summary`(한 곳)와 `/batch`(여러 곳을 한 번의 모델 호출로)를 두고, 요청당 호출 예산은 2회로 추천과 분리했다. 일일 한도만 같은 카운터를 쓴다.

## 결과

추천 예산(≤3회)이 요약 때문에 줄지 않는다. 요약은 제3자 본문을 모델로 보내므로 기본 꺼짐이다([0012](0012-third-party-content-opt-in.md)).

## 관련 커밋

[`5875afd`](https://github.com/we-meet-trip/map-project-agent/commit/5875afd89c8fe3503904630e29d89bc8352a3095), [`99a968e`](https://github.com/we-meet-trip/map-project-agent/commit/99a968eacf32579075412d86f1ef8ea8f9e74be2)
