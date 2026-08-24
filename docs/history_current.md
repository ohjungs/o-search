# 최근 반복 기록

<!--
append 전용. 수정·삭제 금지.

상한 20회 / 300줄. 넘으면 오래된 것부터 history_<NNN>.md 로 밀어내고,
밀어낼 때 digest.md 에 1~2줄로 압축해 남긴다. (docs.md 룰)

이 파일은 매 반복 읽힌다. 그래서 상한이 있다.
-->

## 형식

```
## YYYY-MM-DD HH:MM | <plan-slug> | <phase> <step> | 시도N
- 한 일: <무엇을 했나. 파일 경로 포함>
- 결과: <검증 결과. 테스트 12/12 통과 / 린트 0건 / 실패 출력 요약>
- 다음: <다음 스텝 또는 정지 사유>
```

실패한 반복도 반드시 남긴다. 실패 기록이 없으면 같은 실수를 반복한다.

---

## 2026-08-25 | crawler-core | 계획 1 | 시도1
- 한 일: 초기화(템플릿 7개 배치, 훅 설치) + concept.md 를 계획 6개로 분할(index.md) + plan_crawler-core.md 작성(스텝 7)
- 결과: project.md 명령 절은 "없음"(코드 0줄) — 스텝 1에서 갱신 예정
- 다음: 설계 phase — design_crawler-core.md (스택·모듈 경계)

## 2026-08-25 | crawler-core | 설계 | 시도1
- 한 일: design_crawler-core.md — 대안 3개(stdlib만/의존성 추가/Node) 비교, A 선택. 가정 탐침: 시스템 Python 3.9.6 sqlite3 FTS5 생성 성공
- 결과: 의존성 0 → 설계룰 4절 보류 사안 없음. 계약(시그니처·스키마) 확정
- 다음: 개발 스텝 1 — 스캐폴드 + unittest 러너 확인

## 2026-08-25 야간1 | crawler-core | 개발 1/7 | 시도1
- 한 일: 스캐폴드 — src/websearch/__init__.py, tests/test_smoke.py, .gitignore(data/·reports/), project.md 명령 갱신
- 결과: unittest 1/1 통과. 실패 먼저 확인(네임스페이스 패키지 탓에 1차 시도는 실패를 못 봐 단언 교체)
- 다음: 개발 2/7 robots

## 2026-08-25 야간2 | crawler-core | 개발 2/7 | 시도1
- 한 일: robots.py(RobotsCache) + test_robots.py 5케이스 — 허용/차단/404허용/5xx차단/도메인당 1회 캐시
- 결과: 실패 확인 후 구현, 전체 6/6 통과. 실네트워크 없음(_fetch_robots 주입)
- 다음: 개발 3/7 fetcher

## 2026-08-25 야간3 | crawler-core | 개발 3/7 | 시도1
- 한 일: fetcher.py(fetch→FetchResult) + test_fetcher.py 5케이스 — 성공/비HTML/4xx/타임아웃 3회 포기/재시도 성공
- 결과: 실패 확인 후 구현, 전체 11/11 통과. HTTPError 는 확정 응답이라 재시도 안 함
- 다음: 개발 4/7 store

## 2026-08-25 야간4 | crawler-core | 개발 4/7 | 시도1
- 한 일: store.py(Store: upsert/has/get_html/count) + test_store.py 3케이스 — 저장/갱신 중복 없음/실패기록
- 결과: 실패 확인 후 구현, 전체 14/14 통과. 스키마는 설계 계약대로 pages 단일 테이블
- 다음: 개발 5/7 links

## 2026-08-25 야간5 | crawler-core | 개발 5/7 | 시도1
- 한 일: links.py(extract) + test_links.py 6케이스 — 절대화/fragment/스킴 필터/중복/빈 href/깨진 HTML
- 결과: 실패 확인 후 구현, 전체 20/20 통과. stdlib HTMLParser 로 충분
- 다음: 개발 6/7 frontier

## 2026-08-25 야간6 | crawler-core | 개발 6/7 | 시도1
- 한 일: frontier.py(Frontier: add/next/empty/seconds_until_ready) + test_frontier.py 6케이스 — 중복/재큐 방지/1초 간격/라운드로빈/대기 시간
- 결과: 실패 확인 후 구현, 전체 26/26 통과. 시계 주입으로 sleep 없는 테스트
- 다음: 개발 7/7 crawl 통합

## 2026-08-25 야간7 | crawler-core | 개발 7/7 | 시도1
- 한 일: crawl.py(crawl + CLI main) + test_crawl.py 4케이스 — 시드→링크 추적/robots 미요청/max_pages/실패 미집계
- 결과: 실패 확인 후 구현, 전체 30/30 통과. 개발 phase 완료 → 테스트 phase
- 다음: 테스트 phase (갭 탐색)

## 2026-08-25 야간8 | crawler-core | 테스트 | 시도1
- 한 일: 갭 탐색 6카테고리 — 격리 위반 1건(테스트가 실제 시계 의존, 스위트 4.06s) 수정: crawl 에 now 주입, sleep 목이 가짜 시계를 흘림
- 결과: 30/30 통과 0.004s (PYTHONPATH=src python3 -m unittest discover tests — 전체). 8점 미만 갭 3건 digest 에
- 다음: 리뷰 phase
