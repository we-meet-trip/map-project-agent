"""AgentSettings 환경 변수 배선 단위 테스트.

.env.example 에 문서화된 변수명이 실제 Settings 필드로 로드되는지
(과거 GEMINI_RPM_LIMIT 등이 extra="ignore" 로 조용히 무시되던 결함의
회귀 방지)와 기본값을 검증한다. `_env_file=None` 으로 작업 디렉토리의
.env 간섭을 차단한다.
"""
from __future__ import annotations

from map_project_agent.agent_settings import AgentSettings


def test_defaults() -> None:
    """환경 변수 미주입 시 기본값 — 문서화한 기본값과 일치해야 한다."""
    s = AgentSettings(_env_file=None)
    assert s.GEMINI_RPM_LIMIT == 10
    assert s.GEMINI_RPD_LIMIT == 250
    assert s.GEMINI_RPD_CAP == 200
    # 장소 선정 1 + 동선 1 + 추천이유 1. 블로그 요약은 추천 파이프라인에서
    # 빠져 자기 예산(SUMMARY_MAX_LLM_CALLS)으로 돈다.
    assert s.GEMINI_MAX_CALLS_PER_REQUEST == 3
    assert s.GEMINI_TEMPERATURE == 0.2
    assert s.GEMINI_MAX_OUTPUT_TOKENS == 8192
    assert s.GEMINI_THINKING_BUDGET == 0
    assert s.GEMINI_RETRY_ATTEMPTS == 3
    assert s.GEMINI_RETRY_INITIAL_DELAY == 1.0
    assert s.GEMINI_RETRY_MAX_DELAY == 8.0
    assert s.GEMINI_RETRY_STATUS_CODES == "503,500"
    assert s.GEMINI_HTTP_TIMEOUT_SECONDS == 30.0
    assert s.GEMINI_TIMEOUT_SECONDS == 100.0
    assert s.REDIS_DB_STREAMS == 2
    assert s.REDIS_DB_RATELIMIT == 3
    assert s.STATUS_STREAM_NAME == "agent:jobs:status"
    assert s.STATUS_STREAM_MAXLEN == 2000
    assert s.CHECKPOINT_ENABLED is True
    assert s.CHECKPOINT_ENC_KEYS.get_secret_value() == ""
    assert s.CHECKPOINT_ENC_ACTIVE_KID == ""
    assert s.LANGGRAPH_SCHEMA == "langgraph"
    assert s.JOB_TIMEOUT_SECONDS == 300.0
    assert s.SHUTDOWN_GRACE_SECONDS == 310.0
    assert s.HUB_TIMEOUT_SECONDS == 5.0
    assert s.AUTH_ENFORCED is False
    assert s.REVIEWS_ENRICH_ENABLED is False
    assert s.REVIEWS_MAX_PLACES == 3
    assert s.REVIEWS_DISPLAY == 5
    assert s.REVIEWS_FETCH_CAP_PER_JOB == 10
    assert s.SUMMARY_ENABLED is False
    # 추천 장소 상한(7곳)과 같아야 뒷순번 장소도 요약을 받는다.
    assert s.SUMMARY_MAX_PLACES == 7
    # 본 호출 1 + 형식 이탈 시 교정 재시도 1.
    assert s.SUMMARY_MAX_LLM_CALLS == 2
    assert s.RULES_ENABLED is True
    assert s.LOG_LEVEL == "INFO"


def test_env_injection(monkeypatch) -> None:
    """환경 변수 주입 시 각 필드가 실제로 로드되는지 확인."""
    monkeypatch.setenv("AGENT_GEMINI_RPM_LIMIT", "5")
    monkeypatch.setenv("MAP_PROJECT_GEMINI_RPD_CAP", "100")
    monkeypatch.setenv("AGENT_GEMINI_MAX_CALLS_PER_REQUEST", "2")
    monkeypatch.setenv("AGENT_GEMINI_TEMPERATURE", "0.0")
    monkeypatch.setenv("AGENT_GEMINI_MAX_OUTPUT_TOKENS", "1024")
    monkeypatch.setenv("MAP_PROJECT_REDIS_DB_RATELIMIT", "5")
    monkeypatch.setenv("AGENT_STATUS_STREAM_NAME", "agent:jobs:status-test")
    monkeypatch.setenv("AGENT_CHECKPOINT_ENABLED", "false")
    monkeypatch.setenv("AGENT_DATABASE_PASSWORD", "pw-test")
    monkeypatch.setenv("AGENT_JOB_TIMEOUT_SECONDS", "120")
    monkeypatch.setenv("AGENT_AUTH_ENFORCED", "true")
    monkeypatch.setenv("AGENT_REVIEWS_ENRICH_ENABLED", "false")
    monkeypatch.setenv("AGENT_REVIEWS_MAX_PLACES", "5")
    monkeypatch.setenv("AGENT_RULES_ENABLED", "false")
    s = AgentSettings(_env_file=None)
    assert s.GEMINI_RPM_LIMIT == 5
    assert s.GEMINI_RPD_CAP == 100
    assert s.GEMINI_MAX_CALLS_PER_REQUEST == 2
    assert s.GEMINI_TEMPERATURE == 0.0
    assert s.GEMINI_MAX_OUTPUT_TOKENS == 1024
    assert s.REDIS_DB_RATELIMIT == 5
    assert s.STATUS_STREAM_NAME == "agent:jobs:status-test"
    assert s.CHECKPOINT_ENABLED is False
    assert s.POSTGRES_PASSWORD.get_secret_value() == "pw-test"
    assert s.JOB_TIMEOUT_SECONDS == 120.0
    assert s.AUTH_ENFORCED is True
    assert s.REVIEWS_ENRICH_ENABLED is False
    assert s.REVIEWS_MAX_PLACES == 5
    assert s.RULES_ENABLED is False


def test_old_unprefixed_names_are_ignored(monkeypatch) -> None:
    """접두 없는 옛 이름은 읽지 않는다 — 새 이름만 설정이 된다."""
    monkeypatch.setenv("STATUS_STREAM_NAME", "old-name")
    monkeypatch.setenv("POSTGRES_USER", "operator")
    s = AgentSettings(_env_file=None)
    assert s.STATUS_STREAM_NAME == "agent:jobs:status"
    assert s.POSTGRES_USER == "map_agent_runtime"


def test_shared_values_use_the_common_prefix(monkeypatch) -> None:
    """다른 서비스와 같이 읽는 값은 MAP_PROJECT_ 접두, DB 로그인은 AGENT_DATABASE_*."""
    monkeypatch.setenv("MAP_PROJECT_LOCATION_WIRE_KEY", "k")
    monkeypatch.setenv("MAP_PROJECT_HUB_BASE_URL", "http://hub.test")
    monkeypatch.setenv("AGENT_DATABASE_USER", "runtime-test")
    monkeypatch.setenv("AGENT_LLM_PROVIDER", "gemini")
    s = AgentSettings(_env_file=None)
    assert s.LOCATION_WIRE_KEY.get_secret_value() == "k"
    assert s.HUB_BASE_URL == "http://hub.test"
    assert s.POSTGRES_USER == "runtime-test"
    assert s.LLM_PROVIDER == "gemini"


def test_langsmith_is_passed_to_sdk_names_and_off_by_default(monkeypatch) -> None:
    """SDK 가 읽는 LANGSMITH_* 는 AGENT_LANGSMITH_* 에서 온다. 기본은 꺼짐."""
    from map_project_agent.main import _export_langsmith_env

    # 끝나면 네 이름을 원래 상태로 되돌리도록 먼저 기록해 둔다.
    for name in ("LANGSMITH_API_KEY", "LANGSMITH_PROJECT", "LANGSMITH_ENDPOINT"):
        monkeypatch.delenv(name, raising=False)
    monkeypatch.setenv("LANGSMITH_TRACING", "true")  # 바깥에 남은 값
    _export_langsmith_env(AgentSettings(_env_file=None))
    import os
    assert os.environ["LANGSMITH_TRACING"] == "false"

    monkeypatch.setenv("AGENT_LANGSMITH_TRACING", "true")
    monkeypatch.setenv("AGENT_LANGSMITH_PROJECT", "my-project")
    _export_langsmith_env(AgentSettings(_env_file=None))
    assert os.environ["LANGSMITH_TRACING"] == "true"
    assert os.environ["LANGSMITH_PROJECT"] == "my-project"
