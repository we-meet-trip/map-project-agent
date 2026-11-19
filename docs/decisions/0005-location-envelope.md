# 0005. 서비스 사이 좌표는 봉투로만 오가고 열쇠는 필수다

## 맥락

좌표가 요청 본문·스트림·체크포인트에 평문으로 남아, 같은 망의 다른 컨테이너나 중간 기록·백업에서 사용자가 다닐 곳이 그대로 보였다.

## 선택지

1. 평문 유지(망 격리에 맡김)
2. 열쇠가 있을 때만 봉투, 없으면 평문(전환용)
3. 봉투를 늘 쓰고 열쇠를 필수로

## 결정

세 번째. AES-GCM 봉투(`v1.<난수>.<암호문>`, AAD `map|loc|v1`, 만든 지 300초가 지나면 열지 않음)를 hub·BFF 와 같은 열쇠로 쓴다. 열쇠가 없으면 부팅을 멈춘다. 체크포인트는 kid 로 열쇠를 돌릴 수 있는 별도 봉인으로 저장 전에 감싸며, 두 열쇠가 같으면 부팅을 거부한다.

## 결과

좌표가 평문으로 나가는 길이 없다. 대신 세 서비스가 같은 봉투 열쇠를 가져야 하고, 한쪽만 바꾸면 좌표가 오가는 모든 요청이 거절된다.

## 관련 커밋

[`5e80dcf`](https://github.com/we-meet-trip/map-project-agent/commit/5e80dcfadc6d0ac638a3ccb15512e7876fa5c40b), [`298d06c`](https://github.com/we-meet-trip/map-project-agent/commit/298d06cc12b914417af9c96c7ba0b3b55f8345ca), [`ca65896`](https://github.com/we-meet-trip/map-project-agent/commit/ca65896107df2f30f96008705963208c8613d938), [`34d3dfc`](https://github.com/we-meet-trip/map-project-agent/commit/34d3dfc7cce162aee62899e4e20c54360a320be8)
