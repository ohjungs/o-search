---
signal: DONE
plan: null
mode: night
phase: null
step: null
attempt: 0
iteration: 122
night_iterations: 5
night_red: 0
night_retries: 0
updated: 2026-08-28 (반복 122 · 019 DONE)
ctx: 68% / 200k
stopped: 컨텍스트 여유 부족 — 새 계획 한 벌을 못 돈다. RED 아님
rules: 1411a37
---

# 현재 상태

**계획 019 `normalize-gaps` DONE.** 브랜치 `loop/normalize-gaps` (기점 `33e531d`).
계획서는 `docs/plan_history_017.md`, e2e 결과는 `docs/e2e/normalize-gaps/result.md`.

018 이 못 접은 두 표기를 닫았다. `urls._fold_dots` 가 RFC 3986 5.2.4 를 세그먼트
단위로 돌아 `.`·`..` 만 접고, `domain_key` 는 숫자 포트의 앞자리 0 만 뗀다.

**실측.** 단위 **388건 OK**. e2e **14종 전부 rc=0** — `url_normalize_e2e` 는 표기
**10개가 문서 6개**로 접히고(날 `/a/../p` 수신 **0회**), 대조군 `/a//b`·`/a/b` 는
**둘 다 따로** 받는다. 같은 서버 페이지 간격 최소 **1.005초**.
변이가 서로를 안 대신한다 — 단위 8종(M1~M8) · e2e 3종이 각각 **다른 단언**에서만 죽는다.

**두 번 배웠다.**
1. **`posixpath.normpath` 를 골랐다면 018 의 계약이 뒷문으로 깨졌을 것이다.** 변이
   M4 가 018 의 기존 테스트를 죽여 그것을 **내 주장이 아니라 남의 테스트로** 확인했다
2. **백지 리뷰가 019 자신의 회귀를 잡았다.** `lstrip("0")` 이 `:0` 을 통째로 먹어
   빈 포트가 되고, **빈 포트는 기본 포트**라 요청이 80 번으로 나갔다. "앞자리만 뗀다"
   는 이름이 그 경우를 가렸다 (`or "0"` 로 닫음)

**새로 기록한 것 1건** (고치지 않음): `links.extract` 의 `urljoin` 이 RFC 보다 넓게
접어(루트 표식까지 pop) 상대 href 와 절대 href 가 **231/3905 모양에서 갈린다** —
`digest.md` 새 `[4]`. 019 가 갈리던 범위를 이 한 부류로 줄였지만 안 닫았다.
기존 DB 재키잉은 아래 판단 필요 1번이다.

## 판단 필요 — 사람에게 묻는다 (018 에서 이월, 019 가 안 건드린다)

1. **기존 `data/crawl.db` 의 옛 열쇠 행 통합** — 마이그레이션이라 야간 금지.
   019 도 **새 DB 에서만 목적을 달성한다**
2. **URL 자격증명이 `pages.url` PK 이자 검색 결과 링크** — 보안 경계, 줄 수 무관 야간 금지
3. `loop/*` 브랜치 **머지 판단** (17개가 한 줄로 쌓여 있다 — 실측 `git branch --list`)
4. **`project.md` 의 기본 브랜치 `main` 이 저장소에 없다.** 실제 이력은 `loop/*` 팁이
   줄줄이 달린 한 줄이다. 019 는 관례를 따르고 문서를 안 고쳤다 — 사람이 정한다

## 다음에 할 일 — 계획 없음

`docs/digest.md ## 다음 계획 후보` 와 `## 판단 필요` 에서 고른다. 지금 위에 있는 것:
recrawl(`store.has` 상태 불문 스킵 + indexer 증분 + 옛 열쇠 행 통합 — 셋이 같은
수술이다) · `--deadline`(Ctrl-C 최악 대기와 총 크롤 시간 예산이 같은 답이다) ·
`X-Robots-Tag` 헤더 · `links` 의 `urljoin` 이 RFC 보다 넓게 접는 것(digest 새 `[4]`,
231/3905 모양 — 실물에서 본 적 없어 비용 대비가 안 맞는다고 적어 뒀다).

## 열지 않는 것

recrawl(`store.has` 상태 불문 스킵 · indexer 증분) · `X-Robots-Tag` · `loop/*` 병합 ·
옛 표기로 저장된 기존 행의 마이그레이션 · 끝 슬래시 일반화 · 퍼센트 디코딩 ·
`to_ascii` 수정 · userinfo 처리
