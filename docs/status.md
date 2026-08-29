---
signal: GREEN
plan: number-flag
phase: 테스트
step: 2 (완료)
attempt: 0
iteration: 139
night_iterations: 22
night_red: 0
night_retries: 0
updated: 2026-08-29 18:55 (반복 139 · 스텝 2 완료 — serve 도 같은 파서)
ctx: 70% / 200k
stopped: -
rules: 1411a37
mode: night (지시 실행 — 준 것만 하고 정지)
---

# 현재 상태

**계획 25 `number-flag` — 스텝 2개 전부 완료, 다음은 테스트 phase**(빠진 것 찾기).
`src/websearch/cli.py` 하나가 `crawl` 넷(`--max`·`--workers`·`--deadline`)과
`serve`(`--port`)를 다 읽는다. 단위 412 → **414건 OK** · e2e 아직 안 돌림.
**변이 M1(파서에서 `isascii()` 제거)이 `test_crawl` 과 `test_serve` 를 동시에 죽인다**
— 파서가 한 자리라는 증거다(설계 스텝 2 완료 기준).
보류 패치 0건. 단위 **412건 OK** · e2e **17종 전부 rc=0**.

## 이번 세션 (반복 136) — `loop/number-flag`

**136 · 계획 25 `number-flag`.** 근거는 `index.md` 23·24번이 이미 적어 둔 것이다 —
`str.isdigit()`/`int()` 가 비ASCII 숫자를 받는 함정을 `urls.py:57`(019)과
`serve.py:323`(24)이 **각자 자기 자리에서만** 막았고 `crawl.py:215 _number_flag` 는
그대로다. 착수 전 실측: `_number_flag(['--max','٨٠'],…)` → **80**, `8_0` → 80,
`' 80 '` → 80, `'+80'` → 80. `--max`·`--workers`·`--deadline` 셋이 같은 파서라 셋 다다.
반대로 `serve.main(['prog','a.db','--port=8080'])` → **rc 2**(붙임 형태를 모른다) —
`crawl` 은 `--max=3` 을 받는데 `serve` 는 안 받는 CLI 계약 불일치도 같이 닫는다.

**137 · 설계.** 세 출발점에서 안을 냈다 — ① 모으지 않고 `crawl` 만 좁힌다(3줄) ·
② 새 모듈 `cli.py` · ③ `crawl.py` 에 두고 `serve` 가 임포트. ①은 **문제를 안 푼다**
(네 번째 자리를 남긴다). ②③ 중 "더 적게 쓰나" 는 ③ 이 앞서지만 **의존 방향**이
뒤집었다 — ③ 은 검색 서버가 크롤러를 임포트한다(실측 +6.3ms, 진짜 값은 의미).
**가장 위험한 가정을 탐침으로 깼다**: 파서를 좁히면 `--max -5`·`--deadline -1` 의
경로가 `int()` 수용 → 호출부 `< 1` 에서 **파서 거절**로 바뀌는데, 임시로 좁혀 돌리니
**412건 전부 OK**(rc 2 유지, 바뀌는 것은 stderr 문구뿐). 탐침은 되돌렸다.

**138 · 스텝 1 개발.** TDD 로 갔다 — `--max ٨٠`·`--workers ٨`·`--deadline ٦٠`·
`--max=٨٠`·`8_0`·`' 80 '`·`+80`·`²` 여덟이 rc 2 이고 `crawl()` 이 안 불리는 테스트를
먼저 쓰고 **RED 를 눈으로 봤다**(`--max ٨٠` → rc 0, 80페이지로 돌았다). 그다음
`src/websearch/cli.py` 를 만들고 `crawl._number_flag` 를 지웠다. 413건 OK.

**139 · 스텝 2 개발.** `serve --port=8080` 이 rc 2 로 죽는 것을 RED 로 보고(`crawl` 은
`--max=3` 을 받는다) `serve.py` 의 인라인 블록 10줄을 `cli.number_flag` 한 줄 + 상한
검사로 줄였다. 414건 OK. 변이 3종 확인 — **M1 이 두 파일의 테스트를 함께 죽인다.**

## 이번 세션 (반복 134~135) — `loop/deadline-patches` (기점 `1eaf879`)

**134 · history 회전 (집안일).** 앞 세션이 "328줄" 이라고 적고 범위 밖으로 남긴 것을
`wc -l` 로 **실측 확인**(정확히 328)하고 `docs.md` 3절대로 잘랐다.
`history_current.md` **328 → 128줄**(기록 뒤 181), 계획 020 `deadline` 6회를 `docs/history_007.md` 로.
자를 곳을 **계획 경계**에 뒀다 — 020 은 DONE 이고 잔류분(021~023)이 그것을 안 참조한다.
`digest.md` 135 → 146줄. **020 은 `## 완료` 절에 항목이 아예 없어서** 회전 줄이 유일한
압축본이다 — 설계 선택(③ 되돌리기 우선)·거부한 두 갈래·M6 까지 담았다.
무손실 확인: 원본 328 = 헤더 27 + 아카이브 200 + 잔류 101, 양쪽 `diff` 0.

## 열지 않는 것 (사용자 판단 대기)

`data/crawl.db` 재키잉/옛 열쇠 행 통합(마이그레이션) · URL userinfo 가 `pages.url` PK
이자 검색 결과에 렌더되는 것(보안 경계) · `recrawl`(`fetched_at` 스키마) ·
`X-Robots-Tag`(스키마) · `loop/*` 브랜치 병합 · 의존성 추가·업그레이드 · CI 도입 ·
`docs/specs/` 쓰기 · git 사용자 이메일 설정 변경.
