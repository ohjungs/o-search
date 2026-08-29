---
signal: GREEN
plan: number-flag
phase: 설계
step: -
attempt: 0
iteration: 136
night_iterations: 19
night_red: 0
night_retries: 0
updated: 2026-08-29 18:10 (반복 136 · 계획 25 number-flag 작성)
ctx: 62% / 200k
stopped: -
rules: 1411a37
mode: night (지시 실행 — 준 것만 하고 정지)
---

# 현재 상태

**계획 25 `number-flag` 착수 — `docs/plan_number-flag.md`.** 다음은 **설계**다
(`design.md` 1절 트리거: 새 파일 후보 · 공개 함수 추가 · 3개 이상 파일).
갈림길은 **공유 파서를 어디 두는가** 하나 — 후보 A/B/C 는 계획서에 적혀 있다.
보류 패치 0건. 단위 **412건 OK** · e2e **17종 전부 rc=0**.

## 이번 세션 (반복 136) — `loop/number-flag`

**136 · 계획 25 `number-flag`.** 근거는 `index.md` 23·24번이 이미 적어 둔 것이다 —
`str.isdigit()`/`int()` 가 비ASCII 숫자를 받는 함정을 `urls.py:57`(019)과
`serve.py:323`(24)이 **각자 자기 자리에서만** 막았고 `crawl.py:215 _number_flag` 는
그대로다. 착수 전 실측: `_number_flag(['--max','٨٠'],…)` → **80**, `8_0` → 80,
`' 80 '` → 80, `'+80'` → 80. `--max`·`--workers`·`--deadline` 셋이 같은 파서라 셋 다다.
반대로 `serve.main(['prog','a.db','--port=8080'])` → **rc 2**(붙임 형태를 모른다) —
`crawl` 은 `--max=3` 을 받는데 `serve` 는 안 받는 CLI 계약 불일치도 같이 닫는다.

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
