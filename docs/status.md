---
signal: GREEN
plan: null
phase: 계획
step: -
attempt: 0
iteration: 142
night_iterations: 25
night_red: 0
night_retries: 0
updated: 2026-08-29 20:05 (반복 142 · 계획 25 number-flag DONE)
ctx: 62% / 200k
stopped: -
rules: 1411a37
mode: night (지시 실행 — 준 것만 하고 정지)
---

# 현재 상태

**계획 25 `number-flag` DONE.** 열린 계획 없음 · 보류 패치 0건.
단위 **415건 OK** · e2e **17종 전부 rc=0**(+ 실제 CLI 12가지).
브랜치 `loop/number-flag` 는 `origin` 에 푸시됨 — 병합은 사용자 판단이다.

## 이번 세션 (반복 136~142) — `loop/number-flag` (기점 `dc577d4`)

**숫자 인자 파서를 한 자리로 모았다.** `str.isdigit()`/`int()` 가 비ASCII 숫자를 받는
함정을 019 가 `urls.py` 에서, 24 가 `serve.py` 에서 **각자 자기 자리에서만** 막았고
`crawl.py:215 _number_flag` 가 세 번째 자리였다 — 실측 `--max ٨٠` → **80페이지**,
`8_0`·`' 80 '`·`+80` 통과, `--max -5` → **rc 0**. 이제 `src/websearch/flags.py` 하나가
`crawl` 셋과 `serve` 하나를 다 읽고 `[0-9]+` 만 받는다.

- 136 계획 → 137 설계(자리 판정 + 탐침) → 138·139 개발(TDD) → 140 테스트 →
  141 리뷰(백지 패스) → 142 e2e·DONE. **재시도 0 · RED 0**
- **모았다는 증거는 변이 M1** — 파서에서 `isascii()` 를 떼면 `test_crawl` 과
  `test_serve` 가 **함께** 죽는다. 한쪽만 죽으면 아직 두 벌인 것이다
- **백지 리뷰가 실재 파손을 잡았다** — 모듈 이름을 `cli.py` 로 하니 README 가 안내하는
  `python -m websearch.cli ...` 가 rc 1 에서 **rc 0(조용한 무동작)** 이 됐다 →
  `flags.py` 로 개명. 배경 없는 별도 세션에 넘긴 것이 값을 했다
- **교훈**: 019·24 는 각각 "고쳤다" 로 닫혔지만 **한 자리에서** 안 고쳐 세 번 나왔다

## 다음 (탐색부터)

`digest.md ## 다음 계획 후보` 가 큐다. 이번에 4건이 더해졌다(전부 8점 미만):
`--max 0` 가드 비대칭[5] · 중복 플래그가 시드로 샘[5] · **README 의 명령 셋이 통째로
없다**[5] · `--port 0` 단위 무커버[4] · `int_max_str_digits`[4].
**CLI 인자 축은 최근 넷이 몰려 있다** — 다음은 다른 축을 보는 편이 낫다.
`history_current.md` 293줄(상한 300) — **다음 반복은 회전부터.**

## 열지 않는 것 (사용자 판단 대기)

`data/crawl.db` 재키잉/옛 열쇠 행 통합(마이그레이션) · URL userinfo 가 `pages.url` PK
이자 검색 결과에 렌더되는 것(보안 경계) · `recrawl`(`fetched_at` 스키마) ·
`X-Robots-Tag`(스키마) · `loop/*` 브랜치 병합 · 의존성 추가·업그레이드 · CI 도입 ·
`docs/specs/` 쓰기 · git 사용자 이메일 설정 변경.
