"""합성 LLM 제공자(기본 제공자) 검사.

외부 키·네트워크 없이 추천 그래프가 끝까지 돌아야 하고, 결과에는 합성이라는
표시가 남아야 하며, 같은 입력이면 같은 결과가 나와야 한다.
"""
from __future__ import annotations

import asyncio
from datetime import date, time

import pytest

from map_project_agent.agent_settings import AgentSettings
from map_project_agent.llm.fake_client import (
    PER_DAY,
    SYNTHETIC_MARK,
    FakeLLMClient,
    select_places,
)
from map_project_agent.schemas.agent_schemas import (
    BulletsEnvelope,
    Place,
    PlacesSelection,
    ReasonEnvelope,
)
from map_project_agent.nodes.agent_nodes import _build_reason_prompt, _build_selection_prompt
from map_project_agent.nodes.summary_nodes import (
    build_summary_prompt_from_views,
    summary_place_view,
)
from tests.test_graph_routing import _candidate, _FakeHub, _invoke, _request


def _cands(n: int) -> list[dict]:
    return [_candidate(i) for i in range(n)]


def test_fake_is_the_default_provider() -> None:
    assert AgentSettings(_env_file=None).LLM_PROVIDER == "fake"


def test_selection_takes_candidates_in_rank_order_per_day() -> None:
    req = _request(date=_request().date.model_copy(update={"date_end": date(2026, 7, 7)}))
    _, prompt = _build_selection_prompt(req, {"daily": []}, _cands(10), reviews={})

    out = select_places(prompt)

    assert [s.index for s in out.selections] == list(range(2 * PER_DAY))
    assert [s.day for s in out.selections] == [1] * PER_DAY + [2] * PER_DAY
    assert all(s.recommended_visit_time.startswith(SYNTHETIC_MARK) for s in out.selections)


def test_selection_never_invents_places() -> None:
    _, prompt = _build_selection_prompt(_request(), {"daily": []}, _cands(2), reviews={})

    out = select_places(prompt)

    assert {s.index for s in out.selections} <= {0, 1}


def test_selection_without_candidates_is_empty() -> None:
    assert select_places("no tags here").selections == []


def test_same_prompt_gives_same_result() -> None:
    _, prompt = _build_selection_prompt(_request(), {"daily": []}, _cands(5), reviews={})
    client = FakeLLMClient()

    a = asyncio.run(client.generate_structured(prompt, PlacesSelection))
    b = asyncio.run(client.generate_structured(prompt, PlacesSelection))

    assert a == b


def test_reasons_cover_every_place_and_are_marked() -> None:
    places = [
        Place(place_id=i, day=1, name=f"장소{i}", address="주소", lat=37.5, lng=127.0,
              recommended_visit_time="오전")
        for i in range(3)
    ]
    _, prompt = _build_reason_prompt(_request(), {"daily": []}, places, reviews={})

    out = asyncio.run(FakeLLMClient().generate_structured(prompt, ReasonEnvelope))

    assert [r.place_id for r in out.reasons] == [0, 1, 2]
    assert all(r.reason.startswith(SYNTHETIC_MARK) for r in out.reasons)
    assert out.clothing.startswith(SYNTHETIC_MARK)


def test_summary_bullets_are_marked() -> None:
    views = [summary_place_view(0, "장소0", "카페", [])]
    _, prompt = build_summary_prompt_from_views(views)

    out = asyncio.run(FakeLLMClient().generate_structured(prompt, BulletsEnvelope))

    assert [i.place_id for i in out.items] == [0]
    assert all(b.startswith(SYNTHETIC_MARK) for b in out.items[0].bullets)


def test_unknown_schema_is_a_programming_error() -> None:
    from pydantic import BaseModel

    class Other(BaseModel):
        x: int

    with pytest.raises(TypeError):
        asyncio.run(FakeLLMClient().generate_structured("", Other))


def test_full_graph_runs_with_fake_provider() -> None:
    """외부 모델 없이 초기 추천이 끝까지 돌고, 결과에 합성 표시가 남는다."""
    out, pub = _invoke(_request(), _FakeHub(_cands(6)), FakeLLMClient())

    assert out.get("error") is None
    payload = pub.payloads[-1]
    assert payload["status"] == "done"
    assert payload["places"]
    assert all(p["reason"].startswith(SYNTHETIC_MARK) for p in payload["places"])
    assert payload["clothing"].startswith(SYNTHETIC_MARK)


def test_training_signal_names_the_fake_provider(monkeypatch) -> None:
    """합성 결과로 만든 학습 신호가 실제 모델 이름을 달지 않는다."""
    from map_project_agent.agent_settings import get_settings
    from map_project_agent.nodes.agent_nodes import _training_signal
    import json

    monkeypatch.setattr(get_settings(), "TRAINING_CAPTURE_ENABLED", True)
    monkeypatch.setattr(get_settings(), "LLM_PROVIDER", "fake")
    signal = json.loads(_training_signal({"selection_path": "select", "candidates": []}))

    assert signal["model"] == "fake"


def _stub(i: int) -> dict:
    return {"content_id": f"kakao:stub-{i}", "source": "kakao", "name": f"스텁 장소{i}",
            "address": "주소", "lat": 37.5 + i * 0.001, "lng": 127.0, "category": "음식점 > 카페",
            "category_group_code": "CE7"}


def test_stub_candidates_are_accepted_with_fake_provider(monkeypatch) -> None:
    """hub 시험 모드의 스텁 후보는 합성 제공자일 때만 장소가 된다."""
    from map_project_agent.agent_settings import get_settings
    from map_project_agent.nodes.agent_nodes import _place_from_candidate

    monkeypatch.setattr(get_settings(), "LLM_PROVIDER", "fake")
    p = _place_from_candidate(0, _stub(1), "오전", 1)
    assert p.content_id == "kakao:stub-1"


def test_stub_candidates_are_refused_with_real_provider(monkeypatch) -> None:
    """실제 모델로 돌 때 스텁 후보는 지금처럼 거부한다."""
    from map_project_agent.agent_settings import get_settings
    from map_project_agent.nodes.agent_nodes import _place_from_candidate

    monkeypatch.setattr(get_settings(), "LLM_PROVIDER", "gemini")
    with pytest.raises(ValueError):
        _place_from_candidate(0, _stub(1), "오전", 1)


def test_quick_start_runs_on_hub_stub_candidates(monkeypatch) -> None:
    """빠른 시작 그대로(합성 제공자 + hub 스텁 후보)에서 추천이 끝까지 돈다."""
    from map_project_agent.agent_settings import get_settings

    monkeypatch.setattr(get_settings(), "LLM_PROVIDER", "fake")
    out, pub = _invoke(_request(), _FakeHub([_stub(i) for i in range(4)]), FakeLLMClient())

    payload = pub.payloads[-1]
    assert payload["status"] == "done", payload
    assert {p["content_id"] for p in payload["places"]} <= {f"kakao:stub-{i}" for i in range(4)}
    assert all(p["reason"].startswith(SYNTHETIC_MARK) for p in payload["places"])
