# 프로젝트 정보

<!-- 초기화 시점에 코드가 0줄이라 명령이 없다. crawler-core 스텝 1(스캐폴드)이
     테스트 러너를 확정하면 여기부터 갱신한다. 확인 안 된 명령은 적지 않는다. -->

## 명령

- **테스트(전체)**: `PYTHONPATH=src python3 -m unittest discover tests` (2026-08-25 실행 확인, 실패 감지도 확인)
- **테스트(빠름)**: 전체가 수 초라 구분 없음
- **린트/타입체크**: 없음 — stdlib만 쓰는 소규모, 필요해지면 추가
- **e2e**: `PYTHONPATH=src python3 e2e/crawl_e2e.py` (2026-08-25 실행 확인, 14.7s — 간격 정책상 정상)
- **e2e**: `PYTHONPATH=src python3 e2e/indexer_e2e.py` (2026-08-25 실행 확인, 약 4s)
- **e2e**: `PYTHONPATH=src python3 e2e/noindex_e2e.py` (2026-08-25 실행 확인, 3.7s)

## 브랜치·소유자

- 기본 브랜치: `main` (보호 — 루프는 `loop/<slug>` 브랜치에서 작업)
- 소유자 파일: 없음 (혼자 쓰는 저장소)

## 품질 기준 <!-- docs/specs/concept.md 4축의 실행 명령판 -->

- **경량 상한**: 없음 — search-ui 계획에서 JS 50KB(gzip) 측정 명령 추가 예정
- **성능 측정**: 없음 — search-api 계획에서 p95 측정 스크립트 추가 예정
- **디자인 검사**: 없음 — search-ui 계획에서 추가 예정
- **검색 품질**: 없음 — quality-eval 계획에서 질의 40개 셋 + 포함률 측정 추가 예정
- **기준선 파일**: 없음 — 첫 측정이 기준선이 된다

## 한도

- 크롤러: 도메인당 요청 간격 1초 이상, robots.txt 준수 — 위반 코드는 RED
- 외부 네트워크를 때리는 테스트 금지 — 모킹 또는 로컬 테스트 서버만

## 건드리지 않을 곳

- `docs/specs/` — 읽기 전용 (사용자 영역)
