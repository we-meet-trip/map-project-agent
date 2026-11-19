# 0001. 실측 후보 안에서만 장소를 고른다

## 맥락

LLM 에게 지역과 조건만 주면 그럴듯하지만 존재하지 않는 장소나 틀린 좌표를 만든다. 한때 후보가 0건이면 모델이 장소를 직접 만들어 채우는 폴백을 두었는데, 결과가 실제처럼 보여 오히려 확인하기 어려웠다.

## 선택지

1. 모델이 장소와 좌표를 직접 만든다
2. hub 검색·룰을 통과한 후보 안에서 index 로만 고르게 하고, 부족하면 실패한다
3. 후보에서 고르되 0건이면 모델이 만들어 채운다(폴백)

## 결정

두 번째. 모델은 `<candidates>` 의 index 로만 고르고, 고른 장소는 hub 검색으로 출처를 다시 확인해 원본 좌표를 쓴다. 후보가 없거나 선택이 부족하면 `no_matching_places`·`selection_invalid` 로 실패한다. 창작 폴백은 없앴다.

## 결과

결과의 모든 장소에 출처(`content_id`·`source`·`grounded`)가 있다. 후보가 적은 지역에서는 실패가 늘지만, 지어낸 결과가 섞이지 않는다.

## 관련 커밋

[`633d69d`](https://github.com/we-meet-trip/map-project-agent/commit/633d69ddd0f3704af871b93bf3655f4e6964c38c), [`7668afd`](https://github.com/we-meet-trip/map-project-agent/commit/7668afdc05ec89f0f2af5a207a6e4780c1ee1cf3), [`d4dad3d`](https://github.com/we-meet-trip/map-project-agent/commit/d4dad3dd9a7fa358111d34fb57115b9af3872665)
