---
signal: GREEN
plan: null
phase: 계획
step: -
attempt: 0
iteration: 135
night_iterations: 18
night_red: 0
night_retries: 0
updated: 2026-08-29 17:40 (반복 135 · serve-port-guard 짧은 경로 DONE)
ctx: 55% / 200k
stopped: -
rules: 1411a37
mode: night (지시 실행 — 준 것만 하고 정지)
---

# 현재 상태

**열린 계획 없음. 보류 패치 0건 — `docs/patches/` 는 비었다.**
단위 **412건 OK** · e2e **17종 전부 rc=0**.

## 이번 세션 (반복 134~135) — `loop/deadline-patches` (기점 `1eaf879`)

**134 · history 회전 (집안일).** 앞 세션이 "328줄" 이라고 적고 범위 밖으로 남긴 것을
`wc -l` 로 **실측 확인**(정확히 328)하고 `docs.md` 3절대로 잘랐다.
`history_current.md` **328 → 128줄**(기록 뒤 181), 계획 020 `deadline` 6회를 `docs/history_007.md` 로.
자를 곳을 **계획 경계**에 뒀다 — 020 은 DONE 이고 잔류분(021~023)이 그것을 안 참조한다.
`digest.md` 135 → 146줄. **020 은 `## 완료` 절에 항목이 아예 없어서** 회전 줄이 유일한
압축본이다 — 설계 선택(③ 되돌리기 우선)·거부한 두 갈래·M6 까지 담았다.
무손실 확인: 원본 328 = 헤더 27 + 아카이브 200 + 잔류 101, 양쪽 `diff` 0.

## 짧은 경로 — `serve-port-guard` (**DONE** · 반복 135)

- 근거: `digest.md ## 다음 계획 후보 (테스트 phase 갭)` `[5]` — **`serve.main` 인자 처리에
  단위 테스트 0.** 착수 전 탐침 실측 3건이 전부 트레이스백/조용한 오작동이다:
  `--port 99999` → `OverflowError` · `--port ²` → `ValueError`(`serve.py:323`) ·
  `--port ٨٠٨٠` → **조용히 8080** · `--port 80` → `PermissionError`.
- 할 일: `main()` 의 포트 검증을 `isascii() and isdigit()` + 범위 0~65535 로 좁히고
  bind 실패(`OSError`)를 메시지 + rc 1 로 받는다. `src/websearch/serve.py` 만.
- 완료 기준: 위 넷이 전부 rc 2(또는 bind 실패 rc 1) + 한 줄 메시지, 트레이스백 0.
  `--port` 값 없음·비숫자·db 인자 개수 단위 테스트도 같이 (후보가 지적한 갭 자체다).
- **결과**: 넷이 전부 rc 2 + 한 줄 메시지, bind 실패는 rc 1. 트레이스백 0(실제 CLI 8가지 실측).
  단위 403 → **412건 OK** · e2e 17종 rc=0. 변이 4종 전부 잡힘 — 그중 `> 65535` → `> 65536`
  은 99999 만으로는 안 죽어 **"65535 는 그대로 뜬다"** 를 더해 닫았다(경계는 양쪽에서 잰다).
  `index.md` 24번 · `digest.md` 후보 `[5]` 닫음.
- **짧은 경로 연속 3건 확인**(`SKILL.md` 4-1절): 021 `indexer-cli-guard`(출처: digest
  `## 반복 실패`) · 022 `robots-read-cap`(출처: `## 다음 계획 후보 [5]`) · 이번
  (출처: `## 다음 계획 후보 (테스트 phase 갭) [5]`). **셋의 출처가 다르다** — 탐색이
  막힌 것이 아니라 후보 큐가 실제로 소진되는 중이라 계속한다.
- **안 하기로 한 것**: 없는 DB 경로로 띄우면 서버는 뜨고 질의마다 500 이 난다(실측).
  `TestMissingDb` 가 그 500 을 **계약으로 못 박아 뒀고**(내부 안 흘리고 stderr 에 남긴다)
  시작 시점에 막으면 "먼저 띄우고 나중에 크롤" 이 깨진다. 다른 축이라 안 건드린다.

## 열지 않는 것 (사용자 판단 대기)

`data/crawl.db` 재키잉/옛 열쇠 행 통합(마이그레이션) · URL userinfo 가 `pages.url` PK
이자 검색 결과에 렌더되는 것(보안 경계) · `recrawl`(`fetched_at` 스키마) ·
`X-Robots-Tag`(스키마) · `loop/*` 브랜치 병합 · 의존성 추가·업그레이드 · CI 도입 ·
`docs/specs/` 쓰기 · git 사용자 이메일 설정 변경.
