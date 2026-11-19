# 0007. 기본 Gemini 모델을 gemini-3.8-flash 로 둔다

## 맥락

처음 쓰던 gemini-2.5-flash 는 제공사가 폐기 일정을 공지한 판이었고, 그 뒤 새로 만든 환경에서는 추천이 통째로 멈출 수 있었다.

## 선택지

1. gemini-2.5-flash 유지
2. 폐기 일정이 없는 판(gemini-3.8-flash)으로 기본값 이동

## 결정

두 번째. 모델 이름은 `MAP_PROJECT_GEMINI_MODEL` 로 바꿀 수 있고, thinking 예산·출력 상한 같은 설정은 모델 특성에 맞춰 조정한다([troubleshooting T-AGENT-01](../troubleshooting.md)).

## 결과

Gemini 제공자를 고를 때만 의미가 있다. 기본 제공자는 합성이다([0011](0011-synthetic-llm-default.md)).

## 관련 커밋

[`b33117e`](https://github.com/we-meet-trip/map-project-agent/commit/b33117e89dde5eda5f237f3bfdc60dfd1b53a95d)
