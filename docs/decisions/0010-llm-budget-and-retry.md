# 0010. LLM 호출에 요청당 예산과 한도기를 두고 429 는 재시도하지 않는다

## 맥락

무료 등급은 분당·일일 한도가 낮고 503 이 잦다. 재시도와 교정 재시도가 겹치면 한도가 예상보다 빨리 닳는다.

## 선택지

1. 제한 없이 재시도
2. 요청당 예산(≤3) + Redis 한도기(RPM·일일) + 전송 재시도는 503·500 만

## 결정

두 번째. 모든 호출이 `call_structured` 를 지나며 예산을 소비하고, 한도기는 Lua 한 번으로 분당·일일 두 축을 원자적으로 센다. 429 는 SDK 재시도에서 빼고, 잘린 응답에는 교정 재시도를 걸지 않는다.

## 결과

한도에 걸리면 `quota_exceeded` 로 바로 실패한다. 합성 제공자는 한도기를 쓰지 않는다.

## 관련 커밋

[`4af4405`](https://github.com/we-meet-trip/map-project-agent/commit/4af4405391240e206bb5a1a7d63ff0fdf0b246f8), [`35b462c`](https://github.com/we-meet-trip/map-project-agent/commit/35b462cf26f57d3a64698bed0680b963272e4c05)
