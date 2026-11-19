# 0012. 제3자 본문을 모델로 보내는 기능과 실행 기록 전송은 기본으로 끈다

## 맥락

후기 보강과 후기 요약은 블로그 본문을 모델 프롬프트에 싣고, LangSmith 추적은 실행 기록을 외부 서비스로 보낸다. 모두 쓰는 사람이 이용조건과 동의를 확인해야 하는 전송이다.

## 선택지

1. 기본 켬
2. 기본 끔(opt-in)

## 결정

두 번째. `AGENT_REVIEWS_ENRICH_ENABLED`·`AGENT_SUMMARY_ENABLED`·`AGENT_LANGSMITH_TRACING` 은 기본 false 다. Gemini 키를 넣어도 설정으로 켜야 본문을 보낸다. LangSmith 는 시작할 때 SDK 이름으로 명시해 넘기므로 바깥 환경에 남은 값이 켜 두지 못한다.

## 결과

기본 결과에는 후기 기반 문장이 없다. 켜려면 [data.md](../data.md) 의 전송 경로를 확인한다.
