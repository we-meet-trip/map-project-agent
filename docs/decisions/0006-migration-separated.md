# 0006. 체크포인트 마이그레이션을 런타임과 다른 계정·과정으로 돌린다

## 맥락

런타임이 기동할 때 SDK `setup()` 으로 테이블을 만들면, 런타임 계정에 DDL 권한이 필요하고 계정이 새면 스키마까지 바뀔 수 있다.

## 선택지

1. 런타임이 기동 때 setup
2. 별도 마이그레이션 모듈과 전용 계정, 런타임은 검증만

## 결정

두 번째. `python -m map_project_agent.checkpoint_migrate` 가 migrator 계정으로 고정한 SDK 마이그레이션만 적용하고, 런타임은 `map_agent_runtime` 으로 SELECT 만으로 판·테이블·인덱스·권한을 검사한다.

## 결과

체크포인터를 켜려면 역할 SQL → 마이그레이션 → 역할 SQL 재적용 순서가 필요하다([architecture.md](../architecture.md)). 빠른 시작은 체크포인터를 끈다.

## 관련 커밋

[`27918f8`](https://github.com/we-meet-trip/map-project-agent/commit/27918f87cfe6b6c9a97cea3548d260126569fdee), [`640024d`](https://github.com/we-meet-trip/map-project-agent/commit/640024d4a977be418b92b59eb37e149fafa52456)
