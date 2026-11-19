# agent-service 테스트 패키지.
#
# pytest 가 본 디렉터리의 test_*.py 모듈을 수집한다. 각 테스트는
# map_project_agent.* 를 직접 임포트하며, 외부 클라이언트는 가짜 구현을
# map_project_agent.agent_dependencies 슬롯에 주입해 대체한다.
