"""hub 룰 엔드포인트의 항목 수 상한을 보내는 쪽(agent)이 지키는지 검사.

hub 는 반경 필터·실내 가점·체류시간 요청을 한 번에 100개까지만 받는다. 테마를
여럿 고르면 후보가 그보다 많아지는데, 그대로 보내면 hub 가 거절하고 룰이
조용히 빠진다. 나눠 보내고 합친 결과가 한 번에 보낸 것과 같아야 한다.
"""
from __future__ import annotations

import asyncio

from map_project_agent.clients.agent_clients import HUB_RULES_MAX_ITEMS, HubClient
from map_project_agent.crypto import location_seal


class _Resp:
    def __init__(self, body: dict) -> None:
        self._body = body

    def raise_for_status(self) -> None:
        return None

    def json(self) -> dict:
        return self._body


class _FakeHubHttp:
    """hub 룰을 흉내 낸다: 상한을 넘으면 실패하고, 항목마다 따로 판정한다."""

    def __init__(self) -> None:
        self.sizes: list[tuple[str, int]] = []

    async def post(self, url: str, json: dict) -> _Resp:
        if url.endswith("/mobility-radius"):
            items = location_seal.open_seal(json["loc"])["candidates"]
            self._check(url, items)
            kept = [c for c in items if c["keep"]]
            return _Resp({"filtered": kept, "radius_m": 3000, "dropped": len(items) - len(kept)})
        if url.endswith("/indoor-bonus"):
            items = json["pois"]
            self._check(url, items)
            return _Resp({"scored": [{"content_id": p["content_id"], "score": p["base_score"]} for p in items]})
        items = json["places"]
        self._check(url, items)
        return _Resp({"estimates": [{"content_id": p["content_id"], "stay_minutes": 30} for p in items]})

    def _check(self, url: str, items: list) -> None:
        assert len(items) <= HUB_RULES_MAX_ITEMS, f"{url} got {len(items)} items"
        self.sizes.append((url.rsplit("/", 1)[-1], len(items)))


def _hub() -> tuple[HubClient, _FakeHubHttp]:
    hub = HubClient(base_url="http://hub")
    fake = _FakeHubHttp()
    hub._client = fake
    return hub, fake


def test_limit_matches_hub() -> None:
    assert HUB_RULES_MAX_ITEMS == 100


def test_radius_filter_is_split_and_merged() -> None:
    hub, fake = _hub()
    cands = [{"content_id": f"c{i}", "lat": 37.5, "lng": 127.0, "keep": i % 3 != 0} for i in range(120)]

    out = asyncio.run(hub.filter_mobility_radius({"lat": 37.5, "lng": 127.0}, "car", cands))

    assert [n for _, n in fake.sizes] == [100, 20]
    assert [c["content_id"] for c in out["filtered"]] == [c["content_id"] for c in cands if c["keep"]]
    assert out["dropped"] == 40 and out["radius_m"] == 3000


def test_indoor_bonus_is_split_and_merged() -> None:
    hub, fake = _hub()
    pois = [{"content_id": f"c{i}", "indoor_flag": False, "base_score": 1.0 - 0.01 * i} for i in range(120)]

    out = asyncio.run(hub.score_indoor_bonus(pois, 30))

    assert [n for _, n in fake.sizes] == [100, 20]
    assert [s["content_id"] for s in out["scored"]] == [p["content_id"] for p in pois]


def test_dwell_is_split_and_merged() -> None:
    hub, fake = _hub()
    places = [{"content_id": f"p{i}"} for i in range(150)]

    out = asyncio.run(hub.estimate_dwell(places))

    assert [n for _, n in fake.sizes] == [100, 50]
    assert len(out["estimates"]) == 150


def test_small_requests_stay_single() -> None:
    hub, fake = _hub()
    asyncio.run(hub.estimate_dwell([{"content_id": "p0"}]))
    assert fake.sizes == [("dwell", 1)]
