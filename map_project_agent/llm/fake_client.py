"""외부 모델 없이 도는 결정적 합성 LLM 제공자.

빠른 시작과 시험에서 키·비용 없이 추천 그래프를 끝까지 돌리기 위한 것이다.
기본 제공자이며, Gemini 는 쓰는 사람이 제공자를 gemini 로 고르고 자기 키를
넣었을 때만 부른다.

지키는 것:
  - 같은 입력이면 늘 같은 출력을 낸다(난수·시각을 쓰지 않는다).
  - 새 장소나 좌표를 만들지 않는다. 장소는 프롬프트의 <candidates> 에 실린
    후보(이미 hub 룰로 정렬돼 있다) 앞에서부터 index 로만 고른다.
  - 사람이 읽는 모든 문장 앞에 SYNTHETIC_MARK 를 붙여, 실제 모델 결과와
    섞여 보이지 않게 한다.

프롬프트는 노드가 만든 그대로 받는다. 노드는 데이터를 <user_input>·
<candidates>·<places> 같은 태그 안에 JSON 으로 싣는데, 이 제공자는 그 JSON 만
읽는다. 태그를 못 찾으면 빈 결과를 돌려주고, 판정은 노드의 기존 검증에 맡긴다.
"""
from __future__ import annotations

import json
import re
from datetime import date

from pydantic import BaseModel

from map_project_agent.schemas.agent_schemas import (
    BulletsEnvelope,
    PlaceBullets,
    PlaceReason,
    PlaceSelection,
    PlacesSelection,
    ReasonEnvelope,
)

SYNTHETIC_MARK = "[합성]"

# 하루에 고르는 장소 수. 선정 지시가 요구하는 범위(하루 2~4곳) 가운데 값이다.
PER_DAY = 3
_VISIT_TIMES = ("오전", "점심 무렵", "오후", "늦은 오후")
_NAME_MAX = 60


def _block(prompt: str, tag: str):
    """<tag>…</tag> 안의 JSON 을 꺼낸다. 없거나 깨졌으면 None."""
    m = re.search(rf"<{tag}>(.*?)</{tag}>", prompt, re.S)
    if not m:
        return None
    try:
        return json.loads(m.group(1))
    except ValueError:
        return None


def _num_days(prompt: str) -> int:
    """<user_input> 의 여행 기간에서 일수를 센다. 모르면 1."""
    user = _block(prompt, "user_input")
    period = user.get("date") if isinstance(user, dict) else None
    try:
        start = date.fromisoformat(period["date_start"])
        end = date.fromisoformat(period["date_end"])
    except (TypeError, KeyError, ValueError):
        return 1
    return max(1, (end - start).days + 1)


def _name(item: dict) -> str:
    name = item.get("name") if isinstance(item, dict) else None
    return str(name)[:_NAME_MAX] if name else "이 장소"


def _items(prompt: str, tag: str) -> list[dict]:
    value = _block(prompt, tag)
    return [v for v in value if isinstance(v, dict)] if isinstance(value, list) else []


def select_places(prompt: str) -> PlacesSelection:
    """후보 앞에서부터 하루 PER_DAY 곳씩, 일차 순서대로 고른다."""
    candidates = [c for c in _items(prompt, "candidates") if isinstance(c.get("index"), int)]
    days = _num_days(prompt)
    chosen = candidates[: days * PER_DAY]
    if not chosen:
        return PlacesSelection(selections=[])
    per_day = -(-len(chosen) // days)  # 올림 나눗셈: 앞 일차부터 채운다
    return PlacesSelection(
        selections=[
            PlaceSelection(
                index=c["index"],
                day=min(days, i // per_day + 1),
                recommended_visit_time=f"{SYNTHETIC_MARK} {_VISIT_TIMES[(i % per_day) % len(_VISIT_TIMES)]}",
            )
            for i, c in enumerate(chosen)
        ]
    )


def explain_places(prompt: str) -> ReasonEnvelope:
    """장소마다 틀 문장 하나와 옷차림 안내 하나를 만든다."""
    return ReasonEnvelope(
        reasons=[
            PlaceReason(
                place_id=p["place_id"],
                reason=f"{SYNTHETIC_MARK} {_name(p)} — 후보 순위와 동선을 기준으로 고른 장소입니다.",
            )
            for p in _items(prompt, "places")
            if isinstance(p.get("place_id"), int)
        ],
        clothing=f"{SYNTHETIC_MARK} 출발 전에 날씨 예보를 확인하고 걷기 편한 옷차림을 준비하세요.",
    )


def summarize_places(prompt: str) -> BulletsEnvelope:
    """장소마다 두 줄의 틀 요약을 만든다. 후기 내용은 해석하지 않는다."""
    items = []
    for view in _items(prompt, "places"):
        if not isinstance(view.get("place_id"), int):
            continue
        snippets = view.get("review_snippets")
        count = len(snippets) if isinstance(snippets, list) else 0
        items.append(
            PlaceBullets(
                place_id=view["place_id"],
                bullets=[
                    f"{SYNTHETIC_MARK} {_name(view)} 후기 {count}건을 받았습니다.",
                    f"{SYNTHETIC_MARK} 실제 요약은 Gemini 제공자를 켜면 만들어집니다.",
                ],
            )
        )
    return BulletsEnvelope(items=items)


_HANDLERS = {
    PlacesSelection: select_places,
    ReasonEnvelope: explain_places,
    BulletsEnvelope: summarize_places,
}


class FakeLLMClient:
    """GeminiClient 와 같은 호출 모양을 가진 합성 제공자.

    호출 한도기·네트워크·키를 쓰지 않는다. 토큰을 쓰지 않으므로 사용량
    기록(usage_sink)에는 아무것도 덧붙이지 않는다.
    """

    model = "fake"

    async def generate_structured(
        self,
        prompt: str,
        response_schema: type[BaseModel],
        *,
        system_instruction: str | None = None,
        usage_sink: list[dict] | None = None,
    ) -> BaseModel:
        handler = _HANDLERS.get(response_schema)
        if handler is None:
            raise TypeError(
                f"fake LLM provider has no rule for {response_schema.__name__}"
            )
        return handler(prompt)

    async def aclose(self) -> None:
        """정리할 자원이 없다 — 다른 클라이언트와 같은 수명 훅만 둔다."""
        return None
