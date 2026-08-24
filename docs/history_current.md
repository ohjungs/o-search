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

## 2026-08-25 야간9 | crawler-core | 리뷰 | 시도1
- 한 일: 패스 A 별도 세션(백지, 8건) → 코드 검증 → 자동 6건 수정(TDD 재현 테스트 11개 먼저): store 디렉터리 생성/FetchResult.url(리다이렉트 정본)/스킴 ValueError/charset 존중+폴백/2MB 상한/--max 방어
- 결과: 37/37 통과 0.007s (전체). 보류 2건 digest "판단 필요"로: 쿨다운 공회전(설계 결정), 재실행 스킵 정책(recrawl 소관)
- 다음: e2e phase

## 2026-08-25 야간10 | crawler-core | e2e | 시도1
- 한 일: e2e/crawl_e2e.py 신설(로컬 서버 20p+robots 차단) — CLI 실제 실행 검증. project.md e2e 명령 확정. 계획 아카이브(001)
- 결과: e2e 통과 — 수집 15/15, 차단 요청 0, 최소 간격 1.002s. 품질 4축은 미검증으로 기록(측정 명령 아직 없음)
- 다음: DONE → 다음 계획 indexer (계획 phase)

## 2026-08-25 야간11 | indexer | 계획 | 시도1
- 한 일: plan_indexer.md 작성 — 스텝 4(추출/증분 writer/질의+CLI/e2e). index.md 중복 확인: 없음
- 결과: 설계 필요 판정 (새 모듈+FTS5 스키마+토크나이저 갈림)
- 다음: 설계 phase

## 2026-08-25 야간12 | indexer | 설계 | 시도1
- 한 일: 토크나이저 탐침 — trigram 2글자 질의 불가(실측), unicode61+prefix+질의 재작성 채택. 단독 FTS5·같은 DB. design_indexer.md
- 결과: 컨셉 메모(trigram)와 다른 결정 — 근거 실측 기록. quality-eval 80% 미달 시 재론 조건 명시
- 다음: 개발 1/4 extract

## 2026-08-25 야간13 | indexer | 개발 1/4 | 시도1 (미완)
- 한 일: tests/test_extract.py 5케이스 작성(제목·본문/script 제외/공백 정규화/title 없음/깨진 HTML), 실패 확인
- 결과: 38 중 1 에러(extract 모듈 없음) — TDD 2단계까지. 구현 미착수
- 다음: extract.py 구현부터. 컨텍스트 상한으로 세션 종료

## 2026-08-25 야간14 | indexer | 개발 1/4 | 시도1
- 한 일: src/websearch/extract.py 구현 — stdlib html.parser 재사용(links.py 와 같은 패턴). script/style/noscript 는 깊이 카운터로 스킵, 닫히지 않은 <title> 은 다음 시작 태그에서 종료, 조각을 공백으로 이어 붙인 뒤 split/join 으로 정규화
- 결과: extract 5/5, 전체 42/42 통과 0.007s. 새 의존성 0
- 다음: 개발 2/4 FTS5 증분 색인 writer
