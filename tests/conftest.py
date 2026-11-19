"""모든 테스트에 공통으로 까는 설정.

서비스 사이 좌표는 늘 봉투로만 오가고 열쇠는 필수다. 테스트는 실제 열쇠
대신 단순한 합성 열쇠(32바이트)를 쓴다. 열쇠 자체를 검사하는 테스트는
자기 픽스처로 덮어쓴다.
"""
from __future__ import annotations

import base64

import pytest
from pydantic import SecretStr

from map_project_agent.agent_settings import get_settings

TEST_WIRE_KEY = base64.b64encode(b"w" * 32).decode()


@pytest.fixture(autouse=True)
def _synthetic_wire_key(monkeypatch):
    monkeypatch.setattr(get_settings(), "LOCATION_WIRE_KEY", SecretStr(TEST_WIRE_KEY))
