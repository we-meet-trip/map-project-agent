"""다른 서비스로 보낼 좌표를 감싸는 쪽 검사.

여는 쪽은 hub(파이썬)와 BFF(자바)다. 형식이 어긋나면 배포한 뒤 좌표가 오가는
모든 길이 한꺼번에 막히는데, 화면에는 사유 없는 실패로만 보인다.
"""
from __future__ import annotations

import base64
import json

import pytest
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from pydantic import SecretStr

from map_project_agent.agent_settings import get_settings
from map_project_agent.crypto import location_seal

KEY_B64 = "dHR0dHR0dHR0dHR0dHR0dHR0dHR0dHR0dHR0dHR0dHQ="
KEY = base64.b64decode(KEY_B64)


@pytest.fixture(autouse=True)
def _wire_key():
    settings = get_settings()
    before = settings.LOCATION_WIRE_KEY
    settings.LOCATION_WIRE_KEY = SecretStr(KEY_B64)
    yield
    settings.LOCATION_WIRE_KEY = before


def _open(token: str) -> dict:
    """받는 쪽이 하는 그대로 연다."""
    _, iv, ct = token.split(".", 2)

    def b64u(text: str) -> bytes:
        return base64.urlsafe_b64decode(text + "=" * (-len(text) % 4))

    return json.loads(AESGCM(KEY).decrypt(b64u(iv), b64u(ct), b"map|loc|v1"))


def test_sealed_value_hides_coordinates():
    token = location_seal.seal({"origin": {"lat": 35.1001, "lng": 129.1001}})

    assert token.startswith("v1.")
    assert "35.1001" not in token and "129.1001" not in token


def test_round_trip_keeps_values():
    token = location_seal.seal({"origin": {"lat": 35.1001, "lng": 129.1001}})

    assert _open(token)["origin"]["lat"] == 35.1001


def test_adds_issue_time():
    # 만든 시각이 없으면 한 번 지나간 봉투가 영원히 유효해서, 주워 둔 것을
    # 나중에 그대로 다시 보낼 수 있다.
    assert "iat" in _open(location_seal.seal({"a": 1}))


def test_never_repeats():
    payload = {"origin": {"lat": 35.1001, "lng": 129.1001}}

    assert location_seal.seal(payload) != location_seal.seal(payload)


def test_url_safe_characters_only():
    # 요청 줄에 그대로 실려야 하는데, 더하기와 빗금은 주소에서 다른 뜻으로 읽힌다.
    token = location_seal.seal({"a": 1})

    assert all(c.isalnum() or c in "._-" for c in token)


def test_missing_key_is_refused():
    """열쇠가 없으면 부팅 확인과 봉하기 모두 거부한다(평문으로 보내는 길은 없다)."""
    settings = get_settings()
    settings.LOCATION_WIRE_KEY = SecretStr("")

    with pytest.raises(location_seal.SealError):
        location_seal.check_key()
    with pytest.raises(location_seal.SealError):
        location_seal.seal({"a": 1})


def test_boot_stops_without_key(monkeypatch):
    """열쇠가 없으면 lifespan 이 첫 요청 전에 멈추고 생성법을 알려 준다."""
    import asyncio

    from map_project_agent import main as agent_main

    settings = get_settings()
    monkeypatch.setattr(settings, "GEMINI_API_KEY", SecretStr("test"))
    settings.LOCATION_WIRE_KEY = SecretStr("")

    async def boot():
        async with agent_main.lifespan(agent_main.app):
            pass

    with pytest.raises(RuntimeError, match="openssl rand -base64 32"):
        asyncio.run(boot())


def test_plaintext_places_are_refused():
    """고른 장소가 봉투 없이 평문으로 오면 받지 않는다."""
    from datetime import date, time

    from fastapi import HTTPException

    from map_project_agent.main import _resolve_places
    from map_project_agent.schemas.agent_schemas import (
        AgentRequest,
        DateRange,
        SelectedPlace,
    )

    req = AgentRequest(
        date=DateRange(
            date_start=date(2026, 7, 6),
            date_end=date(2026, 7, 6),
            time_start=time(9, 0),
            time_end=time(18, 0),
        ),
        province="강원특별자치도",
        city="속초시",
        stage="route",
        places=[SelectedPlace(name="속초해변", lat=38.19, lng=128.60)],
    )

    with pytest.raises(HTTPException) as err:
        _resolve_places(req)
    assert err.value.status_code == 400


def test_published_payload_is_always_sealed():
    """완료 스트림에 싣는 본문은 늘 봉투다."""
    import asyncio
    from types import SimpleNamespace
    from unittest.mock import AsyncMock

    from map_project_agent.clients.agent_clients import StreamsPublisher

    publisher = StreamsPublisher("redis://localhost", 0, "test")
    publisher._client = SimpleNamespace(xadd=AsyncMock(return_value="1-0"))
    raw = '{"status":"done","places":[{"lat":38.19,"lng":128.6}]}'
    asyncio.run(publisher.publish("job", "done", raw, None))

    body = publisher._client.xadd.call_args.args[1]["payload"]
    assert body.startswith("v1.") and "38.19" not in body
    assert _open(body)["payload"] == raw


def test_rules_filter_body_is_always_sealed():
    """hub 반경 필터로 보내는 출발지·후보 좌표는 늘 봉투에 담긴다."""
    import asyncio

    from map_project_agent.clients.agent_clients import HubClient

    sent = {}

    class _Resp:
        def raise_for_status(self):
            return None

        def json(self):
            return {"filtered": [], "radius_m": 0, "dropped": 0}

    class _Client:
        async def post(self, url, json):
            sent["url"], sent["json"] = url, json
            return _Resp()

    hub = HubClient(base_url="http://hub")
    hub._client = _Client()
    asyncio.run(hub.filter_mobility_radius(
        {"lat": 38.19, "lng": 128.6}, "walk", [{"content_id": "c1", "lat": 38.2, "lng": 128.61}]))

    body = sent["json"]
    assert set(body) == {"mobility", "loc"}
    assert _open(body["loc"])["origin"] == {"lat": 38.19, "lng": 128.6}


def test_refuses_short_key():
    settings = get_settings()
    settings.LOCATION_WIRE_KEY = SecretStr(base64.b64encode(b"0" * 24).decode())

    with pytest.raises(location_seal.SealError):
        location_seal.seal({"a": 1})


def test_opened_places_become_schema_objects():
    """봉투에서 꺼낸 장소는 스키마로 세워져야 한다.

    검사 없이 dict 인 채로 넘기면 장소를 읽는 첫 노드가
    "'dict' object has no attribute 'day'" 로 터진다 — 화면에는 사유 없는
    502 로만 보이고, 좌표 범위 검사도 그때는 이미 지나간 뒤다.
    """
    from datetime import date, time

    from map_project_agent.main import _resolve_places
    from map_project_agent.schemas.agent_schemas import (
        AgentRequest,
        DateRange,
        SelectedPlace,
    )

    req = AgentRequest(
        date=DateRange(
            date_start=date(2026, 7, 6),
            date_end=date(2026, 7, 6),
            time_start=time(9, 0),
            time_end=time(18, 0),
        ),
        province="강원특별자치도",
        city="속초시",
        stage="route",
        loc=location_seal.seal({
            "places": [
                {"name": "속초해변", "address": "강원 속초시",
                 "lat": 38.19, "lng": 128.60, "day": 1},
                {"name": "영금정", "address": "강원 속초시",
                 "lat": 38.21, "lng": 128.60, "day": 1},
            ]
        }),
    )

    out = _resolve_places(req)

    assert all(isinstance(p, SelectedPlace) for p in out.places)
    assert out.places[0].day == 1
    assert out.loc is None


def test_opened_places_out_of_range_are_refused():
    """봉투 안이라도 국내 밖 좌표는 받지 않는다."""
    from datetime import date, time

    from fastapi import HTTPException

    from map_project_agent.main import _resolve_places
    from map_project_agent.schemas.agent_schemas import AgentRequest, DateRange

    req = AgentRequest(
        date=DateRange(
            date_start=date(2026, 7, 6),
            date_end=date(2026, 7, 6),
            time_start=time(9, 0),
            time_end=time(18, 0),
        ),
        province="강원특별자치도",
        city="속초시",
        stage="route",
        loc=location_seal.seal({
            "places": [
                {"name": "해외", "address": "", "lat": 10.0, "lng": 127.0,
                 "day": 1},
            ]
        }),
    )

    with pytest.raises(HTTPException) as err:
        _resolve_places(req)
    assert err.value.status_code == 400
