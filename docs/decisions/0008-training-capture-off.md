# 0008. 학습 수집은 기본으로 끈다

## 맥락

추천 결과와 함께 노출 후보·선택·요청 조건을 학습 신호로 남길 수 있다. 사용자 기록이라 동의·보관 조건이 정해지기 전에는 만들지 않는 것이 맞다.

## 선택지

1. 기본 켬
2. 기본 끔, 켜면 Streams 의 training 필드로만

## 결정

두 번째. `MAP_PROJECT_TRAINING_CAPTURE_ENABLED=false` 가 기본이며, 꺼져 있으면 학습 전용 JSON 을 만들지도 발행하지도 않는다. 토큰 사용량 계측(내용 없음)은 유지한다. 신호의 형식 판은 `"1.0.0"` 이다.

## 결과

평가(`eval.run`)는 학습 신호 없이 완료 결과만으로 돈다.

## 관련 커밋

[`d4dad3d`](https://github.com/we-meet-trip/map-project-agent/commit/d4dad3dd9a7fa358111d34fb57115b9af3872665)
